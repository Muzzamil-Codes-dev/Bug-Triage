from unittest.mock import MagicMock, patch

from Models.bug_model import BugReport, TriageResult
from Models.llm_cache import LLMCache, cache_key, make_llm_cache
from Models.Nodes import _invoke_structured

MESSAGES = [("system", "Extract."), ("human", "Login is broken.")]


def test_cache_round_trip(tmp_path):
    cache = LLMCache(str(tmp_path / "cache.sqlite"))

    cache.set("key", "value")

    assert cache.get("key") == "value"
    assert cache.get("missing") is None


def test_cache_key_depends_on_model_schema_and_messages():
    key = cache_key("gpt-4o-mini", BugReport, MESSAGES)

    assert key == cache_key("gpt-4o-mini", BugReport, MESSAGES)
    assert key != cache_key("gpt-4o", BugReport, MESSAGES)
    assert key != cache_key("gpt-4o-mini", TriageResult, MESSAGES)
    assert key != cache_key("gpt-4o-mini", BugReport, [("human", "Other.")])


def test_repeated_call_is_served_from_cache(tmp_path):
    fake_llm = MagicMock()
    structured = fake_llm.with_structured_output.return_value
    structured.invoke.return_value = BugReport(title="Login", description="Broken")

    with (
        patch("Models.Nodes.llm", fake_llm),
        patch("Models.Nodes.llm_cache", LLMCache(str(tmp_path / "cache.sqlite"))),
    ):
        first = _invoke_structured(BugReport, MESSAGES)
        second = _invoke_structured(BugReport, MESSAGES)

    assert first == second
    assert isinstance(second, BugReport)
    assert structured.invoke.call_count == 1


def test_cache_can_be_disabled(monkeypatch):
    monkeypatch.setenv("LLM_CACHE_DB", "off")

    assert make_llm_cache() is None
