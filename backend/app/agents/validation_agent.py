"""Validation Agent/Stage (§3.7, §4): deterministically checks that every
material finding cites supporting evidence, and flags anything that doesn't
as "Needs validation" rather than presenting it as fact — this runs as a
plain check (not another LLM call) so it can't itself hallucinate evidence."""
from app.models import Dependency, ImpactItem, RiskItem, TestScenario, ValidationFinding


def run(
    impacted_items: list[ImpactItem],
    dependencies: list[Dependency],
    risks: list[RiskItem],
    test_scenarios: list[TestScenario],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for item in impacted_items:
        if not item.evidence_refs:
            findings.append(
                ValidationFinding(
                    item_description=f"Impact: {item.type} {item.name} ({item.impact_level})",
                    issue="No evidence cited for this impact finding — requires SME validation.",
                )
            )
        if item.confidence < 0.4:
            findings.append(
                ValidationFinding(
                    item_description=f"Impact: {item.type} {item.name}",
                    issue=f"Low model confidence ({item.confidence:.2f}) — verify before use.",
                )
            )

    for dep in dependencies:
        if dep.evidence_ref is None:
            findings.append(
                ValidationFinding(
                    item_description=f"Dependency: {dep.source} -> {dep.target} ({dep.dependency_type})",
                    issue="No evidence cited for this dependency.",
                )
            )

    for risk in risks:
        if risk.evidence_ref is None and risk.severity in ("High", "Medium"):
            findings.append(
                ValidationFinding(
                    item_description=f"Risk: {risk.risk} ({risk.severity})",
                    issue="No evidence cited for a Medium/High severity risk.",
                )
            )

    for scenario in test_scenarios:
        if scenario.evidence_ref is None and scenario.priority in ("High", "Critical"):
            findings.append(
                ValidationFinding(
                    item_description=f"Test scenario: {scenario.scenario}",
                    issue="No evidence cited for a High/Critical priority scenario.",
                )
            )

    return findings
