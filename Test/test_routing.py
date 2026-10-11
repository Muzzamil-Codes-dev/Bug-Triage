from Models.Nodes import routing, MAX_REVISIONS
from Models.bug_model import EvaluationResult


def _evaluation(passed: bool) -> EvaluationResult:
    return EvaluationResult(
    passed=passed,
    overall_score=0.9,
    groundedness_score=0.9,
    completeness_score=0.9,
    consistency_score=0.9,
    severity_policy_score=0.9,
    actionability_score=0.9,
    identified_issues=[],
)


def test_routing_passed_evaluation_goes_to_human():
    state = {
        "evaluation": _evaluation(passed=True),
        "revision_count": 0,
    }

    assert routing(state) == "good"


def test_routing_failed_evaluation_goes_to_revision():
    #Arrange
    state = {
        "evaluation": _evaluation(passed=False),
        "revision_count": 2,
    }
    #Act
    result = routing(state)

    # Assert
    assert result == "bad"


def test_routing_failed_evaluation_at_revision_limit_goes_to_human():
    state = {
        "evaluation": _evaluation(passed=False),
        "revision_count": MAX_REVISIONS,
    }

    assert routing(state) == "good"
