import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Send, Command, Overwrite, interrupt

from Models.llm_cache import cache_key, make_llm_cache
from Models.state import BugTriageState, WorkerState
from Models.bug_model import (
    BugReport,
    InvestigationPlan,
    WorkerResult,
    TriageResult,
    EvaluationResult,
    HumanDecision,
)

from prompts.prompts import (
    SYSTEM_EXTRACT_BUG,
    SYSTEM_INVESTIGATION_PLAN,
    WORKER_PROMPT,
    SYNTHESIZER_PROMPT,
    EVALUATOR_PROMPT,
    REVISION_PROMPT,
)

load_dotenv()

# Maximum number of automatic evaluator-driven revisions per review round
# before the triage is handed to a human regardless of the evaluation.
MAX_REVISIONS = 5

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

llm = ChatOpenAI(
    model=MODEL,
    temperature=0,
)

# Identical prompts reuse the stored response instead of calling OpenAI.
llm_cache = make_llm_cache()


def _invoke_structured(schema: type[BaseModel], messages: list):
    key = None
    if llm_cache is not None:
        key = cache_key(MODEL, schema, messages)
        cached = llm_cache.get(key)
        if cached is not None:
            return schema.model_validate_json(cached)

    result = llm.with_structured_output(schema).invoke(messages)

    if key is not None:
        llm_cache.set(key, result.model_dump_json())
    return result


def _reviewer_feedback(state: BugTriageState) -> list[str]:
    """Feedback from every human "revise" decision so far, oldest first."""
    return [
        decision.feedback
        for decision in state.get("review_history", [])
        if decision.decision == "revise" and decision.feedback
    ]


def _format_reviewer_feedback(feedback: list[str]) -> str:
    if not feedback:
        return ""

    items = "\n".join(
        f"{number}. {text}"
        for number, text in enumerate(feedback, start=1)
    )
    return f"""
Human reviewer feedback (oldest first). Address all of it; if items
conflict, the most recent one takes priority:
{items}
"""


def extract_bug(state: BugTriageState):
    raw_text = state["raw_bug"].replace("\r\n", "\n").strip()

    if not raw_text:
        raise ValueError("Bug report is empty.")

    bug_report = _invoke_structured(BugReport, [
        (
            "system",
            SYSTEM_EXTRACT_BUG,
        ),
        (
            "human",
            f"""
Extract the following bug report into the required structured format.

Bug report:
{raw_text}
""",
        ),
    ])

    return {
        "bug_report": bug_report,
    }

def orchestrator(state: BugTriageState):
    bug_report = state["bug_report"]

    reviewer_feedback = _format_reviewer_feedback(
        _reviewer_feedback(state)
    )

    investigation_plan = _invoke_structured(InvestigationPlan, [
        (
            "system",
            SYSTEM_INVESTIGATION_PLAN,
        ),
        (
            "human",
            f"""
Create an investigation plan for the following structured bug report.

Bug report:
{bug_report}
{reviewer_feedback}
Decide which investigations are necessary and create the required
investigation tasks.

Do not solve the investigations yourself.
""",
        ),
    ])

    return {
        "investigation_plan": investigation_plan,
    }

def assign_worker(state: BugTriageState):
    plan = state["investigation_plan"]
    tasks = plan.tasks

    if not tasks:
        raise ValueError("Investigation plan contains no tasks.")

    reviewer_feedback = _reviewer_feedback(state)

    sends = []

    for task in tasks:
        sends.append(
            Send(
                "worker",
                {
                    "task": task,
                    "bug_report": state["bug_report"],
                    "reviewer_feedback": reviewer_feedback,
                },
            )
        )

    return sends

def worker(state: WorkerState):
    task = state["task"]
    bug_report = state["bug_report"]

    reviewer_feedback = _format_reviewer_feedback(
        state.get("reviewer_feedback", [])
    )

    work_result = _invoke_structured(WorkerResult, [
        (
            "system",
            WORKER_PROMPT,
        ),
        (
            "human",
            f"""
Complete the following investigation task.

Investigation task:
{task}

Relevant bug report:
{bug_report}
{reviewer_feedback}
Investigate only the assigned task and return the result in the
required structured format.
""",
        ),
    ])

    return {
        "worker_results": [work_result],
    }

def _format_worker_results(
    worker_results: list[WorkerResult],
) -> str:

    formatted_results = []

    for result in worker_results:
        evidence = "\n".join(result.evidence)
        limitations = "\n".join(result.limitations)

        formatted_result = f"""
Task ID: {result.task_ID}
Investigation Type: {result.investigation_type}
Conclusion: {result.conclusion}

Evidence:
{evidence}

Confidence:
{result.confidence}

Limitations:
{limitations}
""".strip()

        formatted_results.append(formatted_result)

    return "\n\n---\n\n".join(formatted_results)

