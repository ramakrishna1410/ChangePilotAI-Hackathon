"""Tech Lead review decisions (§3.5, §3.6, §9 Approval screen).

Accept -> locks the run and marks the change request Approved.
Accept with edits -> requires an edited_result payload; the original AI
  result is preserved in ai_original_result for audit, the run's result is
  replaced with the edited version, then locked the same as Accept.
Reject -> marks the run/CR Rejected; unlike Accept, this does not block
  further action — the Tech Lead can start a fresh analysis run on the CR.
A run can only be decided once: once review_status leaves "NotReviewed" the
run is locked and further feedback attempts are rejected with 409.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import AnalysisRun, ChangeRequest, Feedback, get_session
from app.models import AnalysisRunOut, FeedbackCreate, FeedbackDecision, FeedbackOut

router = APIRouter(prefix="/analysis-runs", tags=["feedback"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


_DECISION_TO_REVIEW_STATUS = {
    FeedbackDecision.accepted: "Approved",
    FeedbackDecision.edited: "ApprovedEdited",
    FeedbackDecision.rejected: "Rejected",
}

_DECISION_TO_CR_STATUS = {
    FeedbackDecision.accepted: "Approved",
    FeedbackDecision.edited: "Approved",
    FeedbackDecision.rejected: "Rejected",
}


@router.post("/{run_id}/feedback", response_model=AnalysisRunOut)
def submit_feedback(run_id: int, payload: FeedbackCreate, session: Session = Depends(_session)):
    run = session.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    if run.status != "Completed":
        raise HTTPException(409, "Only a completed analysis run can be reviewed")
    if run.review_status != "NotReviewed":
        raise HTTPException(
            409,
            f"This run was already reviewed (status: {run.review_status}). "
            "Start a new analysis run to make further changes.",
        )
    if payload.decision == FeedbackDecision.edited and payload.edited_result is None:
        raise HTTPException(422, "edited_result is required when decision is 'Edited'")

    cr = session.get(ChangeRequest, run.change_request_id)

    if payload.decision == FeedbackDecision.edited:
        run.ai_original_result = run.result
        run.result = payload.edited_result.model_dump(mode="json")

    run.review_status = _DECISION_TO_REVIEW_STATUS[payload.decision]
    run.decided_by = payload.user
    run.decided_at = datetime.utcnow()
    run.decision_comment = payload.comment
    if cr:
        cr.status = _DECISION_TO_CR_STATUS[payload.decision]

    session.add(
        Feedback(
            run_id=run_id,
            user=payload.user,
            decision=payload.decision.value,
            comment=payload.comment,
        )
    )
    session.commit()
    session.refresh(run)
    return run


@router.get("/{run_id}/feedback", response_model=list[FeedbackOut])
def list_feedback(run_id: int, session: Session = Depends(_session)):
    return session.query(Feedback).filter(Feedback.run_id == run_id).order_by(Feedback.timestamp).all()
