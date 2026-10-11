import os
import sqlite3
from pathlib import Path

from langgraph.graph import StateGraph, START
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from Models.state import BugTriageState
from Models.bug_model import (
    BugReport,
    InvestigationPlan,
    InvestigationTask,
    WorkerResult,
    TriageResult,
    EvaluationResult,
    HumanDecision,
)
from Models.Nodes import (
    extract_bug,
    orchestrator,
    assign_worker,
    worker,
    synthesize_triage,
    evaluate_triage,
    routing,
    revise_triage,
    human_review,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT_DB = PROJECT_ROOT / "data" / "checkpoints.sqlite"


# Explicitly allow the state models to be restored from checkpoints
# (needed to resume after the human_review interrupt).
serializer = JsonPlusSerializer(
    allowed_msgpack_modules=[
        BugReport,
        InvestigationPlan,
        InvestigationTask,
        WorkerResult,
        TriageResult,
        EvaluationResult,
        HumanDecision,
    ],
)


def make_checkpointer(path: str) -> SqliteSaver:
    """SQLite checkpointer, so triages survive server restarts."""
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    # SqliteSaver guards the shared connection with its own lock.
    conn = sqlite3.connect(path, check_same_thread=False)
    return SqliteSaver(conn, serde=serializer)


def build_graph(checkpointer: BaseCheckpointSaver):
    builder = StateGraph(BugTriageState)


    # -------------------------
    # Nodes
    # -------------------------

    builder.add_node("extract_bug", extract_bug)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("worker", worker)
    builder.add_node("synthesizer", synthesize_triage)
    builder.add_node("evaluate", evaluate_triage)
    builder.add_node("revise_triage", revise_triage)
    builder.add_node("human_review", human_review)


    # -------------------------
    # Edges
    # -------------------------

    builder.add_edge(START,"extract_bug")

    builder.add_edge("extract_bug","orchestrator")

    builder.add_conditional_edges(
        "orchestrator",
        assign_worker,
        ["worker"],
    )

    builder.add_edge("worker","synthesizer")
    builder.add_edge("synthesizer","evaluate")

    builder.add_conditional_edges(
        "evaluate",
        routing,
        {
            "good": "human_review",
            "bad": "revise_triage",
        },
    )

    builder.add_edge("revise_triage","evaluate")

    # human_review routes itself with Command: "approve"/"reject" end the
    # run, "revise" goes back to the orchestrator for a new review round.


    # -------------------------
    # Compile
    # -------------------------

    return builder.compile(checkpointer=checkpointer)


graph = build_graph(
    make_checkpointer(
        os.getenv("CHECKPOINT_DB", str(DEFAULT_CHECKPOINT_DB))
    )
)
