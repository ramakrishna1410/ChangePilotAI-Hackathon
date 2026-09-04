"""Pydantic schemas mirroring the data model in Section 7 of the design doc.

These are used both as API request/response shapes and as the structured
JSON contracts passed between agents in the orchestrator (Phase 5 of
Section 10: "Define structured JSON output contracts between agents/tools").
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class ImpactLevel(str, Enum):
    direct = "Direct"
    indirect = "Indirect"
    potentially_related = "Potentially Related"


class Severity(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class ScenarioType(str, Enum):
    positive = "Positive"
    negative = "Negative"
    boundary = "Boundary"
    integration = "Integration"


class RunStatus(str, Enum):
    pending = "Pending"
    running = "Running"
    completed = "Completed"
    failed = "Failed"


class FeedbackDecision(str, Enum):
    accepted = "Accepted"
    edited = "Edited"
    rejected = "Rejected"


class ReviewStatus(str, Enum):
    not_reviewed = "NotReviewed"
    approved = "Approved"
    approved_edited = "ApprovedEdited"
    rejected = "Rejected"


class CostStatus(str, Enum):
    computed = "Computed"
    manual_costing_required = "ManualCostingRequired"


# --- Change Request intake -------------------------------------------------

class ChangeRequestCreate(BaseModel):
    service_now_id: Optional[str] = Field(None, description="ServiceNow CR id, if known")
    application: str = Field(..., description="Target application, e.g. SanofiOrders")
    summary: str
    description: str
    priority: Priority = Priority.medium


class ChangeRequestOut(ChangeRequestCreate):
    id: int
    status: str
    created_date: datetime

    class Config:
        from_attributes = True


# --- Requirement extraction (Requirement Agent) ----------------------------

class RequirementSummary(BaseModel):
    objective: str
    scope: str
    constraints: list[str] = []
    acceptance_criteria: list[str] = []
    affected_application: str


# --- Evidence ---------------------------------------------------------------

class EvidenceRef(BaseModel):
    chunk_id: str
    source_path: str
    symbol: Optional[str] = None  # class/method/SQL object name


# --- Impact analysis (Impact Agent) -----------------------------------------

class ImpactItem(BaseModel):
    type: str  # Controller | Service | Repository | Model | SqlObject | Config | Document
    name: str
    path: str
    impact_level: ImpactLevel
    reason: str
    evidence_refs: list[EvidenceRef] = []
    confidence: float = Field(ge=0, le=1)


# --- Dependency analysis (Dependency Agent) ---------------------------------

class Dependency(BaseModel):
    source: str
    target: str
    dependency_type: str  # calls | reads | writes | shares-table | shares-service
    evidence_ref: Optional[EvidenceRef] = None


# --- Risk & Effort (Risk & Effort Agent) ------------------------------------

class RiskItem(BaseModel):
    risk: str
    severity: Severity
    rationale: str
    evidence_ref: Optional[EvidenceRef] = None
    mitigation: str


class EffortEstimateDraft(BaseModel):
    """AI-estimated portion of the effort estimate, before the deterministic
    overhead defaults (Change Management, Enhancement/Coordination) and cost
    lookup are applied by app/agents/effort_calculator.py."""

    analysis_design_days: float = Field(ge=0)
    build_days: float = Field(ge=0)
    testing_sit_days: float = Field(ge=0)
    uat_support_days: float = Field(ge=0)
    complexity: str
    confidence: float = Field(ge=0, le=1)
    rationale: str


class EffortEstimate(BaseModel):
    """All figures in days (8 hours = 1 day). analysis_design_days through
    uat_support_days are AI-estimated; change_management_days and
    enhancement_coordination_days are deterministic defaults pulled from
    EffortSettings (configurable on the Settings page), not model output."""

    analysis_design_days: float = Field(ge=0)
    build_days: float = Field(ge=0)  # Build (Dev & Unit Testing)
    testing_sit_days: float = Field(ge=0)
    uat_support_days: float = Field(ge=0)
    change_management_days: float = Field(ge=0)  # Change Management (SNOW) — default 0.50
    enhancement_coordination_days: float = Field(ge=0)  # Enhancement/Project Coordination — default 0.20
    total_days: float = Field(ge=0)
    complexity: str  # Low | Medium | High
    confidence: float = Field(ge=0, le=1)
    rationale: str
    cost_status: CostStatus
    cost_eur: Optional[float] = None
    cost_band_label: Optional[str] = None


# --- Regression / test recommendation (Test Agent) --------------------------

class TestScenario(BaseModel):
    scenario: str
    type: ScenarioType
    priority: Priority
    impacted_area: str
    evidence_ref: Optional[EvidenceRef] = None


# --- Validation (Validation Agent) ------------------------------------------

class ValidationFinding(BaseModel):
    item_description: str
    issue: str  # e.g. "no evidence cited", "contradicts retrieved chunk X"


# --- Full analysis result ----------------------------------------------------

class AnalysisResult(BaseModel):
    requirement: RequirementSummary
    impacted_items: list[ImpactItem]
    dependencies: list[Dependency]
    risks: list[RiskItem]
    effort_estimate: EffortEstimate
    test_scenarios: list[TestScenario]
    needs_validation: list[ValidationFinding] = []


class AnalysisRunOut(BaseModel):
    id: int
    change_request_id: int
    model: str
    status: RunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[AnalysisResult] = None
    ai_original_result: Optional[AnalysisResult] = None
    review_status: ReviewStatus
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_comment: Optional[str] = None

    class Config:
        from_attributes = True


# --- Feedback / review decision -----------------------------------------------

class FeedbackCreate(BaseModel):
    user: str
    decision: FeedbackDecision
    comment: Optional[str] = None
    # Required when decision == "Edited": the Tech Lead's edited findings,
    # replacing the AI-generated result on this run (original is preserved
    # in ai_original_result for audit).
    edited_result: Optional[AnalysisResult] = None


class FeedbackOut(BaseModel):
    id: int
    run_id: int
    user: str
    decision: FeedbackDecision
    comment: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Effort/cost settings (Settings page) --------------------------------------

class CostBand(BaseModel):
    """A row in the cost lookup table: if total_days < upper_bound_days, this
    band's cost_eur applies (first match wins, bands must be given in
    ascending upper_bound_days order)."""

    label: str
    upper_bound_days: float = Field(gt=0)
    cost_eur: float = Field(ge=0)


class EffortRevisionRequest(BaseModel):
    """Body for POST /analysis-runs/{run_id}/re-estimate-effort: the Tech
    Lead's in-progress edits, sent to get an AI-revised effort estimate
    before they save (they can still hand-tune the result afterward)."""

    requirement: RequirementSummary
    impacted_items: list[ImpactItem]
    comment: Optional[str] = None


class EffortSettings(BaseModel):
    change_management_default_days: float = Field(ge=0, default=0.50)
    # Fraction (0-1), not a flat day count: Enhancement/Project Coordination
    # days = enhancement_coordination_percent * (analysis_design_days +
    # build_days + testing_sit_days + uat_support_days). Default 0.10 = 10%.
    enhancement_coordination_percent: float = Field(ge=0, le=1, default=0.10)
    cost_bands: list[CostBand]
    # Free-text identity of whoever is saving this change (no auth system
    # yet — see README) — recorded in the audit history, not persisted here.
    changed_by: Optional[str] = None


class EffortSettingsHistoryEntry(BaseModel):
    id: int
    timestamp: datetime
    changed_by: Optional[str] = None
    previous: EffortSettings
    new: EffortSettings
