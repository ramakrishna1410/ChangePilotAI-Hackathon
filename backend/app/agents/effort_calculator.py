"""Deterministic effort/cost calculator — NOT an LLM call. Takes the AI's
draft SDLC effort estimate (§3.5) and combines it with the configurable
overhead defaults and cost bands from EffortSettings to produce the final
EffortEstimate, including the EUR cost. Keeping this arithmetic out of the
LLM means the cost figure is always exactly reproducible from the settings
and the AI's day estimates — it can't be hallucinated.
"""
from app.models import CostStatus, EffortEstimate, EffortEstimateDraft, EffortSettings


def compute(draft: EffortEstimateDraft, settings: EffortSettings) -> EffortEstimate:
    total_days = (
        draft.analysis_design_days
        + draft.build_days
        + draft.testing_sit_days
        + draft.uat_support_days
        + settings.change_management_default_days
        + settings.enhancement_coordination_default_days
    )

    cost_eur: float | None = None
    cost_band_label: str | None = None
    cost_status = CostStatus.manual_costing_required

    for band in sorted(settings.cost_bands, key=lambda b: b.upper_bound_days):
        if total_days < band.upper_bound_days:
            cost_eur = band.cost_eur
            cost_band_label = band.label
            cost_status = CostStatus.computed
            break

    return EffortEstimate(
        analysis_design_days=draft.analysis_design_days,
        build_days=draft.build_days,
        testing_sit_days=draft.testing_sit_days,
        uat_support_days=draft.uat_support_days,
        change_management_days=settings.change_management_default_days,
        enhancement_coordination_days=settings.enhancement_coordination_default_days,
        total_days=round(total_days, 2),
        complexity=draft.complexity,
        confidence=draft.confidence,
        rationale=draft.rationale,
        cost_status=cost_status,
        cost_eur=cost_eur,
        cost_band_label=cost_band_label,
    )
