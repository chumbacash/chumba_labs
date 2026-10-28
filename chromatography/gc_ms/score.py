from chromatography.gc_ms.simulate import GcMethod, GcSimulationResult


def score_gc_method(
    max_run_time_min: float,
    min_peak_spacing_min: float,
    simulation: GcSimulationResult,
) -> dict:
    penalties: dict[str, float] = {}
    if simulation.total_time_min > max_run_time_min:
        penalties["run_time"] = simulation.total_time_min - max_run_time_min

    peaks = simulation.peaks
    if len(peaks) >= 2:
        spacings = [
            peaks[i + 1].retention_min - peaks[i].retention_min for i in range(len(peaks) - 1)
        ]
        min_spacing = min(spacings)
        if min_spacing < min_peak_spacing_min:
            penalties["spacing"] = min_peak_spacing_min - min_spacing

    return {
        "total_time_min": simulation.total_time_min,
        "passed": not penalties,
        "penalties": penalties,
    }
