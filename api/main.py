from fastapi import FastAPI, HTTPException
from api.frontend import mount_frontend
from api.schema.triage import (
BugTriageRequest,ReviewTriageRequest,TriageThreadResponse )
from graph.graph import graph
from uuid import uuid4
from langgraph.types import Command

app = FastAPI(title="Bug Triage API")


def _thread_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }


def _thread_response(thread_id: str) -> TriageThreadResponse:
    snapshot = graph.get_state(_thread_config(thread_id))
    values = snapshot.values

    if not values:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown thread_id: {thread_id}",
        )
    if "triage_result" not in values:
        raise HTTPException(
            status_code=409,
            detail="This triage did not finish. Please submit it again.",
        )

    # A pending next node means the graph is paused at human_review.
    human_decision = values.get("human_decision")
    if snapshot.next:
        status = "awaiting_review"
    elif human_decision and human_decision.decision == "reject":
        status = "rejected"
    else:
        status = "completed"

    return TriageThreadResponse(
        thread_id=thread_id,
        status=status,
        bug_report=values["bug_report"],
        triage_result=values["triage_result"],
        evaluation=values["evaluation"],
        revision_count=values.get("revision_count", 0),
        review_round=values.get("review_round", 1),
        human_decision=human_decision,
        review_history=values.get("review_history", []),
    )


@app.post("/bug-triage",response_model = TriageThreadResponse)
def create_bug_triage(request: BugTriageRequest):
    bug = request.bug_report

    if not bug.strip():
        raise HTTPException(status_code=422, detail="Bug report is empty.")

    thread_id = str(uuid4())

    initial_state = {
        "raw_bug": bug,
        "worker_results": [],
        "revision_count": 0,
        "review_round": 1,
        "review_history": [],
    }
    graph.invoke(initial_state, config=_thread_config(thread_id))

    return _thread_response(thread_id)

@app.get("/bug-triage/{thread_id}",response_model=TriageThreadResponse)
def get_bug_triage(thread_id: str):
    return _thread_response(thread_id)

@app.post("/bug-review",response_model=TriageThreadResponse)
def review_request(request : ReviewTriageRequest):

    config = _thread_config(request.thread_id)

    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown thread_id: {request.thread_id}",
        )
    if not snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="This triage is not awaiting review.",
        )

    human_response = {
        "decision": request.decision,
        "feedback": request.feedback,
    }
    graph.invoke(
        Command(resume=human_response),
        config=config,
    )
    return _thread_response(request.thread_id)


# Registered last so the API routes above take precedence over "/".
mount_frontend(app)
