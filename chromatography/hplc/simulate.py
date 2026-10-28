from chromatography.common.smiles import analyte_descriptors
from chromatography.common.types import Analyte, HplcMethod, SimulatedPeak, SimulationResult
from chromatography.hplc.catalog import get_column

# LSS-style approximation, not a validated chromatographic model:
# log k(φ) = log k_w − S·φ. log k_w and S come from RDKit descriptors.
# Higher MolLogP elutes later in reversed phase. φ is the organic fraction.


def _column(method: HplcMethod) -> dict:
    return get_column(method.column_id) or {
        "length_mm": 100.0,
        "id_mm": 4.6,
        "particle_um": 5.0,
    }


def _void_time_min(method: HplcMethod) -> float:
    col = _column(method)
    length_cm = col["length_mm"] / 10.0
    diameter_cm = col["id_mm"] / 10.0
    void_ml = 0.5 * length_cm * diameter_cm**2
    return void_ml / max(method.flow_ml_min, 0.05)


def _phi(method: HplcMethod, t_min: float) -> float:
    gradient = method.gradient
    if not gradient:
        return 0.05
    if t_min <= gradient[0].time_min:
        return gradient[0].percent_b / 100.0
    for left, right in zip(gradient, gradient[1:]):
        if t_min <= right.time_min:
            span = right.time_min - left.time_min
            if span <= 0:
                return right.percent_b / 100.0
            frac = (t_min - left.time_min) / span
            percent_b = left.percent_b + frac * (right.percent_b - left.percent_b)
            return percent_b / 100.0
    return gradient[-1].percent_b / 100.0


def _lss_params(desc: dict[str, float], temperature_c: float) -> tuple[float, float]:
    logp = desc["logp"]
    log_kw = (
        0.45
        + 1.0 * logp
        - 0.006 * desc["tpsa"]
        - 0.04 * desc["hbd"]
        - 0.02 * desc["hba"]
        + 0.08 * desc["aromatic_rings"]
    )
    log_kw -= 0.01 * (temperature_c - 25.0)
    s_phi = 2.4 + 0.3 * max(logp, 0.0) + 0.006 * desc["mw"]
    return log_kw, max(s_phi, 1.5)


def _retention_min(desc: dict[str, float], method: HplcMethod, t0: float) -> float:
    log_kw, s_phi = _lss_params(desc, method.temperature_c)
    dt = 0.025
    t_min = 0.0
    migrated = 0.0
    limit = 90.0
    while t_min < limit and migrated < 1.0:
        log_k = log_kw - s_phi * _phi(method, t_min)
        log_k = min(max(log_k, -1.5), 4.0)
        k = 10.0**log_k
        step = dt / (t0 * (1.0 + k))
        if step <= 0:
            break
        if migrated + step >= 1.0:
            t_min += dt * (1.0 - migrated) / step
            break
        migrated += step
        t_min += dt
    return t_min


def _width_min(method: HplcMethod, retention_min: float) -> float:
    col = _column(method)
    plates = col["length_mm"] / (2.0 * col["particle_um"] * 0.001)
    plates = max(plates, 100.0)
    width = 2.355 * retention_min / plates**0.5
    return max(width, 0.02)


def simulate_chromatogram(analytes: list[Analyte], method: HplcMethod) -> SimulationResult:
    t0 = _void_time_min(method)
    peaks: list[SimulatedPeak] = []
    for analyte in analytes:
        desc = analyte_descriptors(analyte.smiles)
        retention = _retention_min(desc, method, t0)
        peaks.append(
            SimulatedPeak(
                name=analyte.name,
                retention_min=retention,
                width_min=_width_min(method, retention),
            )
        )
    peaks.sort(key=lambda peak: peak.retention_min)
    end_gradient = method.gradient[-1].time_min if method.gradient else 10.0
    last_rt = peaks[-1].retention_min if peaks else 0.0
    total = max(end_gradient, last_rt + 0.5)
    return SimulationResult(peaks=peaks, total_time_min=total)
