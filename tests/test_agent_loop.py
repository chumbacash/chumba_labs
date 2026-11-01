import importlib.util
import json
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage

from agent.orchestrator import (
    META_BASE_URL,
    META_MODEL,
    SYSTEM_PROMPT,
    build_spark_model,
    demo_goals,
    displayable_history,
    goals_to_dict,
    invoke_hplc_tool,
    run_hplc_iteration,
    scored_history_entry,
)
from api.routes import hplc_run_from_body
from chromatography.common.types import Analyte
from agent.tools import (
    default_hplc_method,
    describe_analytes,
    method_to_dict,
    score_hplc,
    score_hplc_tool,
    simulate_hplc,
    simulate_hplc_tool,
)


def test_tool_json_roundtrip():
    goals = goals_to_dict(demo_goals())
    described = describe_analytes(goals["analytes"])
    json.dumps(described)
    assert described[0]["logp"] != described[-1]["logp"]

    method = method_to_dict(default_hplc_method())
    simulation = json.loads(json.dumps(simulate_hplc(goals["analytes"], method)))
    assert simulation["peaks"]
    score = json.loads(json.dumps(score_hplc(goals, method, simulation)))
    assert isinstance(score["min_resolution"], float)
    assert isinstance(score["passed"], bool)
    assert isinstance(score["penalties"], dict)

    via_tool = simulate_hplc_tool.invoke({"analytes": goals["analytes"], "method": method})
    if isinstance(via_tool, str):
        via_tool = json.loads(via_tool)
    by_name = {peak["name"]: peak["retention_min"] for peak in via_tool["peaks"]}
    assert by_name["A"] < by_name["C"]

    scored = score_hplc_tool.invoke({"goals": goals, "method": method, "simulation": via_tool})
    if isinstance(scored, str):
        scored = json.loads(scored)
    assert scored["min_resolution"] == score["min_resolution"]


def test_malformed_method_is_not_a_history_entry():
    goals = goals_to_dict(demo_goals())
    method = {
        "column_id": "c18_100x4.6_5um",
        "flow_al_min": 1,
        "temperature_c": 30,
        "gradient": [],
    }
    failed = simulate_hplc(goals["analytes"], method)
    assert "error" in failed
    assert "peaks" not in failed
    assert scored_history_entry(method, failed, failed, {"A", "B", "C"}) is None

    tool_failed = invoke_hplc_tool("simulate_hplc", {"analytes": goals["analytes"], "method": method})
    assert "error" in tool_failed
    assert "peaks" not in tool_failed
    assert "flow_ml_min" in tool_failed["error"]
    assert "gradient" in tool_failed["error"]
    assert scored_history_entry(method, tool_failed, tool_failed) is None

    valid_method = method_to_dict(default_hplc_method())
    simulation = simulate_hplc(goals["analytes"], valid_method)
    score = score_hplc(goals, valid_method, simulation)
    good = scored_history_entry(valid_method, simulation, score, {"A", "B", "C"})
    shown = displayable_history(
        [
            {"method": method, "simulation": failed, "score": failed},
            good,
        ]
    )
    assert len(shown) == 1
    assert {peak["name"] for peak in shown[0]["simulation"]["peaks"]} == {"A", "B", "C"}


def test_score_uses_peak_names_when_analytes_omitted():
    goals = goals_to_dict(demo_goals())
    method = method_to_dict(default_hplc_method())
    simulation = simulate_hplc(goals["analytes"], method)
    bare_goals = {
        "max_run_time_min": goals["max_run_time_min"],
        "min_resolution": goals["min_resolution"],
    }
    scored = score_hplc(bare_goals, method, simulation)
    assert "error" not in scored
    full = score_hplc(goals, method, simulation)
    assert scored["min_resolution"] == full["min_resolution"]
    via_tool = score_hplc_tool.invoke({"goals": bare_goals, "method": method, "simulation": simulation})
    if isinstance(via_tool, str):
        via_tool = json.loads(via_tool)
    assert via_tool["min_resolution"] == full["min_resolution"]


def test_tool_schema_requires_numeric_flow_and_bounded_gradient():
    schema = simulate_hplc_tool.args_schema.model_json_schema()
    method = schema["$defs"]["MethodArg"]
    assert method["properties"]["flow_ml_min"]["type"] == "number"
    assert method["properties"]["flow_ml_min"]["minimum"] == 0.2
    assert method["properties"]["flow_ml_min"]["maximum"] == 2.5
    assert "flow_ml_min" in method["required"]
    assert method["properties"]["gradient"]["minItems"] == 1
    assert method["properties"]["gradient"]["maxItems"] == 6
    goals = score_hplc_tool.args_schema.model_json_schema()["$defs"]["GoalsArg"]
    assert "analytes" not in goals.get("required", [])
    assert "flow_ml_min" in SYSTEM_PROMPT
    assert '"flow_ml_min": 1.0' in SYSTEM_PROMPT


