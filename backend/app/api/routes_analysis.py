from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_analysis
from app.config import CHAT_MODEL
from app.db import AnalysisRun, ChangeRequest, get_session, load_effort_settings
from app.models import AnalysisRunOut

router = APIRouter(prefix="/analysis-runs", tags=["analysis-runs"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/{cr_id}", response_model=AnalysisRunOut)
def start_analysis(cr_id: int, session: Session = Depends(_session)):
    cr = session.get(ChangeRequest, cr_id)
    if not cr:
        raise HTTPException(404, "Change request not found")

    run = AnalysisRun(
        change_request_id=cr.id,
        model=CHAT_MODEL,
        status="Running",
        started_at=datetime.utcnow(),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        effort_settings = load_effort_settings(session)
        result = run_analysis(cr.application, cr.summary, cr.description, effort_settings)
        run.result = result.model_dump(mode="json")
        run.status = "Completed"
        run.completed_at = datetime.utcnow()
        cr.status = "Analyzed"
    except Exception as exc:  # analysis failures shouldn't 500 the API — surface as a failed run
        run.status = "Failed"
        run.error = str(exc)
        run.completed_at = datetime.utcnow()

    session.commit()
    session.refresh(run)
    return run


@router.get("/{run_id}", response_model=AnalysisRunOut)
def get_analysis(run_id: int, session: Session = Depends(_session)):
    run = session.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(404, "Analysis run not found")
    return run


@router.get("", response_model=list[AnalysisRunOut])
def list_analysis_runs(change_request_id: int | None = None, session: Session = Depends(_session)):
    query = session.query(AnalysisRun)
    if change_request_id is not None:
        query = query.filter(AnalysisRun.change_request_id == change_request_id)
    return query.order_by(AnalysisRun.started_at.desc()).all()
