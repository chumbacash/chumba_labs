import json
import os
import sys
from typing import Any

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


def meta_model_api_key() -> str | None:
    return os.environ.get("MODEL_API_KEY") or os.environ.get("META_API_KEY")

SYSTEM_PROMPT = (
    "You develop HPLC methods by calling tools. "
    "Never invent resolution (Rs) or retention times. "
    "Cite only numbers returned by simulate_hplc and score_hplc. "
    "Workflow: describe_analytes once, then simulate_hplc and score_hplc for a method. "
    "Use column_id from: c18_100x4.6_5um, c18_150x4.6_5um. "
    "After score_hplc returns, give a one-sentence summary and stop calling tools."
)


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


def _step(name: str, output: Any) -> dict[str, Any]:
    return {"tool": name, "output": output}


def run_local(goals: Goals) -> dict[str, Any]:
    analytes = goals_to_dict(goals)["analytes"]
    goals_payload = goals_to_dict(goals)
    steps = [_step("describe_analytes", describe_analytes(analytes))]
    best_score: dict[str, Any] | None = None
    best_simulation: dict[str, Any] = {}
    best_method: dict[str, Any] = {}
    for method in _bounded_methods()[:MAX_AGENT_STEPS]:
        simulation = simulate_hplc(analytes, method)
        steps.append(_step("simulate_hplc", simulation))
        if "error" in simulation:
            continue
        score = score_hplc(goals_payload, method, simulation)
        steps.append(_step("score_hplc", score))
        if _better(score, best_score):
            best_score = score
            best_simulation = simulation
            best_method = method
        if score.get("passed"):
            break
    return {
        "method": best_method,
        "simulation": best_simulation,
        "score": best_score or {},
        "steps": steps,
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


def _invoke_tool(name: str, args: dict[str, Any]) -> Any:
    tool = _tools_by_name().get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}
    return tool.invoke(args)


def run_spark(goals: Goals) -> dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

    goals_payload = goals_to_dict(goals)
    model = build_spark_model().bind_tools(list(HPLC_TOOLS))
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                "Find an HPLC method for these goals using the tools. "
                "Do not invent metrics.\n"
                + json.dumps(goals_payload)
            )
        ),
    ]
    steps: list[dict[str, Any]] = []
    score: dict[str, Any] | None = None
    simulation: dict[str, Any] | None = None
    explanation = ""
    max_model_turns = MAX_AGENT_STEPS + 4

    for _ in range(max_model_turns):
        ai = model.invoke(messages)
        messages.append(ai)
        text = _message_text(ai)
        if text:
            explanation = text
        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            if score is not None:
                break
            continue
        for call in tool_calls:
            name = call.get("name") or ""
            args = call.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            payload = _invoke_tool(name, args)
            steps.append(_step(name, payload))
            messages.append(
                ToolMessage(
                    content=json.dumps(payload),
                    tool_call_id=str(call.get("id") or name),
                )
            )
            if name == "simulate_hplc" and isinstance(payload, dict) and "peaks" in payload:
                simulation = payload
            if name == "score_hplc" and isinstance(payload, dict) and "min_resolution" in payload:
                score = payload

    if score is None:
        raise RuntimeError("Spark returned no score_hplc tool result")
    if simulation is None:
        simulation = score.get("simulation", {})
    method = score.get("method") or (simulation.get("method") if isinstance(simulation, dict) else {})
    return {
        "method": method,
        "simulation": simulation,
        "score": score,
        "steps": steps,
        "explanation": explanation,
    }


def run_hplc_iteration(goals: Goals) -> dict[str, Any]:
    if meta_model_api_key():
        print("hplc path: spark", file=sys.stderr)
        try:
            result = run_spark(goals)
            result["path"] = "spark"
            return result
        except Exception as exc:
            print(f"spark failed: {type(exc).__name__}", file=sys.stderr)
            result = run_local(goals)
            result["path"] = "spark-fallback"
            result["spark_error"] = type(exc).__name__
            return result
    print("hplc path: local", file=sys.stderr)
    result = run_local(goals)
    result["path"] = "local"
    return result
