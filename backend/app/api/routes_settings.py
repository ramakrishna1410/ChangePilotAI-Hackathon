from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import EffortSettingsRow, get_session, load_effort_settings
from app.models import EffortSettings

router = APIRouter(prefix="/settings", tags=["settings"])


def _session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/effort", response_model=EffortSettings)
def get_effort_settings(session: Session = Depends(_session)):
    return load_effort_settings(session)


@router.put("/effort", response_model=EffortSettings)
def update_effort_settings(payload: EffortSettings, session: Session = Depends(_session)):
    row = session.get(EffortSettingsRow, 1)
    row.change_management_default_days = payload.change_management_default_days
    row.enhancement_coordination_percent = payload.enhancement_coordination_percent
    row.cost_bands = [b.model_dump() for b in sorted(payload.cost_bands, key=lambda b: b.upper_bound_days)]
    session.commit()
    session.refresh(row)
    return load_effort_settings(session)
