import json
import os
import sys
from typing import Any

from pydantic import ValidationError

from chromatography.common.types import Analyte, Goals

from agent.tools import (
    HPLC_TOOLS,
    describe_analytes,
    goals_to_dict,
    method_to_dict,
    score_hplc,
    simulate_hplc,
    default_hplc_method,
)

META_BASE_URL = "https://api.meta.ai/v1"
META_MODEL = "muse-spark-1.3"
MAX_AGENT_STEPS = 5
MIN_RETRY_RESOLUTION = 2.0


def meta_model_api_key() -> str | None:
    return os.environ.get("MODEL_API_KEY") or os.environ.get("META_API_KEY")

def _system_prompt() -> str:
    example = json.dumps(method_to_dict(default_hplc_method()))
    return (
        "You develop HPLC methods by calling tools. "
        "Never invent resolution (Rs) or retention times. "
        "Cite only numbers returned by simulate_hplc and score_hplc. "
        "Workflow: describe_analytes once, then simulate_hplc and score_hplc for a method. "
        "Pass every user analyte (name and smiles) to describe_analytes and simulate_hplc. "
        "score_hplc needs goals.max_run_time_min, goals.min_resolution, method, and the "
        "simulation object from simulate_hplc. You may omit goals.analytes when that simulation "
        "already lists every peak name. "
        "Method keys are exactly column_id, flow_ml_min (a number in mL/min, 0.2-2.5), "
        "temperature_c (a number, 20-60), and gradient (1 to 6 objects with time_min and percent_b). "
        "Do not rename flow_ml_min. "
        f"Example method: {example}. "
        "column_id must be c18_100x4.6_5um or c18_150x4.6_5um. "
        "Honor the user's requested method constraints. If you change a requested setting, "
        "state what changed and why, using the tool results. "
        f"Keep testing distinct supported C18 methods until the goals pass and min_resolution "
        f"is at least {MIN_RETRY_RESOLUTION}, or until the retry limit is reached. "
        "Change gradient composition or timing between attempts. The simulator only models "
        "the listed C18 columns: do not claim that a stationary phase can or cannot separate "
        "a compound class, or that another phase is required. Describe only what the tested "
        "simulations show. After the final score, give a concise user-facing summary."
    )


SYSTEM_PROMPT = _system_prompt()


def demo_goals() -> Goals:
    return Goals(
        modality="hplc",
        max_run_time_min=12.0,
        min_resolution=1.5,
        analytes=[
            Analyte(name="A", smiles="CCO"),
            Analyte(name="B", smiles="CC(=O)O"),
            Analyte(name="C", smiles="c1ccccc1"),
        ],
    )


def _bounded_methods() -> list[dict[str, Any]]:
    return [
        method_to_dict(default_hplc_method()),
        {
            "column_id": "c18_150x4.6_5um",
            "flow_ml_min": 0.8,
            "temperature_c": 30.0,
            "gradient": [
                {"time_min": 0.0, "percent_b": 5.0},
                {"time_min": 12.0, "percent_b": 60.0},
            ],
        },
        {
            "column_id": "c18_150x4.6_5um",
            "flow_ml_min": 1.0,
            "temperature_c": 35.0,
            "gradient": [
                {"time_min": 0.0, "percent_b": 5.0},
                {"time_min": 6.0, "percent_b": 30.0},
                {"time_min": 11.0, "percent_b": 80.0},
            ],
        },
    ]


def _penalty_sum(score: dict[str, Any]) -> float:
    return float(sum(score.get("penalties", {}).values()))


def _better(candidate: dict[str, Any], incumbent: dict[str, Any] | None) -> bool:
    if incumbent is None:
        return True
    if bool(candidate.get("passed")) != bool(incumbent.get("passed")):
        return bool(candidate.get("passed"))
    if _penalty_sum(candidate) != _penalty_sum(incumbent):
        return _penalty_sum(candidate) < _penalty_sum(incumbent)
    return float(candidate.get("min_resolution", 0.0)) > float(incumbent.get("min_resolution", 0.0))


def _meets_retry_target(score: dict[str, Any], goals: Goals) -> bool:
    return bool(score.get("passed")) and float(score.get("min_resolution", 0.0)) >= max(
        MIN_RETRY_RESOLUTION,
        goals.min_resolution,
    )


