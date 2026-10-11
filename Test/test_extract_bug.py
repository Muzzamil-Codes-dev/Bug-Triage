from unittest.mock import MagicMock, patch

from Models.Nodes import extract_bug
from Models.bug_model import BugReport


def test_extract_bug_returns_bug_report():

    # Arrange
    expected_bug = BugReport(
        title="Login failure",
        description="Users cannot log in.",
        environment="production",
    )

    fake_structured_llm = MagicMock()

    fake_llm = MagicMock()

    fake_llm.with_structured_output.return_value = (fake_structured_llm)

    fake_structured_llm.invoke.return_value = expected_bug

    state = {
        "raw_bug": "Users cannot log in to production."
    }

    # Act
    with patch("Models.Nodes.llm", fake_llm):
        result = extract_bug(state)

    # Assert
    assert result["bug_report"] == expected_bug