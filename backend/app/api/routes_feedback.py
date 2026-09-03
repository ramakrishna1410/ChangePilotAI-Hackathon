from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import AnalysisRun, Feedback, get_session
from app.models import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/analysis-runs", tags=["feedback"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/{run_id}/feedback", response_model=FeedbackOut)
def submit_feedback(run_id: int, payload: FeedbackCreate, session: Session = Depends(_session)):
    run = session.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")

    feedback = Feedback(
        run_id=run_id,
        user=payload.user,
        decision=payload.decision.value,
        comment=payload.comment,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


@router.get("/{run_id}/feedback", response_model=list[FeedbackOut])
def list_feedback(run_id: int, session: Session = Depends(_session)):
    return session.query(Feedback).filter(Feedback.run_id == run_id).order_by(Feedback.timestamp).all()
