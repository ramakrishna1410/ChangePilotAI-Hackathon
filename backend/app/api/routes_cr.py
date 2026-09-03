from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import ChangeRequest, get_session
from app.models import ChangeRequestCreate, ChangeRequestOut

router = APIRouter(prefix="/change-requests", tags=["change-requests"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("", response_model=ChangeRequestOut)
def create_change_request(payload: ChangeRequestCreate, session: Session = Depends(_session)):
    cr = ChangeRequest(
        service_now_id=payload.service_now_id,
        application=payload.application,
        summary=payload.summary,
        description=payload.description,
        priority=payload.priority.value,
        status="New",
    )
    session.add(cr)
    session.commit()
    session.refresh(cr)
    return cr


@router.get("", response_model=list[ChangeRequestOut])
def list_change_requests(session: Session = Depends(_session)):
    return session.query(ChangeRequest).order_by(ChangeRequest.created_date.desc()).all()


@router.get("/{cr_id}", response_model=ChangeRequestOut)
def get_change_request(cr_id: int, session: Session = Depends(_session)):
    cr = session.get(ChangeRequest, cr_id)
    if not cr:
        raise HTTPException(404, "Change request not found")
    return cr
