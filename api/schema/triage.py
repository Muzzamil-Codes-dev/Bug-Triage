from pydantic import BaseModel, model_validator
from typing import Literal
from Models.bug_model import (
    BugReport,
    TriageResult,
    EvaluationResult,
    HumanDecision,
)

TriageStatus = Literal["awaiting_review", "completed", "rejected"]


class BugTriageRequest(BaseModel):
    bug_report : str

class ReviewTriageRequest(BaseModel):
    thread_id : str
    decision : Literal["approve","revise","reject"]
    feedback : str | None = None

    @model_validator(mode="after")
    def revise_needs_feedback(self):
        if self.decision == "revise" and not (self.feedback or "").strip():
            raise ValueError("Feedback is required to request a revision.")
        return self

class TriageThreadResponse(BaseModel):
    """Current state of a triage thread; returned by every endpoint."""

    thread_id : str
    status : TriageStatus

    bug_report : BugReport
    triage_result : TriageResult
    evaluation : EvaluationResult

    # Automatic revisions in the current review round.
    revision_count : int
    # Starts at 1; every human "revise" decision starts a new round.
    review_round : int

    human_decision : HumanDecision | None = None
    review_history : list[HumanDecision]
