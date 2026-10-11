import { useEffect, useState } from "react";

import { createTriage, getTriage, submitReview } from "./api.js";
import BugForm from "./components/BugForm.jsx";
import BugReportDetails from "./components/BugReportDetails.jsx";
import EvaluationPanel from "./components/EvaluationPanel.jsx";
import Loading from "./components/Loading.jsx";
import ReviewPanel from "./components/ReviewPanel.jsx";
import TriageResult from "./components/TriageResult.jsx";

// The open triage's id is kept in the URL (?thread=...) so a page refresh
// or a bookmark reopens it; the server keeps triages across restarts.
function threadIdFromUrl() {
  return new URLSearchParams(window.location.search).get("thread");
}

function setThreadIdInUrl(threadId) {
  const url = new URL(window.location.href);
  if (threadId) {
    url.searchParams.set("thread", threadId);
  } else {
    url.searchParams.delete("thread");
  }
  window.history.replaceState(null, "", url);
}

export default function App() {
  const [bugText, setBugText] = useState("");
  // Latest state of the triage thread, as returned by the API.
  const [triage, setTriage] = useState(null);
  const [restoring, setRestoring] = useState(() => threadIdFromUrl() !== null);
  const [triaging, setTriaging] = useState(false);
  const [busyDecision, setBusyDecision] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const threadId = threadIdFromUrl();
    if (!threadId) {
      return;
    }

    getTriage(threadId)
      .then(setTriage)
      .catch((err) => {
        setThreadIdInUrl(null);
        setError(
          err.status === 404
            ? "That saved triage could not be found. Start a new one below."
            : err.message,
        );
      })
      .finally(() => setRestoring(false));
  }, []);

  async function runTriage() {
    setTriaging(true);
    setError(null);
    try {
      const result = await createTriage(bugText);
      setTriage(result);
      setThreadIdInUrl(result.thread_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setTriaging(false);
    }
  }

  async function review(decision, feedback) {
    setBusyDecision(decision);
    setError(null);
    try {
      setTriage(await submitReview(triage.thread_id, decision, feedback));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setBusyDecision(null);
    }
  }

  function startOver() {
    setBugText("");
    setTriage(null);
    setError(null);
    setThreadIdInUrl(null);
  }

  const reinvestigating = busyDecision === "revise";

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>
            <span aria-hidden="true">🐞</span> Bug Triage
          </h1>
          <p className="muted">
            AI agents investigate your bug report, an evaluator checks their
            work, and you make the final call.
          </p>
        </div>
        {triage && (
          <button
            type="button"
            className="button secondary"
            onClick={startOver}
            disabled={busyDecision !== null}
          >
            New triage
          </button>
        )}
      </header>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      {restoring && <p className="muted">Loading saved triage…</p>}

      {triaging && <Loading />}

      {!restoring && !triaging && !triage && (
        <BugForm value={bugText} onChange={setBugText} onSubmit={runTriage} />
      )}

      {triage && reinvestigating && <Loading revision />}

      {triage && (
        <main className={`results${reinvestigating ? " stale" : ""}`}>
          <div className="results-main">
            <TriageResult
              title={triage.bug_report.title}
              result={triage.triage_result}
              status={triage.status}
              revisionCount={triage.revision_count}
            />
            <BugReportDetails report={triage.bug_report} />
          </div>

          <aside className="results-side">
            <ReviewPanel
              status={triage.status}
              round={triage.review_round}
              busyDecision={busyDecision}
              history={triage.review_history}
              onReview={review}
            />
            <EvaluationPanel evaluation={triage.evaluation} />
          </aside>
        </main>
      )}
    </div>
  );
}
