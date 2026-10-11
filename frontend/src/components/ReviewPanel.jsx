import { useRef, useState } from "react";

const BUSY_LABELS = {
  approve: "Approving…",
  revise: "Re-investigating…",
  reject: "Rejecting…",
};

const DECISION_LABELS = {
  approve: "Approved",
  revise: "Asked for a revision",
  reject: "Rejected",
};

export default function ReviewPanel({ status, round, busyDecision, history, onReview }) {
  const [feedback, setFeedback] = useState("");
  const [feedbackError, setFeedbackError] = useState(null);
  const feedbackRef = useRef(null);
  const awaitingReview = status === "awaiting_review";
  const busy = busyDecision !== null;

  async function review(decision) {
    const text = feedback.trim();
    if (decision === "revise" && !text) {
      setFeedbackError("Describe what should change before requesting a revision.");
      feedbackRef.current?.focus();
      return;
    }

    setFeedbackError(null);
    const succeeded = await onReview(decision, text);
    if (succeeded) {
      setFeedback("");
    }
  }

  function decisionButton(decision, label, className) {
    return (
      <button
        type="button"
        className={`button ${className}`}
        disabled={busy}
        onClick={() => review(decision)}
      >
        {busyDecision === decision ? BUSY_LABELS[decision] : label}
      </button>
    );
  }

  return (
    <section className="card review">
      <div className="panel-head">
        <h2>Your review</h2>
        <span className="badge round">Round {round}</span>
      </div>

      {awaitingReview ? (
        <>
          <p className="muted">
            Approve or reject the triage, or tell the agents what to change.
            A revision re-plans and re-investigates the bug with your
            feedback, then comes back here for review.
          </p>

          <label htmlFor="review-feedback" className="field-label">
            Feedback <span className="muted">(required for a revision)</span>
          </label>
          <textarea
            id="review-feedback"
            ref={feedbackRef}
            value={feedback}
            onChange={(event) => {
              setFeedback(event.target.value);
              setFeedbackError(null);
            }}
            placeholder="e.g. Checkout is revenue-critical, raise the severity and add a rollback as the first action."
            rows={4}
            disabled={busy}
            aria-invalid={feedbackError !== null}
            aria-describedby={feedbackError ? "feedback-error" : undefined}
          />
          {feedbackError && (
            <p id="feedback-error" className="field-error" role="alert">
              {feedbackError}
            </p>
          )}

          <div className="review-actions">
            {decisionButton("revise", "Request revision", "revise")}
            {decisionButton("approve", "Approve", "approve")}
            {decisionButton("reject", "Reject", "reject")}
          </div>
        </>
      ) : (
        <p className={`final-status ${status}`}>
          {status === "completed"
            ? "✓ This triage was approved."
            : "✕ This triage was rejected."}
        </p>
      )}

      {history.length > 0 && (
        <section className="history">
          <h3>History</h3>
          <ol>
            {history.map((entry, index) => (
              <li key={index}>
                <strong>{DECISION_LABELS[entry.decision]}</strong>
                {entry.feedback && <q>{entry.feedback}</q>}
              </li>
            ))}
          </ol>
        </section>
      )}
    </section>
  );
}
