from typing import TypedDict, Annotated, NotRequired
import operator

from Models.bug_model import (
    BugReport,
    InvestigationPlan,
    InvestigationTask,
    WorkerResult,
    TriageResult,
    EvaluationResult,
    HumanDecision,
)


class BugTriageState(TypedDict):
    raw_bug: str

    bug_report: NotRequired[BugReport]
    investigation_plan: NotRequired[InvestigationPlan]

    worker_results: Annotated[
        list[WorkerResult],
        operator.add,
    ]

    triage_result: NotRequired[TriageResult]
    evaluation: NotRequired[EvaluationResult]

    # Automatic (evaluator-driven) revisions in the current review round.
    revision_count: NotRequired[int]

    # Starts at 1; every human "revise" decision starts a new round.
    review_round: NotRequired[int]

    human_decision: NotRequired[HumanDecision]
    review_history: Annotated[
        list[HumanDecision],
        operator.add,
    ]


class WorkerState(TypedDict):
    task: InvestigationTask
    bug_report: BugReport
    reviewer_feedback: list[str]
