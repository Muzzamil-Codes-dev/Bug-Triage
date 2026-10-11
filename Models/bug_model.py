from pydantic import BaseModel, Field
from typing import Optional, Literal


class BugReport(BaseModel):
    title: str
    description: str

    environment: Optional[str] = None
    service: Optional[str] = None
    logs: Optional[list[str]] = None
    stack_trace: Optional[str] = None
    reproduction_steps: Optional[list[str]] = None
    recent_changes: Optional[list[str]] = None
    user_impact: Optional[str] = None
    other_supplied_evidence: Optional[str] = None


class InvestigationTask(BaseModel):
    task_ID: str
    investigation_type: Literal[
        "severity",
        "component",
        "duplicate",
        "root_cause",
    ]
    objective: str
    relevant_context: list[str]
    expected_output: str


class InvestigationPlan(BaseModel):
    tasks: list[InvestigationTask]


class WorkerResult(BaseModel):
    task_ID: str
    investigation_type: Literal[
        "severity",
        "component",
        "duplicate",
        "root_cause",
    ]
    conclusion: str
    evidence: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str]


class TriageResult(BaseModel):
    severity: Literal[
        "Critical",
        "High",
        "Medium",
        "Low",
    ]
    affected_component: list[str]
    probable_causes: list[str]
    duplicate_candidates: list[str]
    recommended_team: str
    recommended_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_summary: list[str]
    uncertainty: str


class EvaluationResult(BaseModel):
    passed: bool

    overall_score: float = Field(ge=0.0, le=1.0)
    groundedness_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    severity_policy_score: float = Field(ge=0.0, le=1.0)
    actionability_score: float = Field(ge=0.0, le=1.0)

    identified_issues: list[str]
    revision_feedback: Optional[str] = None


class HumanDecision(BaseModel):
    decision: Literal["approve", "revise", "reject"]
    feedback: Optional[str] = None
    corrections: Optional[str] = None