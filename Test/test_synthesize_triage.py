from unittest.mock import MagicMock, patch
from Models.Nodes import synthesize_triage
from Models.bug_model import BugReport, WorkerResult
from Models.Nodes import TriageResult

# Testing the LLM Node

def test_synthesize_triage_returns_synthesis():
    # Arrange
    expected_triage = TriageResult(
    severity="High",
    affected_component=["Authentication API"],
    probable_causes=[
        "The login flow is attempting to access user_id on a missing user object after a password reset."
    ],
    duplicate_candidates=[],
    recommended_team="Authentication Team",
    recommended_actions=[
        "Inspect the user lookup logic after password reset.",
        "Add a guard for missing user objects before accessing user_id.",
        "Add logging around the post-reset login flow.",
    ],
    confidence=0.85,
    evidence_summary=[
        "Users receive an HTTP 500 after resetting their password.",
        "The stack trace contains an AttributeError involving user_id.",
        "Multiple users are affected in production.",
    ],
    uncertainty="The exact code path causing the missing user object has not been confirmed."
)

    fake_structured_llm = MagicMock()

    fake_llm = MagicMock()
    fake_llm.with_structured_output.return_value = fake_structured_llm

    fake_structured_llm.invoke.return_value =  expected_triage
    bug_report = BugReport(
    title="Login failure",
    description="Users receive HTTP 500 after resetting their password.",
    environment="production",
    service="Authentication API",
)
    worker_result = WorkerResult(
    task_ID="task_1",
    investigation_type="root_cause",
    conclusion="The login flow is attempting to access user_id on a missing user object.",
    evidence=[
        "HTTP 500 occurs after password reset.",
        "AttributeError references user_id."
    ],
    confidence=0.8,
    limitations=[
        "The exact failing code path has not been confirmed."
    ],
)
    state = {
        "bug_report": bug_report,
        "worker_results": [worker_result],
    }

# RUN
    with patch("Models.Nodes.llm",fake_llm):
        result = synthesize_triage(state)

# Assert
    assert result["triage_result"] == expected_triage