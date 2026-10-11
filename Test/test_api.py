from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from graph.graph import graph
from Models.bug_model import EvaluationResult, InvestigationPlan, WorkerResult
from fakes import FakeLLM

# End-to-end tests of the API running the real compiled graph, with the
# LLM replaced by a fake that returns a canned object per output schema.


@pytest.fixture
def client():
    return TestClient(app)


def _start_triage(client, evaluations=(True,)):
    with patch("Models.Nodes.llm", FakeLLM(evaluations)):
        response = client.post(
            "/bug-triage",
            json={"bug_report": "Users get HTTP 500 after password reset."},
        )
    assert response.status_code == 200, response.text
    return response.json()


def _review(client, thread_id, decision, feedback=None, fake_llm=None):
    with patch("Models.Nodes.llm", fake_llm or FakeLLM()):
        return client.post(
            "/bug-review",
            json={
                "thread_id": thread_id,
                "decision": decision,
                "feedback": feedback,
            },
        )


def test_triage_pauses_for_human_review(client):
    body = _start_triage(client)

    assert body["status"] == "awaiting_review"
    assert body["revision_count"] == 0
    assert body["review_round"] == 1
    assert body["review_history"] == []
    assert body["bug_report"]["title"] == "Login failure"
    assert body["triage_result"]["severity"] == "High"
    assert body["evaluation"]["passed"] is True


def test_failed_evaluation_triggers_automatic_revision(client):
    body = _start_triage(client, evaluations=(False, True))

    assert body["status"] == "awaiting_review"
    assert body["revision_count"] == 1


def test_approve_completes_triage(client):
    thread_id = _start_triage(client)["thread_id"]

    response = _review(client, thread_id, "approve")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["human_decision"]["decision"] == "approve"
    assert body["bug_report"]["title"] == "Login failure"


def test_reject_marks_triage_rejected(client):
    thread_id = _start_triage(client)["thread_id"]

    response = _review(client, thread_id, "reject", feedback="Not a bug.")

    body = response.json()
    assert body["status"] == "rejected"
    assert body["human_decision"]["feedback"] == "Not a bug."


def test_revise_reinvestigates_with_feedback_and_returns_to_review(client):
    thread_id = _start_triage(client, evaluations=(False, True))["thread_id"]
    fake = FakeLLM()

    response = _review(client, thread_id, "revise", "Login is fully blocked.", fake)

    body = response.json()
    assert body["status"] == "awaiting_review"
    assert body["review_round"] == 2
    assert body["revision_count"] == 0
    assert [d["decision"] for d in body["review_history"]] == ["revise"]

    # The feedback reached the planner, every worker, and the evaluator.
    assert "Login is fully blocked." in fake.prompts_for(InvestigationPlan)[0]
    worker_prompts = fake.prompts_for(WorkerResult)
    assert len(worker_prompts) == 2
    assert all("Login is fully blocked." in p for p in worker_prompts)
    assert "Login is fully blocked." in fake.prompts_for(EvaluationResult)[0]

    # Old worker results were replaced, not accumulated.
    config = {"configurable": {"thread_id": thread_id}}
    assert len(graph.get_state(config).values["worker_results"]) == 2

    response = _review(client, thread_id, "approve")
    body = response.json()
    assert body["status"] == "completed"
    assert [d["decision"] for d in body["review_history"]] == ["revise", "approve"]


def test_feedback_from_every_round_is_kept(client):
    thread_id = _start_triage(client)["thread_id"]
    _review(client, thread_id, "revise", "First note.")
    fake = FakeLLM()

    _review(client, thread_id, "revise", "Second note.", fake)

    plan_prompt = fake.prompts_for(InvestigationPlan)[0]
    assert "First note." in plan_prompt
    assert "Second note." in plan_prompt


def test_revise_without_feedback_returns_422(client):
    thread_id = _start_triage(client)["thread_id"]

    response = _review(client, thread_id, "revise", feedback="   ")

    assert response.status_code == 422


def test_get_triage_returns_saved_thread(client):
    started = _start_triage(client)

    response = client.get(f"/bug-triage/{started['thread_id']}")

    assert response.status_code == 200
    assert response.json() == started


def test_get_unknown_triage_returns_404(client):
    assert client.get("/bug-triage/does-not-exist").status_code == 404


def test_review_unknown_thread_returns_404(client):
    response = _review(client, "does-not-exist", "approve")

    assert response.status_code == 404


def test_review_finished_thread_returns_409(client):
    thread_id = _start_triage(client)["thread_id"]
    _review(client, thread_id, "approve")

    response = _review(client, thread_id, "approve")

    assert response.status_code == 409


def test_empty_bug_report_returns_422(client):
    response = client.post("/bug-triage", json={"bug_report": "   "})

    assert response.status_code == 422
