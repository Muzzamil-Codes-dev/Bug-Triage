import { SAMPLE_REPORTS } from "../samples.js";

export default function BugForm({ value, onChange, onSubmit }) {
  const canSubmit = value.trim().length > 0;

  function handleSubmit(event) {
    event.preventDefault();
    if (canSubmit) {
      onSubmit();
    }
  }

  function handleKeyDown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      handleSubmit(event);
    }
  }

  return (
    <form className="card bug-form" onSubmit={handleSubmit}>
      <label htmlFor="bug-report">
        <h2>Bug report</h2>
        <span className="muted">
          Paste it as-is: description, logs, stack traces, repro steps,
          recent changes. No special format needed.
        </span>
      </label>

      <textarea
        id="bug-report"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="e.g. Checkout returns HTTP 500 in production since this morning's deploy..."
        rows={14}
        autoFocus
      />

      <div className="form-footer">
        <div className="samples">
          <span className="muted">Try a sample:</span>
          {SAMPLE_REPORTS.map((sample) => (
            <button
              key={sample.label}
              type="button"
              className="chip-button"
              onClick={() => onChange(sample.text)}
            >
              {sample.label}
            </button>
          ))}
        </div>

        <button type="submit" className="button primary" disabled={!canSubmit}>
          Run triage
        </button>
      </div>
    </form>
  );
}
