from unittest.mock import patch

from langgraph.types import Command

from graph.graph import build_graph, make_checkpointer
from fakes import FakeLLM, TRIAGE

CONFIG = {"configurable": {"thread_id": "thread-1"}}


def test_paused_triage_survives_a_restart(tmp_path):
    db_path = str(tmp_path / "checkpoints.sqlite")

    first_saver = make_checkpointer(db_path)
    with patch("Models.Nodes.llm", FakeLLM()):
        build_graph(first_saver).invoke({"raw_bug": "Login broken."}, CONFIG)
    first_saver.conn.close()

    # A fresh graph + checkpointer on the same file, as after a restart.
    second_saver = make_checkpointer(db_path)
    restarted = build_graph(second_saver)

    snapshot = restarted.get_state(CONFIG)
    assert snapshot.next == ("human_review",)
    assert snapshot.values["triage_result"] == TRIAGE

    with patch("Models.Nodes.llm", FakeLLM()):
        result = restarted.invoke(Command(resume={"decision": "approve"}), CONFIG)
    second_saver.conn.close()

    assert result["human_decision"].decision == "approve"
