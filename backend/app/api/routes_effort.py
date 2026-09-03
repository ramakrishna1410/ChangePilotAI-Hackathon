"""AI-assisted effort re-estimation for the Tech Lead's "Accept with edits"
flow: given their in-progress edits to the requirement and impact levels
(plus an optional comment), re-runs only the Risk & Effort Agent — not the
full pipeline — against fresh evidence for the edited requirement, and
returns a revised EffortEstimate whose rationale explains what changed.
The Tech Lead can still hand-edit the numbers afterward before saving.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents import effort_calculator, risk_effort_agent
from app.db import AnalysisRun, get_session, load_effort_settings
from app.models import Dependency, EffortEstimate, EffortRevisionRequest
from app.rag.retriever import retrieve

router = APIRouter(prefix="/analysis-runs", tags=["effort"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/{run_id}/re-estimate-effort", response_model=EffortEstimate)
def re_estimate_effort(run_id: int, payload: EffortRevisionRequest, session: Session = Depends(_session)):
    run = session.get(AnalysisRun, run_id)
    if not run or not run.result:
        raise HTTPException(404, "Analysis run not found")
    if run.review_status != "NotReviewed":
        raise HTTPException(409, "This run was already reviewed — start a new analysis run to revise further")

    previous_effort = run.result.get("effort_estimate", {})
    dependencies = [Dependency.model_validate(d) for d in run.result.get("dependencies", [])]

    # Re-target retrieval at the Tech Lead's edited requirement text — not the original —
    # so a materially different requirement pulls in relevant evidence for the new text.
    evidence_chunks = retrieve(f"{payload.requirement.objective} {payload.requirement.scope}")

    revision_lines = [
        "TECH LEAD REVISION:",
        f"Previous effort estimate: analysis_design={previous_effort.get('analysis_design_days')}, "
        f"build={previous_effort.get('build_days')}, testing_sit={previous_effort.get('testing_sit_days')}, "
        f"uat_support={previous_effort.get('uat_support_days')} "
        f"(dev subtotal {sum(previous_effort.get(k, 0) for k in ('analysis_design_days', 'build_days', 'testing_sit_days', 'uat_support_days')):.2f} days)",
        f"Edited requirement objective: {payload.requirement.objective}",
        f"Edited requirement scope: {payload.requirement.scope}",
    ]
    if payload.comment:
        revision_lines.append(f"Tech Lead comment: {payload.comment}")
    revision_context = "\n".join(revision_lines)

    try:
        _risks, draft = risk_effort_agent.run(
            payload.impacted_items, dependencies, evidence_chunks, revision_context=revision_context
        )
    except Exception as exc:
        raise HTTPException(502, f"Re-estimation failed (check OPENAI_API_KEY / connectivity): {exc}")

    effort_settings = load_effort_settings(session)
    return effort_calculator.compute(draft, effort_settings)
