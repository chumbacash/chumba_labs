import importlib
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.append(str(_REPO))


def _load_modal_sdk():
    existing = sys.modules.get("modal")
    if existing is not None and hasattr(existing, "App"):
        return existing

    repo_modal = Path(__file__).resolve().parent
    shadowed = existing is not None and not hasattr(existing, "App")
    if shadowed:
        for key in list(sys.modules):
            if key == "modal" or (key.startswith("modal.") and key != __name__):
                sys.modules.pop(key, None)

    blocked: list[str] = []
    kept: list[str] = []
    for entry in sys.path:
        try:
            resolved = Path(entry).resolve()
        except OSError:
            kept.append(entry)
            continue
        if resolved == _REPO or resolved == repo_modal:
            blocked.append(entry)
        else:
            kept.append(entry)
    previous = sys.path[:]
    sys.path[:] = kept
    try:
        sdk = importlib.import_module("modal")
    finally:
        sys.path[:] = previous
    if not hasattr(sdk, "App"):
        raise ImportError("modal SDK is not installed")
    return sdk


modal = _load_modal_sdk()

app = modal.App("chumba-labs")
image = (
    modal.Image.debian_slim(python_version="3.13")
    .uv_pip_install("rdkit>=2026.9.1", "fastapi[standard]")
    .add_local_python_source("chromatography")
)


def score_request(body: dict[str, Any] | None = None) -> dict[str, Any]:
    from chromatography.common.types import Analyte, Goals, GradientSegment, HplcMethod
    from chromatography.hplc.score import score_method
    from chromatography.hplc.simulate import simulate_chromatogram

    payload = body or {}
    raw_analytes = payload.get("analytes") or [
        {"name": "acetaminophen", "smiles": "CC(=O)Nc1ccc(O)cc1"},
        {"name": "caffeine", "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C"},
        {"name": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    analytes = [Analyte(name=item["name"], smiles=item["smiles"]) for item in raw_analytes]
    goals = Goals(
        modality="hplc",
        max_run_time_min=float(payload.get("max_run_time_min", 12.0)),
        min_resolution=float(payload.get("min_resolution", 1.5)),
        analytes=analytes,
    )
    raw_gradient = payload.get("gradient") or [
        {"time_min": 0.0, "percent_b": 5.0},
        {"time_min": 8.0, "percent_b": 40.0},
        {"time_min": 10.0, "percent_b": 95.0},
    ]
    method = HplcMethod(
        column_id=str(payload.get("column_id", "c18_100x4.6_5um")),
        flow_ml_min=float(payload.get("flow_ml_min", 1.0)),
        temperature_c=float(payload.get("temperature_c", 30.0)),
        gradient=[
            GradientSegment(time_min=float(segment["time_min"]), percent_b=float(segment["percent_b"]))
            for segment in raw_gradient
        ],
    )
    simulation = simulate_chromatogram(analytes, method)
    score = score_method(goals, method, simulation)
    return {
        "modality": "hplc",
        "min_resolution": score.min_resolution,
        "total_time_min": score.total_time_min,
        "passed": score.passed,
        "penalties": score.penalties,
        "peaks": [
            {"name": peak.name, "retention_min": peak.retention_min, "width_min": peak.width_min}
            for peak in simulation.peaks
        ],
    }


@app.function(image=image, cpu=1.0)
def hplc_demo() -> dict:
    return score_request({})


@app.function(image=image, cpu=1.0)
@modal.fastapi_endpoint()
def demo_score() -> dict:
    return score_request({})


@app.function(image=image, cpu=1.0)
@modal.fastapi_endpoint(method="POST")
def demo_score_post(body: dict) -> dict:
    return score_request(body)


@app.local_entrypoint()
def main() -> None:
    print(hplc_demo.remote())
