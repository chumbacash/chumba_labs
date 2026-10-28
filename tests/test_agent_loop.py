import importlib.util
import json
from pathlib import Path

import pytest

from agent.orchestrator import META_BASE_URL, META_MODEL, build_spark_model, demo_goals, goals_to_dict, run_hplc_iteration
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
