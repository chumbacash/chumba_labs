from dataclasses import dataclass, field
from typing import Literal

Modality = Literal["hplc", "gc_ms"]


@dataclass
class Analyte:
    name: str
    smiles: str


@dataclass
class Goals:
    modality: Modality
    max_run_time_min: float
    min_resolution: float
    analytes: list[Analyte] = field(default_factory=list)


@dataclass
class GradientSegment:
    time_min: float
    percent_b: float


@dataclass
class HplcMethod:
    column_id: str
    flow_ml_min: float
    temperature_c: float
    gradient: list[GradientSegment]


@dataclass
class SimulatedPeak:
    name: str
    retention_min: float
    width_min: float


@dataclass
class SimulationResult:
    peaks: list[SimulatedPeak]
    total_time_min: float


@dataclass
class ScoreResult:
    min_resolution: float
    total_time_min: float
    passed: bool
    penalties: dict[str, float] = field(default_factory=dict)
