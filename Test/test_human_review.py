from unittest.mock import patch

import pytest
from langgraph.graph import END
from langgraph.types import Overwrite

from Models.Nodes import human_review


STATE = {
    "triage_result": "triage",
    "evaluation": "evaluation",
    "review_round": 1,
}


def _review(response):
    with patch("Models.Nodes.interrupt", return_value=response):
        return human_review(STATE)


@pytest.mark.parametrize("decision", ["approve", "reject", "  APPROVE "])
def test_approve_or_reject_ends_the_run(decision):
    command = _review({"decision": decision, "feedback": "Note."})

    assert command.goto == END
    recorded = command.update["human_decision"]
    assert recorded.decision == decision.lower().strip()
    assert recorded.feedback == "Note."
    assert command.update["review_history"] == [recorded]


def test_revise_restarts_investigation_in_a_new_round():
    command = _review({"decision": "revise", "feedback": "  Wrong severity. "})

    assert command.goto == "orchestrator"
    assert command.update["human_decision"].feedback == "Wrong severity."
    assert command.update["review_round"] == 2
    assert command.update["revision_count"] == 0
    assert command.update["worker_results"] == Overwrite([])


def test_revise_requires_feedback():
    with pytest.raises(ValueError):
        _review({"decision": "revise", "feedback": "  "})


def test_human_review_rejects_unknown_decision():
    with pytest.raises(ValueError):
        _review({"decision": "maybe"})
