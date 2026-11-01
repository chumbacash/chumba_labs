from typing import Any

from chromatography.common.types import Analyte, Goals

from agent.orchestrator import (
    best_history_entry,
    demo_goals,
    displayable_history,
    meta_model_api_key,
    run_hplc_iteration,
)


def health() -> dict:
    return {"status": "ok"}


def goals_from_body(body: dict[str, Any]) -> Goals | dict[str, str]:
    if not isinstance(body, dict):
        return {"error": "body must be a JSON object"}
    modality = body.get("modality", "hplc")
    if modality not in ("hplc", "gc_ms"):
        return {"error": "modality must be hplc or gc_ms"}
    try:
        max_run_time_min = float(body.get("max_run_time_min", 12.0))
        min_resolution = float(body.get("min_resolution", 1.5))
    except (TypeError, ValueError):
        return {"error": "max_run_time_min and min_resolution must be numbers"}
    raw_analytes = body.get("analytes")
    if not isinstance(raw_analytes, list) or not raw_analytes:
        return {"error": "analytes must be a non-empty list"}
    analytes: list[Analyte] = []
    for item in raw_analytes:
        if not isinstance(item, dict) or "name" not in item or "smiles" not in item:
            return {"error": "each analyte needs name and smiles"}
        analytes.append(Analyte(name=str(item["name"]), smiles=str(item["smiles"])))
    return Goals(
        modality=modality,
        max_run_time_min=max_run_time_min,
        min_resolution=min_resolution,
        analytes=analytes,
    )


def _simulation_for_ui(simulation: dict[str, Any]) -> dict[str, Any]:
    if not simulation:
        return {"peaks": [], "total_time_min": 0.0}
    peaks = simulation.get("peaks") or []
    if isinstance(simulation.get("simulation"), dict):
        inner = simulation["simulation"]
        peaks = inner.get("peaks") or peaks
        total = inner.get("total_time_min", simulation.get("total_time_min", 0.0))
    else:
        total = simulation.get("total_time_min", 0.0)
    return {"peaks": peaks, "total_time_min": float(total)}


def hplc_run_payload(goals: Goals, result: dict[str, Any]) -> dict[str, Any]:
    history = displayable_history(result.get("history") or [])
    best = best_history_entry(history)
    if best is None:
        fallback = displayable_history(
            [
                {
                    "method": result.get("method") or {},
                    "simulation": result.get("simulation") or {},
                    "score": result.get("score") or {},
                }
            ]
        )
        history = fallback
        best = best_history_entry(history)
    if best:
        score = best["score"]
        simulation = best["simulation"]
        method = best["method"]
    else:
        score = {}
        simulation = _simulation_for_ui({})
        method = {}
    payload: dict[str, Any] = {
        "path": result.get("path", "local"),
        "modality": goals.modality,
        "min_resolution": score.get("min_resolution"),
        "total_time_min": score.get("total_time_min"),
        "passed": score.get("passed"),
        "penalties": score.get("penalties", {}),
        "method": method,
        "simulation": simulation,
        "score": score,
        "steps": result.get("steps", []),
        "history": history,
        "explanation": result.get("explanation", ""),
        "iterations": len(history),
    }
    if result.get("spark_error"):
        payload["spark_error"] = result["spark_error"]
    return payload


def gc_ms_not_implemented_payload(goals: Goals) -> dict[str, Any]:
    return {
        "path": "gc_ms",
        "modality": "gc_ms",
        "message": "GC-MS method development is not implemented in the UI yet.",
        "min_resolution": None,
        "total_time_min": None,
        "passed": False,
        "penalties": {},
        "method": {},
        "simulation": {"peaks": [], "total_time_min": 0.0},
        "score": {},
        "steps": [],
        "history": [],
        "explanation": "",
        "iterations": 0,
    }


def hplc_demo_run() -> dict:
    goals = demo_goals()
    result = run_hplc_iteration(goals)
    payload = hplc_run_payload(goals, result)
    slim = {
        "path": payload["path"],
        "modality": payload["modality"],
        "min_resolution": payload["min_resolution"],
        "total_time_min": payload["total_time_min"],
        "passed": payload["passed"],
        "penalties": payload["penalties"],
        "iterations": payload["iterations"],
    }
    if payload.get("explanation"):
        slim["explanation"] = payload["explanation"]
    return slim


def hplc_run_from_body(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    parsed = goals_from_body(body)
    if isinstance(parsed, dict) and "error" in parsed:
        return 400, parsed
    goals = parsed
    assert isinstance(goals, Goals)
    if goals.modality == "gc_ms":
        return 200, gc_ms_not_implemented_payload(goals)
    follow_up = body.get("follow_up")
    if follow_up is not None and not isinstance(follow_up, str):
        return 400, {"error": "follow_up must be a string"}
    follow_up = follow_up.strip() if follow_up else None
    if follow_up and not meta_model_api_key():
        return 400, {"error": "Follow-up instructions require the Meta Model API key"}
    try:
        result = run_hplc_iteration(goals, user_instruction=follow_up)
    except RuntimeError as exc:
        return 502, {"error": str(exc)}
    return 200, hplc_run_payload(goals, result)
