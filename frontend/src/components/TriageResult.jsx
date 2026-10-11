import { ItemList, Meter, SeverityBadge, StatusBadge } from "./ui.jsx";

export default function TriageResult({ title, result, status, revisionCount }) {
  return (
    <section className="card triage">
      <div className="triage-head">
        <div className="badges">
          <SeverityBadge severity={result.severity} />
          <StatusBadge status={status} />
        </div>
        {revisionCount > 0 && (
          <span className="muted" title="Revisions made automatically after the evaluator flagged issues">
            Auto-revised {revisionCount} {revisionCount === 1 ? "time" : "times"}
          </span>
        )}
      </div>

      <h2 className="triage-title">{title}</h2>

      <Meter label="Confidence" value={result.confidence} />

      <dl className="facts">
        <div>
          <dt>Recommended team</dt>
          <dd>{result.recommended_team}</dd>
        </div>
        <div>
          <dt>Affected components</dt>
          <dd className="chips">
            {result.affected_component.length > 0
              ? result.affected_component.map((component) => (
                  <span key={component} className="chip">
                    {component}
                  </span>
                ))
              : "Not identified"}
          </dd>
        </div>
      </dl>

      <ItemList title="Recommended actions" items={result.recommended_actions} ordered />
      <ItemList title="Probable causes" items={result.probable_causes} />
      <ItemList title="Evidence" items={result.evidence_summary} />
      <ItemList
        title="Possible duplicates"
        items={result.duplicate_candidates}
        emptyText="No duplicates identified."
      />

      <section className="uncertainty">
        <h3>Uncertainty</h3>
        <p>{result.uncertainty}</p>
      </section>
    </section>
  );
}