def _retry_instruction(score: dict[str, Any], goals: Goals) -> str:
    target = max(MIN_RETRY_RESOLUTION, goals.min_resolution)
    return (
        f"The last scored method had min_resolution={score.get('min_resolution')} and "
        f"passed={score.get('passed')}; continue testing a distinct method. The minimum "
        f"resolution target for stopping is {target}, and the run-time goal is "
        f"{goals.max_run_time_min} minutes. Use only the supported C18 columns and vary "
        "the gradient. Preserve explicit user constraints when possible; if you deviate, "
        "explain the change and its measured result. Do not make claims about unmodeled "
        "stationary phases or absolute inability to separate analyte classes."
    )


def _user_facing_explanation(text: str) -> str:
    text = text.strip()
    lowered = text.lower()
    prompt_markers = (
        "you develop hplc methods by calling tools.",
        "method keys are exactly column_id",
        "after the final score, give a concise user-facing summary.",
    )
    if SYSTEM_PROMPT.lower() in lowered or any(marker in lowered for marker in prompt_markers):
        return ""
    return text


def _step(name: str, output: Any) -> dict[str, Any]:
    return {"tool": name, "output": output}


def _peak_names(simulation: Any) -> set[str] | None:
    if not isinstance(simulation, dict) or "error" in simulation:
        return None
    peaks = simulation.get("peaks")
    if not isinstance(peaks, list) or not peaks:
        return None
    names: set[str] = set()
    for peak in peaks:
        if not isinstance(peak, dict) or "name" not in peak:
            return None
        if "retention_min" not in peak or "width_min" not in peak:
            return None
        names.add(str(peak["name"]))
    return names


def scored_history_entry(
    method: Any,
    simulation: Any,
    score: Any,
    required_names: set[str] | None = None,
) -> dict[str, Any] | None:
    """A history row only when a score and a peak list both succeeded."""
    if not isinstance(score, dict) or "error" in score:
        return None
    if "min_resolution" not in score or "passed" not in score:
        return None
    sim = score.get("simulation") if isinstance(score.get("simulation"), dict) else simulation
    names = _peak_names(sim)
    if names is None:
        return None
    if required_names and not required_names.issubset(names):
        return None
    method_out = score.get("method") if isinstance(score.get("method"), dict) else method
    if not isinstance(method_out, dict) or "column_id" not in method_out:
        return None
    peaks = sim["peaks"]
    return {
        "method": method_out,
        "simulation": {
            "peaks": peaks,
            "total_time_min": float(sim.get("total_time_min", score.get("total_time_min", 0.0))),
        },
        "score": score,
    }


def displayable_history(entries: list[Any] | None) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        kept = scored_history_entry(entry.get("method"), entry.get("simulation"), entry.get("score"))
        if kept:
            cleaned.append(kept)
    return cleaned


