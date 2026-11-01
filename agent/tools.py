from typing import Any, Literal

from langchain.tools import tool
from pydantic import BaseModel, ConfigDict, Field, model_validator

from chromatography.common.smiles import analyte_descriptors
from chromatography.common.types import (
    Analyte,
    Goals,
    GradientSegment,
    HplcMethod,
    SimulatedPeak,
    SimulationResult,
)
from chromatography.hplc.catalog import COLUMNS
from chromatography.hplc.score import score_method
from chromatography.hplc.simulate import simulate_chromatogram

TOOL_NAMES = (
    "describe_analytes",
    "simulate_hplc",
    "score_hplc",
)

class AnalyteArg(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Peak label. Preserved exactly; do not merge names.")
    smiles: str = Field(..., description="RDKit SMILES string.")


class GradientArg(BaseModel):
    model_config = ConfigDict(extra="ignore")

    time_min: float = Field(..., description="Gradient time in minutes. Times must be non-decreasing.")
    percent_b: float = Field(..., ge=0, le=100, description="Organic solvent percent B, 0-100.")


class MethodArg(BaseModel):
    """HPLC method. flow_ml_min must be that exact key and a number."""

    model_config = ConfigDict(extra="ignore")

    column_id: Literal["c18_100x4.6_5um", "c18_150x4.6_5um"]
    flow_ml_min: float = Field(
        ...,
        ge=0.2,
        le=2.5,
        description=(
            "Flow in mL/min. JSON key must be exactly flow_ml_min (number, example 1.0). "
            "Do not send flow_al_min or a string."
        ),
    )
    temperature_c: float = Field(..., ge=20, le=60, description="Column temperature in °C, 20-60.")
    gradient: list[GradientArg] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="1 to 6 segments. Example: [{\"time_min\": 0, \"percent_b\": 5}, {\"time_min\": 8, \"percent_b\": 40}].",
    )

    @model_validator(mode="after")
    def _gradient_times(self) -> "MethodArg":
        previous = -1.0
        for segment in self.gradient:
            if segment.time_min < previous:
                raise ValueError("gradient times must be non-decreasing")
            previous = segment.time_min
        return self


class GoalsArg(BaseModel):
    model_config = ConfigDict(extra="ignore")

    max_run_time_min: float = Field(..., gt=0)
    min_resolution: float = Field(..., ge=0)
    modality: Literal["hplc", "gc_ms"] = "hplc"
    analytes: list[AnalyteArg] = Field(
        default_factory=list,
        description=(
            "Same analytes as the user goals. Optional when simulation.peaks already has a name "
            "for every compound; those peak names are scored if this list is omitted."
        ),
    )


