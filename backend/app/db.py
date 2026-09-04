"""SQLAlchemy persistence — SQLite for the MVP, swap DB_PATH for a SQL Server
connection string in production (§7 data model uses the same shapes)."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_now_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    application: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String(4000))
    priority: Mapped[str] = mapped_column(String(20), default="Medium")
    status: Mapped[str] = mapped_column(String(20), default="New")
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_request_id: Mapped[int] = mapped_column(ForeignKey("change_requests.id"))
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_original_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Review workflow: once review_status leaves "NotReviewed" the run is
    # locked (Approved/ApprovedEdited) or reopened for a fresh run (Rejected).
    review_status: Mapped[str] = mapped_column(String(20), default="NotReviewed")
    decided_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"))
    user: Mapped[str] = mapped_column(String(200))
    decision: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


DEFAULT_COST_BANDS = [
    {"label": "< 1 day", "upper_bound_days": 1, "cost_eur": 170},
    {"label": "1-2 days", "upper_bound_days": 2, "cost_eur": 273},
    {"label": "2-5 days", "upper_bound_days": 5, "cost_eur": 505},
    {"label": "5-10 days", "upper_bound_days": 10, "cost_eur": 1282},
    {"label": "10-15 days", "upper_bound_days": 15, "cost_eur": 3300},
    {"label": "15-20 days", "upper_bound_days": 20, "cost_eur": 4442},
]


class EffortSettingsRow(Base):
    """Single-row table (id is always 1) holding the configurable effort/cost
    settings edited on the Settings page."""

    __tablename__ = "effort_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    change_management_default_days: Mapped[float] = mapped_column(Float, default=0.50)
    # Fraction (0-1) of the AI-estimated dev-effort subtotal, not flat days — see EffortSettings.
    enhancement_coordination_percent: Mapped[float] = mapped_column(Float, default=0.10)
    cost_bands: Mapped[list] = mapped_column(JSON, default=lambda: DEFAULT_COST_BANDS)


class EffortSettingsHistory(Base):
    """Audit trail of every Settings-page save: who changed the cost bands /
    overhead defaults, when, and the full before/after snapshot."""

    __tablename__ = "effort_settings_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    changed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    previous: Mapped[dict] = mapped_column(JSON)
    new: Mapped[dict] = mapped_column(JSON)


def init_db() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.get(EffortSettingsRow, 1) is None:
            session.add(EffortSettingsRow(id=1))
            session.commit()


def load_effort_settings(session: Session):
    """Reads the singleton EffortSettingsRow and returns it as the
    app.models.EffortSettings pydantic shape used by the orchestrator."""
    from app.models import CostBand, EffortSettings  # local import avoids a module-load cycle

    row = session.get(EffortSettingsRow, 1)
    return EffortSettings(
        change_management_default_days=row.change_management_default_days,
        enhancement_coordination_percent=row.enhancement_coordination_percent,
        cost_bands=[CostBand.model_validate(b) for b in row.cost_bands],
    )


def get_session() -> Session:
    return SessionLocal()
