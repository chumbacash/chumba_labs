from agent.orchestrator import demo_goals, run_hplc_iteration


def health() -> dict:
    return {"status": "ok"}


def hplc_demo_run() -> dict:
    goals = demo_goals()
    result = run_hplc_iteration(goals)
    score = result["score"]
    payload = {
        "path": result["path"],
        "modality": goals.modality,
        "min_resolution": score["min_resolution"],
        "total_time_min": score["total_time_min"],
        "passed": score["passed"],
        "penalties": score["penalties"],
        "iterations": sum(1 for step in result.get("steps", []) if step.get("tool") == "score_hplc"),
    }
    if result.get("explanation"):
        payload["explanation"] = result["explanation"]
    return payload
