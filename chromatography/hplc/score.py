from chromatography.common.types import Goals, HplcMethod, ScoreResult, SimulationResult


def _pair_resolution(p1_ret: float, p2_ret: float, w1: float, w2: float) -> float:
    if p2_ret <= p1_ret:
        return 0.0
    return 1.18 * (p2_ret - p1_ret) / (w1 + w2)


def score_method(
    goals: Goals,
    method: HplcMethod,
    simulation: SimulationResult,
) -> ScoreResult:
    penalties: dict[str, float] = {}
    peaks = simulation.peaks

    if len(peaks) < 2:
        rs_min = 0.0
    else:
        rs_values = []
        for i in range(len(peaks) - 1):
            rs_values.append(
                _pair_resolution(
                    peaks[i].retention_min,
                    peaks[i + 1].retention_min,
                    peaks[i].width_min,
                    peaks[i + 1].width_min,
                )
            )
        rs_min = min(rs_values)

    if simulation.total_time_min > goals.max_run_time_min:
        penalties["run_time"] = simulation.total_time_min - goals.max_run_time_min

    if rs_min < goals.min_resolution:
        penalties["resolution"] = goals.min_resolution - rs_min

    passed = not penalties
    return ScoreResult(
        min_resolution=rs_min,
        total_time_min=simulation.total_time_min,
        passed=passed,
        penalties=penalties,
    )
