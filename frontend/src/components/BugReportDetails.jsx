const TEXT_FIELDS = [
  ["description", "Description"],
  ["service", "Service"],
  ["environment", "Environment"],
  ["user_impact", "User impact"],
  ["other_supplied_evidence", "Other evidence"],
];

const LIST_FIELDS = [
  ["reproduction_steps", "Reproduction steps"],
  ["recent_changes", "Recent changes"],
];

export default function BugReportDetails({ report }) {
  return (
    <details className="card report-details">
      <summary>
        <h2>Extracted bug report</h2>
        <span className="muted">What the AI pulled out of your text</span>
      </summary>

      <dl className="facts">
        {TEXT_FIELDS.filter(([key]) => report[key]).map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{report[key]}</dd>
          </div>
        ))}

        {LIST_FIELDS.filter(([key]) => report[key]?.length).map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>
              <ol>
                {report[key].map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ol>
            </dd>
          </div>
        ))}

        {report.logs?.length > 0 && (
          <div>
            <dt>Logs</dt>
            <dd>
              <pre>{report.logs.join("\n")}</pre>
            </dd>
          </div>
        )}

        {report.stack_trace && (
          <div>
            <dt>Stack trace</dt>
            <dd>
              <pre>{report.stack_trace}</pre>
            </dd>
          </div>
        )}
      </dl>
    </details>
  );
}