def synthesize_triage(state: BugTriageState):
    bug_report = state["bug_report"]
    worker_results = state["worker_results"]

    formatted_results = _format_worker_results(worker_results)

    reviewer_feedback = _format_reviewer_feedback(
        _reviewer_feedback(state)
    )

    triage_result = _invoke_structured(TriageResult, [
        (
            "system",
            SYNTHESIZER_PROMPT,
        ),
        (
            "human",
            f"""
Produce the final bug triage result using the original structured
bug report and the completed investigation results below.

Structured bug report:
{bug_report}

Worker investigation results:
{formatted_results}
{reviewer_feedback}
Combine the findings into one final TriageResult.

Use only the supplied evidence, worker findings, and reviewer feedback.

If evidence is weak, incomplete, or conflicting, reflect that in
the confidence and uncertainty fields rather than inventing
information.
""",
        ),
    ])

    return {
        "triage_result": triage_result,
    }

def evaluate_triage(state: BugTriageState):
    bug_report = state["bug_report"]
    worker_results = state["worker_results"]
    triage_result = state["triage_result"]

    formatted_results = _format_worker_results(
        worker_results
    )

    reviewer_feedback = _format_reviewer_feedback(
        _reviewer_feedback(state)
    )

    evaluation = _invoke_structured(EvaluationResult, [
        (
            "system",
            EVALUATOR_PROMPT,
        ),
        (
            "human",
            f"""
Evaluate the following final bug triage result against the
original bug report and worker investigation results.

Original structured bug report:
{bug_report}

Worker investigation results:
{formatted_results}
{reviewer_feedback}
Final triage result:
{triage_result}

Assess the triage for:

- groundedness
- completeness
- consistency
- severity correctness
- actionability
- whether it addresses all human reviewer feedback (if any)

Do not rewrite the triage result.

Return only the required structured EvaluationResult.
""",
        ),
    ])

    return {
        "evaluation": evaluation,
    }

def routing(state: BugTriageState):

    evaluation = state["evaluation"]
    revision_count = state.get("revision_count", 0)

    if evaluation.passed:
        return "good"

    if revision_count >= MAX_REVISIONS:
        return "good"

    return "bad"

def revise_triage(state: BugTriageState):
    evaluation = state["evaluation"]
    bug_report = state["bug_report"]
    worker_results = state["worker_results"]
    triage_result = state["triage_result"]

    revision_count = state.get(
        "revision_count",
        0,
    )

    formatted_results = _format_worker_results(
        worker_results
    )

    evaluator_feedback = (
        evaluation.revision_feedback
        or "No specific evaluator feedback was supplied."
    )

    feedback_text = f"""
Evaluator feedback:
{evaluator_feedback}
{_format_reviewer_feedback(_reviewer_feedback(state))}"""

    revised_triage_result = _invoke_structured(TriageResult, [
        (
            "system",
            REVISION_PROMPT,
        ),
        (
            "human",
            f"""
Revise the current bug triage result using the feedback below.

Original structured bug report:
{bug_report}

Worker investigation results:
{formatted_results}

Current triage result:
{triage_result}

{feedback_text}

Correct the identified issues while preserving any valid
conclusions that are still supported by the evidence.

Return the revised result in the required TriageResult structure.
""",
        ),
    ])

    return {
        "triage_result": revised_triage_result,
        "revision_count": revision_count + 1,
    }

def human_review(
    state: BugTriageState,
) -> Command[Literal["orchestrator", "__end__"]]:

    response = interrupt({
        "question": (
            "Do you approve, revise, or reject "
            "this triage result?"
        ),
        "triage_result": state["triage_result"],
        "evaluation": state["evaluation"],
    })

    decision = str(
        response.get("decision", "")
    ).lower().strip()

    feedback = (response.get("feedback") or "").strip() or None

    if decision not in {
        "approve",
        "revise",
        "reject",
    }:
        raise ValueError(
            "Decision must be 'approve', "
            "'revise', or 'reject'."
        )

    if decision == "revise" and not feedback:
        raise ValueError(
            "Feedback is required to request a revision."
        )

    human_decision = HumanDecision(
        decision=decision,
        feedback=feedback,
    )

    update = {
        "human_decision": human_decision,
        "review_history": [human_decision],
    }

    if decision == "revise":
        # Start a new review round: re-plan and re-investigate with the
        # reviewer's feedback, replacing the previous round's findings.
        update.update({
            "worker_results": Overwrite([]),
            "revision_count": 0,
            "review_round": state.get("review_round", 1) + 1,
        })
        return Command(
            update=update,
            goto="orchestrator",
        )

    return Command(
        update=update,
        goto=END,
    )
