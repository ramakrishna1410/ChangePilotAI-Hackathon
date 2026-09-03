"""Orchestrator Agent (§4, §5.1): understands the request and drives the
analysis workflow — requirement extraction -> RAG/impact -> dependencies ->
risk/effort -> regression scenarios -> evidence validation -> structured
result. Logical agents/tools within one orchestrated workflow, per §4's
hackathon-MVP note.
"""
from app.agents import (
    dependency_agent,
    impact_agent,
    requirement_agent,
    risk_effort_agent,
    test_agent,
    validation_agent,
)
from app.models import AnalysisResult


def run_analysis(application: str, summary: str, description: str) -> AnalysisResult:
    requirement = requirement_agent.run(application, summary, description)

    impacted_items, evidence_chunks = impact_agent.run(
        requirement.objective, requirement.scope, application
    )

    dependencies = dependency_agent.run(impacted_items, evidence_chunks)

    risks, effort_estimate = risk_effort_agent.run(impacted_items, dependencies, evidence_chunks)

    test_scenarios = test_agent.run(
        requirement.objective, requirement.acceptance_criteria, impacted_items, evidence_chunks
    )

    needs_validation = validation_agent.run(impacted_items, dependencies, risks, test_scenarios)

    return AnalysisResult(
        requirement=requirement,
        impacted_items=impacted_items,
        dependencies=dependencies,
        risks=risks,
        effort_estimate=effort_estimate,
        test_scenarios=test_scenarios,
        needs_validation=needs_validation,
    )
