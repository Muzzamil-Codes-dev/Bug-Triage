import { useEffect, useState } from "react";

const PIPELINE = [
  ["Extract", "Structure the raw report"],
  ["Plan", "Decide which investigations are needed"],
  ["Investigate", "Workers check severity, component, duplicates, root cause"],
  ["Synthesize", "Combine findings into one triage"],
  ["Evaluate", "Score the triage and revise it if it falls short"],
];

const REVISION_PIPELINE = [
  ["Plan", "Re-plan the investigation around your feedback"],
  ["Investigate", "Workers re-investigate with your feedback"],
  ["Synthesize", "Build a new triage from the fresh findings"],
  ["Evaluate", "Check the triage, including that your feedback was applied"],
];

export default function Loading({ revision = false }) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const steps = revision ? REVISION_PIPELINE : PIPELINE;

  return (
    <section className="card loading" aria-live="polite">
      <div className="loading-head">
        <span className="spinner" aria-hidden="true" />
        <div>
          <h2>
            {revision
              ? "Re-investigating with your feedback…"
              : "Triaging your bug report…"}
          </h2>
          <p className="muted">
            {seconds}s elapsed. This usually takes{" "}
            {revision ? "20–60" : "10–30"} seconds.
          </p>
        </div>
      </div>

      <ol className="pipeline">
        {steps.map(([step, description]) => (
          <li key={step}>
            <strong>{step}</strong>
            <span className="muted">{description}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
