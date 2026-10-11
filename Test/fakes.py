"""Canned pipeline outputs and a fake LLM shared by the graph-level tests."""

from Models.bug_model import (
    BugReport,
    InvestigationPlan,
    InvestigationTask,
    WorkerResult,
    TriageResult,
    EvaluationResult,
)

BUG_REPORT = BugReport(
    title="Login failure",
    description="Users receive HTTP 500 after resetting their password.",
    environment="production",
    service="Authentication API",
)

PLAN = InvestigationPlan(tasks=[
    InvestigationTask(
        task_ID="task_1",
        investigation_type="severity",
        objective="Determine the severity of the issue.",
        relevant_context=["Users cannot log in in production."],
        expected_output="Severity assessment",
    ),
    InvestigationTask(
        task_ID="task_2",
        investigation_type="root_cause",
        objective="Investigate the likely root cause.",
        relevant_context=["HTTP 500 after password reset."],
        expected_output="Root cause assessment",
    ),
])

WORKER_RESULT = WorkerResult(
    task_ID="task_1",
    investigation_type="severity",
    conclusion="Login is broken for users who reset their password.",
    evidence=["HTTP 500 after password reset."],
    confidence=0.8,
    limitations=[],
)

TRIAGE = TriageResult(
    severity="High",
    affected_component=["Authentication API"],
    probable_causes=["Unhandled error in the post-reset login flow."],
    duplicate_candidates=[],
    recommended_team="Authentication Team",
    recommended_actions=["Inspect the post-reset login flow."],
    confidence=0.8,
    evidence_summary=["HTTP 500 after password reset."],
    uncertainty="Exact failing code path not confirmed.",
)


def evaluation(passed: bool) -> EvaluationResult:
    return EvaluationResult(
        passed=passed,
        overall_score=0.9 if passed else 0.4,
        groundedness_score=0.9,
        completeness_score=0.9,
        consistency_score=0.9,
        severity_policy_score=0.9,
        actionability_score=0.9,
        identified_issues=[] if passed else ["Severity is not justified."],
        revision_feedback=None if passed else "Justify the severity.",
    )


class FakeLLM:
    """Stands in for ChatOpenAI.

    `evaluations` is the sequence of pass/fail verdicts the evaluator
    returns (it passes once the sequence runs out). Every structured call
    is recorded in `calls` as (schema, messages).
    """

    def __init__(self, evaluations=(True,)):
        self._verdicts = iter(evaluations)
        self.calls = []

    def with_structured_output(self, schema):
        return _StructuredFake(self, schema)

    def prompts_for(self, schema) -> list[str]:
        """The human-message text of every call made for `schema`."""
        return [
            dict(messages)["human"]
            for called_schema, messages in self.calls
            if called_schema is schema
        ]

    def respond(self, schema):
        if schema is EvaluationResult:
            return evaluation(next(self._verdicts, True))
        return {
            BugReport: BUG_REPORT,
            InvestigationPlan: PLAN,
            WorkerResult: WORKER_RESULT,
            TriageResult: TRIAGE,
        }[schema]


class _StructuredFake:
    def __init__(self, fake_llm, schema):
        self._fake_llm = fake_llm
        self._schema = schema

    def invoke(self, messages):
        self._fake_llm.calls.append((self._schema, messages))
        return self._fake_llm.respond(self._schema)
