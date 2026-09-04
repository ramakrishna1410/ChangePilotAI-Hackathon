from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import EffortSettingsHistory, EffortSettingsRow, get_session, load_effort_settings
from app.models import EffortSettings, EffortSettingsHistoryEntry

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
    previous = load_effort_settings(session)

    row.change_management_default_days = payload.change_management_default_days
    row.enhancement_coordination_percent = payload.enhancement_coordination_percent
    row.cost_bands = [b.model_dump() for b in sorted(payload.cost_bands, key=lambda b: b.upper_bound_days)]
    session.commit()
    session.refresh(row)
    new = load_effort_settings(session)

    session.add(
        EffortSettingsHistory(
            timestamp=datetime.utcnow(),
            changed_by=payload.changed_by,
            previous=previous.model_dump(mode="json", exclude={"changed_by"}),
            new=new.model_dump(mode="json", exclude={"changed_by"}),
        )
    )
    session.commit()
    return new


@router.get("/effort/history", response_model=list[EffortSettingsHistoryEntry])
def get_effort_settings_history(session: Session = Depends(_session)):
    rows = session.query(EffortSettingsHistory).order_by(EffortSettingsHistory.timestamp.desc()).all()
    return [
        EffortSettingsHistoryEntry(
            id=r.id, timestamp=r.timestamp, changed_by=r.changed_by, previous=r.previous, new=r.new
        )
        for r in rows
    ]
