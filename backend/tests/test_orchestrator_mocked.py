"""Runs the real orchestrator end-to-end with app.agents.llm.call_structured
monkeypatched to return fixed, canned JSON per agent — this verifies the
actual pipeline wiring (data flowing correctly between agents, evidence-ref
filtering, effort_calculator integration) without needing a real OpenAI key.
"""
from app.agents import orchestrator
from app.models import CostBand, EffortSettings

FAKE_REQUIREMENT = {
    "objective": "Auto-approve orders below a threshold",
    "scope": "OrderApprovalService",
    "constraints": [],
    "acceptance_criteria": ["Orders under threshold skip manual approval"],
    "affected_application": "SanofiOrders",
}


def _settings():
    return EffortSettings(
        change_management_default_days=0.5,
        enhancement_coordination_percent=0.10,
        cost_bands=[
            CostBand(label="< 1 day", upper_bound_days=1, cost_eur=170),
            CostBand(label="1-2 days", upper_bound_days=2, cost_eur=273),
            CostBand(label="2-5 days", upper_bound_days=5, cost_eur=505),
        ],
    )


def test_orchestrator_wires_agents_together(monkeypatch):
    calls = []

    def fake_call_structured(system_prompt, user_prompt):
        calls.append(system_prompt)
        if "Requirement Agent" in system_prompt:
            return FAKE_REQUIREMENT
        if "Impact Agent" in system_prompt:
            # include a chunk_id that was NOT retrieved, to prove it gets filtered out
            return {
                "impacted_items": [
                    {
                        "type": "Service",
                        "name": "OrderApprovalService",
                        "path": "Services/OrderApprovalService.cs",
                        "impact_level": "Direct",
                        "reason": "Contains the approval rule",
                        "evidence_refs": [{"chunk_id": "not-a-real-chunk-id", "source_path": "x", "symbol": "y"}],
                        "confidence": 0.9,
                    }
                ]
            }
        if "Dependency Agent" in system_prompt:
            return {"dependencies": []}
        if "Risk & Effort Agent" in system_prompt:
            return {
                "risks": [],
                "effort_estimate": {
                    "analysis_design_days": 0.1,
                    "build_days": 1.0,
                    "testing_sit_days": 0.5,
                    "uat_support_days": 0.25,
                    "complexity": "Medium",
                    "confidence": 0.7,
                    "rationale": "small change",
                },
            }
        if "Test Recommendation Agent" in system_prompt:
            return {"test_scenarios": []}
        raise AssertionError(f"Unexpected agent prompt: {system_prompt[:60]}")

    # Each agent module does `from app.agents.llm import call_structured`, binding its
    # own local name — patching app.agents.llm.call_structured alone wouldn't affect
    # those already-bound references, so each agent module's copy must be patched too.
    for module in ("requirement_agent", "impact_agent", "dependency_agent", "risk_effort_agent", "test_agent"):
        monkeypatch.setattr(f"app.agents.{module}.call_structured", fake_call_structured)

    result = orchestrator.run_analysis("SanofiOrders", "summary", "description", _settings())

    assert result.requirement.objective == FAKE_REQUIREMENT["objective"]
    assert len(result.impacted_items) == 1
    # evidence ref pointing at a non-retrieved chunk must be stripped by impact_agent
    assert result.impacted_items[0].evidence_refs == []
    # effort_calculator must have applied the deterministic overhead + cost lookup
    assert result.effort_estimate.change_management_days == 0.5
    assert result.effort_estimate.enhancement_coordination_days == 0.19  # 10% of 1.85, rounded to 2dp
    assert result.effort_estimate.cost_status.value == "Computed"
    # validation agent should flag the impact item since its only evidence was stripped
    assert len(result.needs_validation) == 1