def best_history_entry(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for entry in entries:
        if best is None or _better(entry["score"], best["score"]):
            best = entry
    return best


def _merge_analytes(provided: Any, goal_analytes: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(provided, list):
        return list(goal_analytes)
    kept: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in provided:
        if isinstance(item, dict) and item.get("name") and item.get("smiles"):
            name = str(item["name"])
            if name not in seen:
                kept.append({"name": name, "smiles": str(item["smiles"])})
                seen.add(name)
    for analyte in goal_analytes:
        if analyte["name"] not in seen:
            kept.append(dict(analyte))
            seen.add(analyte["name"])
    return kept or list(goal_analytes)


def _with_goal_analytes(name: str, args: dict[str, Any], goals: Goals) -> dict[str, Any]:
    prepared = dict(args)
    goal_analytes = [{"name": analyte.name, "smiles": analyte.smiles} for analyte in goals.analytes]
    if name in ("describe_analytes", "simulate_hplc"):
        prepared["analytes"] = _merge_analytes(prepared.get("analytes"), goal_analytes)
    elif name == "score_hplc":
        raw_goals = prepared.get("goals")
        if not isinstance(raw_goals, dict):
            prepared["goals"] = goals_to_dict(goals)
        else:
            merged = dict(raw_goals)
            merged["analytes"] = _merge_analytes(merged.get("analytes"), goal_analytes)
            merged.setdefault("max_run_time_min", goals.max_run_time_min)
            merged.setdefault("min_resolution", goals.min_resolution)
            merged.setdefault("modality", goals.modality)
            prepared["goals"] = merged
    return prepared


def _short_tool_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        messages: list[str] = []
        for err in exc.errors():
            loc = ".".join(str(item) for item in err.get("loc", ()))
            kind = str(err.get("type", ""))
            if loc.endswith("flow_ml_min") and kind in {
                "missing",
                "float_parsing",
                "float_type",
                "int_parsing",
                "int_type",
            }:
                messages.append("method needs numeric flow_ml_min and temperature_c")
            elif loc.endswith("temperature_c") and kind in {
                "missing",
                "float_parsing",
                "float_type",
                "int_parsing",
                "int_type",
            }:
                messages.append("method needs numeric flow_ml_min and temperature_c")
            elif loc.endswith("flow_ml_min") and kind in {"greater_than_equal", "less_than_equal"}:
                messages.append("flow_ml_min out of bounds (0.2-2.5)")
            elif loc.endswith("temperature_c") and kind in {"greater_than_equal", "less_than_equal"}:
                messages.append("temperature_c out of bounds (20-60)")
            elif "gradient" in loc and kind in {"too_short", "too_long", "missing"}:
                messages.append("gradient must have 1 to 6 segments")
            elif loc.endswith("percent_b") and kind in {"greater_than_equal", "less_than_equal"}:
                messages.append("percent_b out of bounds (0-100)")
            elif loc.endswith("column_id"):
                messages.append(f"unknown column_id: {err.get('input')}")
            elif kind == "value_error":
                messages.append(str(err.get("msg", "")).removeprefix("Value error, ") or "invalid tool arguments")
            elif "analytes" in loc and kind in {"missing", "too_short"}:
                messages.append("analytes must be a non-empty list")
            else:
                messages.append(f"{loc}: {err.get('msg')}")
        return "; ".join(dict.fromkeys(messages)) or "invalid tool arguments"
    text = str(exc).strip() or type(exc).__name__
    return text[:500]


def run_local(goals: Goals) -> dict[str, Any]:
    analytes = goals_to_dict(goals)["analytes"]
    goals_payload = goals_to_dict(goals)
    steps = [_step("describe_analytes", describe_analytes(analytes))]
    best_score: dict[str, Any] | None = None
    best_simulation: dict[str, Any] = {}
    best_method: dict[str, Any] = {}
    history: list[dict[str, Any]] = []
    for method in _bounded_methods()[:MAX_AGENT_STEPS]:
        simulation = simulate_hplc(analytes, method)
        steps.append(_step("simulate_hplc", simulation))
        if "error" in simulation:
            continue
        score = score_hplc(goals_payload, method, simulation)
        steps.append(_step("score_hplc", score))
        entry = scored_history_entry(
            method,
            simulation,
            score,
            {analyte.name for analyte in goals.analytes},
        )
        if entry is None:
            continue
        history.append(entry)
        if _better(entry["score"], best_score):
            best_score = entry["score"]
            best_simulation = entry["simulation"]
            best_method = entry["method"]
        if _meets_retry_target(entry["score"], goals):
            break
    return {
        "method": best_method,
        "simulation": best_simulation,
        "score": best_score or {},
        "steps": steps,
        "history": history,
        "explanation": "",
    }


def build_spark_model():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=META_MODEL,
        base_url=META_BASE_URL,
        api_key=meta_model_api_key() or "",
        use_responses_api=False,
    )


def _content_json(content: Any) -> dict[str, Any] | None:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _message_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(part for part in parts if part)
    return ""


def _tools_by_name():
    return {tool.name: tool for tool in HPLC_TOOLS}


def invoke_hplc_tool(name: str, args: dict[str, Any]) -> Any:
    tool = _tools_by_name().get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}
    if not isinstance(args, dict):
        return {"error": "tool arguments must be an object"}
    try:
        payload = tool.invoke(args)
    except Exception as exc:
        return {"error": _short_tool_error(exc)}
    if isinstance(payload, str):
        parsed = _content_json(payload)
        return parsed if parsed is not None else {"error": payload}
    return payload


