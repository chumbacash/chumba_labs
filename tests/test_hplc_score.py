import pytest

from chromatography.common.smiles import validate_smiles
from chromatography.common.types import Analyte, Goals, GradientSegment, HplcMethod
from chromatography.gc_ms.simulate import GcMethod, simulate_gc_run
from chromatography.hplc.score import score_method
from chromatography.hplc.simulate import simulate_chromatogram


def test_simulate_and_score_improves_with_spread_gradient():
    analytes = [
        Analyte(name="A", smiles="CCO"),
        Analyte(name="B", smiles="CC(=O)O"),
        Analyte(name="C", smiles="c1ccccc1"),
    ]
    goals = Goals(modality="hplc", max_run_time_min=15.0, min_resolution=0.5, analytes=analytes)

    tight = HplcMethod(
        column_id="c18_100x4.6_5um",
        flow_ml_min=1.2,
        temperature_c=30.0,
        gradient=[GradientSegment(0.0, 10.0), GradientSegment(8.0, 10.0)],
    )
    wide = HplcMethod(
        column_id="c18_150x4.6_5um",
        flow_ml_min=0.8,
        temperature_c=30.0,
        gradient=[GradientSegment(0.0, 5.0), GradientSegment(12.0, 60.0)],
    )

    sim_tight = simulate_chromatogram(analytes, tight)
    sim_wide = simulate_chromatogram(analytes, wide)
    score_tight = score_method(goals, tight, sim_tight)
    score_wide = score_method(goals, wide, sim_wide)

    assert sim_tight.peaks[0].retention_min <= sim_tight.peaks[-1].retention_min
    assert score_wide.min_resolution >= score_tight.min_resolution or score_wide.passed


def _demo_method() -> HplcMethod:
    return HplcMethod(
        column_id="c18_100x4.6_5um",
        flow_ml_min=1.0,
        temperature_c=30.0,
        gradient=[
            GradientSegment(0.0, 5.0),
            GradientSegment(10.0, 90.0),
        ],
    )


def test_rp_elution_ethanol_before_toluene():
    analytes = [
        Analyte(name="toluene", smiles="Cc1ccccc1"),
        Analyte(name="ethanol", smiles="CCO"),
    ]
    sim = simulate_chromatogram(analytes, _demo_method())
    by_name = {peak.name: peak.retention_min for peak in sim.peaks}
    assert by_name["ethanol"] < by_name["toluene"]


def test_invalid_smiles_rejected():
    assert validate_smiles("CCO")
    assert not validate_smiles("not_a_smiles")
    assert not validate_smiles("")
    with pytest.raises(ValueError):
        simulate_chromatogram([Analyte(name="bad", smiles="not_a_smiles")], _demo_method())


def test_gc_elution_follows_boiling_point_proxy():
    analytes = [
        Analyte(name="toluene", smiles="Cc1ccccc1"),
        Analyte(name="ethanol", smiles="CCO"),
    ]
    method = GcMethod(
        column_id="db5_30m",
        oven_start_c=40.0,
        oven_end_c=280.0,
        ramp_c_min=10.0,
        flow_ml_min=1.0,
    )
    sim = simulate_gc_run(analytes, method)
    by_name = {peak.name: peak.retention_min for peak in sim.peaks}
    assert by_name["ethanol"] < by_name["toluene"]
