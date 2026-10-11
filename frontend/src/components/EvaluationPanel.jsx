import { ItemList, Meter } from "./ui.jsx";

const SCORES = [
  ["groundedness_score", "Groundedness"],
  ["completeness_score", "Completeness"],
  ["consistency_score", "Consistency"],
  ["severity_policy_score", "Severity policy"],
  ["actionability_score", "Actionability"],
];

export default function EvaluationPanel({ evaluation }) {
  return (
    <section className="card evaluation">
      <div className="panel-head">
        <h2>Automatic evaluation</h2>
        <span className={`badge ${evaluation.passed ? "pass" : "fail"}`}>
          {evaluation.passed ? "Passed" : "Did not pass"}
        </span>
      </div>

      <Meter label="Overall" value={evaluation.overall_score} />
      <div className="score-grid">
        {SCORES.map(([key, label]) => (
          <Meter key={key} label={label} value={evaluation[key]} />
        ))}
      </div>

      {evaluation.identified_issues.length > 0 && (
        <ItemList title="Issues found" items={evaluation.identified_issues} />
      )}
      {evaluation.revision_feedback && (
        <section className="item-list">
          <h3>Evaluator feedback</h3>
          <p>{evaluation.revision_feedback}</p>
        </section>
      )}
    </section>
  );
}
