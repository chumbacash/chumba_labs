from dataclasses import dataclass

from chromatography.common.smiles import analyte_descriptors
from chromatography.common.types import Analyte


@dataclass
class GcMethod:
    column_id: str
    oven_start_c: float
    oven_end_c: float
    ramp_c_min: float
    flow_ml_min: float


@dataclass
class GcPeak:
    name: str
    retention_min: float


@dataclass
class GcSimulationResult:
    peaks: list[GcPeak]
    total_time_min: float


def boiling_point_proxy_c(smiles: str) -> float:
    # Rough °C rank proxy fit to a few public normal boiling points. Not experimental.
    desc = analyte_descriptors(smiles)
    return (
        -44.0
        + 0.59 * desc["mw"]
        + 43.0 * desc["hbd"]
        + 2.35 * desc["tpsa"]
        + 22.6 * desc["logp"]
        + 55.0 * desc["aromatic_rings"]
    )


def simulate_gc_run(analytes: list[Analyte], method: GcMethod) -> GcSimulationResult:
    ramp = max(method.ramp_c_min, 0.1)
    flow = max(method.flow_ml_min, 0.1)
    peaks = []
    for analyte in analytes:
        bp = boiling_point_proxy_c(analyte.smiles)
        retention = max((bp - method.oven_start_c) / ramp, 0.2) / flow
        peaks.append(GcPeak(name=analyte.name, retention_min=retention))
    peaks.sort(key=lambda peak: peak.retention_min)
    ramp_time = (method.oven_end_c - method.oven_start_c) / ramp
    last_rt = peaks[-1].retention_min if peaks else 0.0
    total = max(ramp_time + 1.0, last_rt + 0.5)
    return GcSimulationResult(peaks=peaks, total_time_min=total)