def _record_score(
    payload: Any,
    args: dict[str, Any],
    last_simulation: dict[str, Any] | None,
    goals_payload: dict[str, Any],
    required_names: set[str],
) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or "error" in payload or "min_resolution" not in payload:
        return None
    method = payload.get("method") if isinstance(payload.get("method"), dict) else args.get("method")
    sim = payload.get("simulation") if isinstance(payload.get("simulation"), dict) else last_simulation
    entry = scored_history_entry(method, sim, payload, required_names)
    if entry is not None:
        return entry
    if not isinstance(method, dict):
        return None
    corrected = simulate_hplc(goals_payload["analytes"], method)
    if not isinstance(corrected, dict) or "error" in corrected:
        return None
    corrected_score = score_hplc(goals_payload, corrected.get("method") or method, corrected)
    return scored_history_entry(
        corrected.get("method") or method,
        corrected,
        corrected_score,
        required_names,
    )


def run_spark(goals: Goals, user_instruction: str | None = None) -> dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

    goals_payload = goals_to_dict(goals)
    model = build_spark_model().bind_tools(list(HPLC_TOOLS))
    request = (
        "Find an HPLC method for these goals using the tools. "
        "Do not invent metrics.\n"
        + json.dumps(goals_payload)
    )
    if user_instruction:
        request += "\n\nAdditional user instruction:\n" + user_instruction
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=request),
    ]
    steps: list[dict[str, Any]] = []
    best_score: dict[str, Any] | None = None
    best_simulation: dict[str, Any] | None = None
    best_method: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    last_simulation: dict[str, Any] | None = None
    explanation = ""
    required_names = {analyte.name for analyte in goals.analytes}
    score_attempts = 0
    max_model_turns = MAX_AGENT_STEPS * 3 + 4

    for _ in range(max_model_turns):
        ai = model.invoke(messages)
        messages.append(ai)
        text = _message_text(ai)
        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            if best_score is not None:
                explanation = _user_facing_explanation(text)
                break
            continue
        attempts_before_turn = score_attempts
        for call in tool_calls:
            name = call.get("name") or ""
            args = call.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            prepared = _with_goal_analytes(name, args, goals)
            if name == "score_hplc" and score_attempts >= MAX_AGENT_STEPS:
                payload = {"error": "method retry limit reached"}
            else:
                payload = invoke_hplc_tool(name, prepared)
            steps.append(_step(name, payload))
            messages.append(
                ToolMessage(
                    content=json.dumps(payload),
                    tool_call_id=str(call.get("id") or name),
                )
            )
            if (
                name == "simulate_hplc"
                and isinstance(payload, dict)
                and "error" not in payload
                and "peaks" in payload
            ):
                last_simulation = payload
            if name == "score_hplc":
                entry = _record_score(
                    payload,
                    prepared,
                    last_simulation,
                    goals_payload,
                    required_names,
                )
                if entry is None:
                    continue
                score_attempts += 1
                history.append(entry)
                if _better(entry["score"], best_score):
                    best_score = entry["score"]
                    best_simulation = entry["simulation"]
                    best_method = entry["method"]
        if best_score is not None and not _meets_retry_target(best_score, goals):
            if score_attempts >= MAX_AGENT_STEPS:
                continue
            if score_attempts > attempts_before_turn:
                messages.append(HumanMessage(content=_retry_instruction(best_score, goals)))

    if best_score is None:
        raise RuntimeError("Spark returned no score_hplc tool result")
    if best_simulation is None:
        best_simulation = best_score.get("simulation", {})
    if best_method is None:
        best_method = best_score.get("method") or (
            best_simulation.get("method") if isinstance(best_simulation, dict) else {}
        )
    return {
        "method": best_method,
        "simulation": best_simulation,
        "score": best_score,
        "steps": steps,
        "history": history,
        "explanation": explanation,
    }


def run_hplc_iteration(
    goals: Goals,
    user_instruction: str | None = None,
) -> dict[str, Any]:
    if meta_model_api_key():
        print("hplc path: spark", file=sys.stderr)
        try:
            result = run_spark(goals, user_instruction)
            result["path"] = "spark"
            return result
        except Exception as exc:
            if user_instruction:
                raise RuntimeError("Spark could not complete the follow-up instruction") from exc
            print(f"spark failed: {type(exc).__name__}", file=sys.stderr)
            result = run_local(goals)
            result["path"] = "spark-fallback"
            result["spark_error"] = type(exc).__name__
            return result
    if user_instruction:
        raise RuntimeError("Follow-up instructions require the Meta Model API key")
    print("hplc path: local", file=sys.stderr)
    result = run_local(goals)
    result["path"] = "local"
    return result