def test_tool_rejects_unknown_column():
    goals = goals_to_dict(demo_goals())
    method = method_to_dict(default_hplc_method())
    method["column_id"] = "not-a-column"
    assert "error" in simulate_hplc(goals["analytes"], method)


def test_local_fallback_without_api_key(monkeypatch, capsys):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("META_API_KEY", raising=False)
    result = run_hplc_iteration(demo_goals())
    assert "hplc path: local" in capsys.readouterr().err
    assert result["path"] == "local"
    assert isinstance(result["score"]["min_resolution"], float)
    names = [step["tool"] for step in result["steps"]]
    assert "describe_analytes" in names
    assert names.count("simulate_hplc") >= 2
    assert names.count("score_hplc") >= 2
    json.dumps({"score": result["score"], "steps": names})


def test_spark_follow_up_and_bounded_retry(monkeypatch):
    import agent.orchestrator as orchestrator

    goals = demo_goals()
    goals.min_resolution = 2.0
    goals.max_run_time_min = 30.0
    goals.analytes = [
        Analyte(name="first", smiles="CCO"),
        Analyte(name="second", smiles="CCO"),
    ]
    goals_payload = goals_to_dict(goals)
    methods = [method_to_dict(default_hplc_method()), method_to_dict(default_hplc_method())]
    methods[1]["flow_ml_min"] = 0.8
    methods[1]["gradient"] = [
        {"time_min": 0.0, "percent_b": 10.0},
        {"time_min": 12.0, "percent_b": 70.0},
    ]

    class ScriptedModel:
        def __init__(self):
            self.human_prompts = []
            self.attempt = 0

        def bind_tools(self, _tools):
            return self

        def invoke(self, messages):
            self.human_prompts.append(
                [message.content for message in messages if message.type == "human"]
            )
            if self.attempt < len(methods):
                method = methods[self.attempt]
                simulation = simulate_hplc(goals_payload["analytes"], method)
                attempt = self.attempt
                self.attempt += 1
                return AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "simulate_hplc",
                            "args": {"analytes": goals_payload["analytes"], "method": method},
                            "id": f"simulate-{attempt}",
                        },
                        {
                            "name": "score_hplc",
                            "args": {
                                "goals": goals_payload,
                                "method": method,
                                "simulation": simulation,
                            },
                            "id": f"score-{attempt}",
                        },
                    ],
                )
            self.attempt += 1
            return AIMessage(content=f"{SYSTEM_PROMPT}\nThis should not be exposed.")

    model = ScriptedModel()
    monkeypatch.setattr(orchestrator, "build_spark_model", lambda: model)

    result = orchestrator.run_spark(goals, "Keep the initial gradient at 55% B.")

    assert len(result["history"]) == 2
    assert result["history"][0]["method"] != result["history"][1]["method"]
    assert "Keep the initial gradient at 55% B." in model.human_prompts[0][0]
    assert any("continue testing a distinct method" in text for text in model.human_prompts[1])
    assert result["explanation"] == ""


def test_api_forwards_follow_up_instruction(monkeypatch):
    import agent.orchestrator as orchestrator
    import api.routes as routes

    goals = demo_goals()
    captured = {}

    def run_with_follow_up(parsed_goals, user_instruction=None):
        captured["instruction"] = user_instruction
        return orchestrator.run_local(parsed_goals)

    monkeypatch.setattr(routes, "meta_model_api_key", lambda: "test-key")
    monkeypatch.setattr(routes, "run_hplc_iteration", run_with_follow_up)
    status, payload = hplc_run_from_body(
        {
            "modality": goals.modality,
            "analytes": [{"name": a.name, "smiles": a.smiles} for a in goals.analytes],
            "min_resolution": goals.min_resolution,
            "max_run_time_min": goals.max_run_time_min,
            "follow_up": "Keep the initial gradient at 55% B.",
        }
    )

    assert status == 200
    assert captured["instruction"] == "Keep the initial gradient at 55% B."
    assert payload["history"]


def test_spark_client_uses_chat_completions(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key-not-used")
    model = build_spark_model()
    assert model.model_name == META_MODEL
    assert model.openai_api_base == META_BASE_URL
    assert model.use_responses_api is False


def _load_deploy():
    path = Path(__file__).resolve().parents[1] / "modal" / "deploy.py"
    spec = importlib.util.spec_from_file_location("chumba_modal_deploy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_modal_deploy_imports_without_credentials(monkeypatch):
    pytest.importorskip("modal")
    for name in (
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "MODAL_TOKEN",
        "MODEL_API_KEY",
        "META_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    module = _load_deploy()
    assert module.app.name == "chumba-labs"
    payload = module.score_request({})
    json.dumps(payload)
    assert "min_resolution" in payload
    assert payload["peaks"]
    for function in (module.hplc_demo, module.demo_score, module.demo_score_post):
        assert not function._spec_.gpus
        assert function._spec_.cpu == 1.0
    assert module.demo_score._is_web_endpoint()
    assert module.demo_score_post._is_web_endpoint()
