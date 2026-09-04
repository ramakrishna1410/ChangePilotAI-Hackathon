from app.agents.effort_calculator import compute
from app.models import CostBand, EffortEstimateDraft, EffortSettings

BANDS = [
    CostBand(label="< 1 day", upper_bound_days=1, cost_eur=170),
    CostBand(label="1-2 days", upper_bound_days=2, cost_eur=273),
    CostBand(label="2-5 days", upper_bound_days=5, cost_eur=505),
    CostBand(label="5-10 days", upper_bound_days=10, cost_eur=1282),
    CostBand(label="10-15 days", upper_bound_days=15, cost_eur=3300),
    CostBand(label="15-20 days", upper_bound_days=20, cost_eur=4442),
]


def settings(change_mgmt=0.5, coord_pct=0.10):
    return EffortSettings(
        change_management_default_days=change_mgmt,
        enhancement_coordination_percent=coord_pct,
        cost_bands=BANDS,
    )


def draft(analysis=0.1, build=1.0, testing=0.5, uat=0.25):
    return EffortEstimateDraft(
        analysis_design_days=analysis,
        build_days=build,
        testing_sit_days=testing,
        uat_support_days=uat,
        complexity="Medium",
        confidence=0.7,
        rationale="test",
    )


def test_coordination_is_percentage_of_dev_subtotal():
    result = compute(draft(analysis=1, build=2, testing=1, uat=0.5), settings(coord_pct=0.10))
    # dev subtotal = 1+2+1+0.5 = 4.5; coordination = 10% of 4.5 = 0.45
    assert result.enhancement_coordination_days == 0.45
    assert result.total_days == 4.5 + 0.5 + 0.45  # + change mgmt


def test_band_lower_bound_is_exclusive_boundary_goes_to_next_band():
    # total exactly 1.0 should NOT match "< 1 day" (upper_bound_days=1 is exclusive)
    result = compute(draft(analysis=0, build=0.5, testing=0, uat=0), settings(change_mgmt=0.5, coord_pct=0))
    assert result.total_days == 1.0
    assert result.cost_eur == 273
    assert result.cost_band_label == "1-2 days"


def test_total_under_smallest_band_upper_bound():
    result = compute(draft(analysis=0, build=0, testing=0, uat=0), settings(change_mgmt=0.1, coord_pct=0))
    assert result.total_days == 0.1
    assert result.cost_eur == 170


def test_total_at_or_above_largest_band_requires_manual_costing():
    result = compute(draft(analysis=5, build=15, testing=5, uat=2), settings(change_mgmt=0.5, coord_pct=0.10))
    assert result.total_days >= 20
    assert result.cost_status.value == "ManualCostingRequired"
    assert result.cost_eur is None
    assert result.cost_band_label is None


def test_zero_effort_falls_in_smallest_band():
    result = compute(draft(0, 0, 0, 0), settings(change_mgmt=0, coord_pct=0))
    assert result.total_days == 0
    assert result.cost_eur == 170


def test_bands_matched_regardless_of_input_order():
    unordered = [BANDS[3], BANDS[0], BANDS[5], BANDS[1], BANDS[4], BANDS[2]]
    result = compute(
        draft(analysis=0.1, build=1, testing=0.5, uat=0.25),
        EffortSettings(change_management_default_days=0.5, enhancement_coordination_percent=0.10, cost_bands=unordered),
    )
    assert result.cost_band_label == "2-5 days"
