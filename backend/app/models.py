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


class EffortEstimate(BaseModel):
    analysis_hours: float
    complexity: str  # Low | Medium | High
    confidence: float = Field(ge=0, le=1)
    rationale: str


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

    class Config:
        from_attributes = True


# --- Feedback -----------------------------------------------------------------

class FeedbackCreate(BaseModel):
    user: str
    decision: FeedbackDecision
    comment: Optional[str] = None


class FeedbackOut(FeedbackCreate):
    id: int
    run_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
