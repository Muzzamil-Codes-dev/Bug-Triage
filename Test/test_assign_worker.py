import pytest

from Models.Nodes import assign_worker
from Models.bug_model import InvestigationTask,BugReport,InvestigationPlan

def test_assign_worker_sends_one_worker_per_task():
    bug_report = BugReport(
        title="Login failure",
        description="Users cannot log in after resetting their password.",
    )

    task_1 = InvestigationTask(
    task_ID="task_1",
    investigation_type="severity",
    objective="Determine the severity of the issue.",
    relevant_context=["Multiple users cannot log in."],
    expected_output="Severity assessment",
)

    task_2 = InvestigationTask(
        task_ID="task_2",
        investigation_type="root_cause",
        objective="Investigate the likely root cause.",
        relevant_context=["HTTP 500 occurs after password reset."],
        expected_output="Root cause assessment",
    )
    plan = InvestigationPlan(
        tasks = [task_1,task_2]
    )
    state = {
        "bug_report":bug_report,
        "investigation_plan": plan
    }
    results = assign_worker(state)

    # Assert
    #Check number of sends = 2
    assert len(results) == 2
    assert results[0].node == "worker"
    assert results[0].arg["task"] == task_1
    assert results[0].arg["bug_report"] == bug_report
    assert results[1].arg["task"] == task_2


def test_assign_worker_rejects_empty_plan():
    state = {
        "bug_report": BugReport(title="t", description="d"),
        "investigation_plan": InvestigationPlan(tasks=[]),
    }

    with pytest.raises(ValueError):
        assign_worker(state)