class PeakArg(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    retention_min: float
    width_min: float


class SimulationArg(BaseModel):
    model_config = ConfigDict(extra="ignore")

    peaks: list[PeakArg] = Field(..., min_length=1)
    total_time_min: float


class DescribeArgs(BaseModel):
    analytes: list[AnalyteArg] = Field(..., min_length=1)


class SimulateArgs(BaseModel):
    analytes: list[AnalyteArg] = Field(
        ...,
        min_length=1,
        description="Every analyte from the user goals, each with name and smiles.",
    )
    method: MethodArg


class ScoreArgs(BaseModel):
    goals: GoalsArg = Field(
        ...,
        description="max_run_time_min and min_resolution. analytes may be omitted if simulation.peaks is complete.",
    )
    method: MethodArg
    simulation: SimulationArg = Field(
        ...,
        description="The object returned by simulate_hplc (peaks and total_time_min).",
    )


def default_hplc_method() -> HplcMethod:
    return HplcMethod(
        column_id="c18_100x4.6_5um",
        flow_ml_min=1.0,
        temperature_c=30.0,
        gradient=[
            GradientSegment(time_min=0.0, percent_b=5.0),
            GradientSegment(time_min=8.0, percent_b=40.0),
            GradientSegment(time_min=10.0, percent_b=95.0),
        ],
    )


def method_to_dict(method: HplcMethod) -> dict[str, Any]:
    return {
        "column_id": method.column_id,
        "flow_ml_min": method.flow_ml_min,
        "temperature_c": method.temperature_c,
        "gradient": [
            {"time_min": segment.time_min, "percent_b": segment.percent_b}
            for segment in method.gradient
        ],
    }


def goals_to_dict(goals: Goals) -> dict[str, Any]:
    return {
        "modality": goals.modality,
        "max_run_time_min": goals.max_run_time_min,
        "min_resolution": goals.min_resolution,
        "analytes": [{"name": analyte.name, "smiles": analyte.smiles} for analyte in goals.analytes],
    }


def _error(message: str) -> dict[str, str]:
    return {"error": message}


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


def _analytes(items: list[dict[str, Any]]) -> list[Analyte] | dict[str, str]:
    if not isinstance(items, list) or not items:
        return _error("analytes must be a non-empty list")
    analytes: list[Analyte] = []
    for item in items:
        if not isinstance(item, dict) or "name" not in item or "smiles" not in item:
            return _error("each analyte needs name and smiles")
        analytes.append(Analyte(name=str(item["name"]), smiles=str(item["smiles"])))
    return analytes


def _analytes_from_peaks(simulation: dict[str, Any]) -> list[Analyte] | dict[str, str]:
    peaks = simulation.get("peaks") if isinstance(simulation, dict) else None
    if not isinstance(peaks, list) or not peaks:
        return _error("analytes must be a non-empty list")
    analytes: list[Analyte] = []
    for peak in peaks:
        if isinstance(peak, dict) and peak.get("name"):
            analytes.append(Analyte(name=str(peak["name"]), smiles=""))
    if not analytes:
        return _error("analytes must be a non-empty list")
    return analytes


def _method(data: dict[str, Any]) -> HplcMethod | dict[str, str]:
    if not isinstance(data, dict):
        return _error("method must be an object")
    column_id = data.get("column_id")
    if column_id not in COLUMNS:
        return _error(f"unknown column_id: {column_id}")
    try:
        flow = float(data["flow_ml_min"])
        temperature = float(data["temperature_c"])
    except (KeyError, TypeError, ValueError):
        return _error("method needs numeric flow_ml_min and temperature_c")
    if not 0.2 <= flow <= 2.5:
        return _error("flow_ml_min out of bounds (0.2-2.5)")
    if not 20.0 <= temperature <= 60.0:
        return _error("temperature_c out of bounds (20-60)")
    raw_gradient = data.get("gradient")
    if not isinstance(raw_gradient, list) or not 1 <= len(raw_gradient) <= 6:
        return _error("gradient must have 1 to 6 segments")
    gradient: list[GradientSegment] = []
    previous = -1.0
    for segment in raw_gradient:
        if not isinstance(segment, dict):
            return _error("gradient segment must be an object")
        try:
            time_min = float(segment["time_min"])
            percent_b = float(segment["percent_b"])
        except (KeyError, TypeError, ValueError):
            return _error("gradient segment needs time_min and percent_b")
        if time_min < previous:
            return _error("gradient times must be non-decreasing")
        if not 0.0 <= percent_b <= 100.0:
            return _error("percent_b out of bounds (0-100)")
        previous = time_min
        gradient.append(GradientSegment(time_min=time_min, percent_b=percent_b))
    return HplcMethod(
        column_id=str(column_id),
        flow_ml_min=flow,
        temperature_c=temperature,
        gradient=gradient,
    )


def _peaks(simulation: dict[str, Any]) -> dict[str, str] | None:
    peaks = simulation.get("peaks")
    if not isinstance(peaks, list):
        return _error("simulation.peaks must be a list")
    for peak in peaks:
        if not isinstance(peak, dict):
            return _error("simulation peak must be an object")
        for key in ("name", "retention_min", "width_min"):
            if key not in peak:
                return _error(f"simulation peak missing {key}")
    if "total_time_min" not in simulation:
        return _error("simulation.total_time_min is required")
    return None


def describe_analytes(analytes: list[dict[str, Any]]) -> list[dict[str, Any]] | dict[str, str]:
    """RDKit descriptors for each analyte (logp, tpsa, mw, hbd, hba, aromatic_rings)."""
    parsed = _analytes(_dump(analytes))
    if isinstance(parsed, dict):
        return parsed
    described: list[dict[str, Any]] = []
    for analyte in parsed:
        try:
            descriptors = analyte_descriptors(analyte.smiles)
        except ValueError as exc:
            described.append({"name": analyte.name, "smiles": analyte.smiles, "error": str(exc)})
            continue
        described.append({"name": analyte.name, "smiles": analyte.smiles, **descriptors})
    return described


def simulate_hplc(
    analytes: list[dict[str, Any]],
    method: dict[str, Any],
) -> dict[str, Any]:
    """Simulate HPLC peaks. Returns retention_min from the LSS model only.

    method.flow_ml_min is a number in mL/min (0.2-2.5). gradient has 1 to 6 segments.
    Example method: {"column_id": "c18_100x4.6_5um", "flow_ml_min": 1.0, "temperature_c": 30,
    "gradient": [{"time_min": 0, "percent_b": 5}, {"time_min": 8, "percent_b": 40}, {"time_min": 10, "percent_b": 95}]}.
    """
    parsed_analytes = _analytes(_dump(analytes))
    if isinstance(parsed_analytes, dict):
        return parsed_analytes
    parsed_method = _method(_dump(method))
    if isinstance(parsed_method, dict):
        return parsed_method
    try:
        simulation = simulate_chromatogram(parsed_analytes, parsed_method)
    except ValueError as exc:
        return _error(str(exc))
    return {
        "method": method_to_dict(parsed_method),
        "peaks": [
            {
                "name": peak.name,
                "retention_min": peak.retention_min,
                "width_min": peak.width_min,
            }
            for peak in simulation.peaks
        ],
        "total_time_min": simulation.total_time_min,
    }


def score_hplc(
    goals: dict[str, Any],
    method: dict[str, Any],
    simulation: dict[str, Any],
) -> dict[str, Any]:
    """Score a simulation. min_resolution and penalties come only from this tool.

    Pass goals.max_run_time_min and goals.min_resolution. Analytes are optional when
    simulation.peaks already lists every compound by name.
    """
    goals = _dump(goals)
    method = _dump(method)
    simulation = _dump(simulation)
    if not isinstance(goals, dict):
        return _error("goals must be an object")
    parsed_method = _method(method)
    if isinstance(parsed_method, dict):
        return parsed_method
    if not isinstance(simulation, dict):
        return _error("simulation must be an object")
    peak_error = _peaks(simulation)
    if peak_error:
        return peak_error
    raw_analytes = goals.get("analytes") or []
    if isinstance(raw_analytes, list) and raw_analytes:
        parsed_analytes = _analytes(raw_analytes)
    else:
        parsed_analytes = _analytes_from_peaks(simulation)
    if isinstance(parsed_analytes, dict):
        return parsed_analytes
    try:
        parsed_goals = Goals(
            modality="hplc",
            max_run_time_min=float(goals["max_run_time_min"]),
            min_resolution=float(goals["min_resolution"]),
            analytes=parsed_analytes,
        )
    except (KeyError, TypeError, ValueError):
        return _error("goals need max_run_time_min and min_resolution")
    peaks = [
        SimulatedPeak(
            name=str(peak["name"]),
            retention_min=float(peak["retention_min"]),
            width_min=float(peak["width_min"]),
        )
        for peak in simulation["peaks"]
    ]
    scored = score_method(
        parsed_goals,
        parsed_method,
        SimulationResult(peaks=peaks, total_time_min=float(simulation["total_time_min"])),
    )
    return {
        "min_resolution": scored.min_resolution,
        "total_time_min": scored.total_time_min,
        "passed": scored.passed,
        "penalties": scored.penalties,
        "method": method_to_dict(parsed_method),
        "simulation": {
            "peaks": simulation["peaks"],
            "total_time_min": float(simulation["total_time_min"]),
        },
    }


describe_analytes_tool = tool(args_schema=DescribeArgs)(describe_analytes)
simulate_hplc_tool = tool(args_schema=SimulateArgs)(simulate_hplc)
score_hplc_tool = tool(args_schema=ScoreArgs)(score_hplc)

HPLC_TOOLS = (describe_analytes_tool, simulate_hplc_tool, score_hplc_tool)
