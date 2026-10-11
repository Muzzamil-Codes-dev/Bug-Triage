const STATUS_LABELS = {
  awaiting_review: "Awaiting your review",
  completed: "Approved",
  rejected: "Rejected",
};

export function SeverityBadge({ severity }) {
  return (
    <span className={`badge severity-${severity.toLowerCase()}`}>
      {severity}
    </span>
  );
}

export function StatusBadge({ status }) {
  return (
    <span className={`badge status-${status}`}>{STATUS_LABELS[status]}</span>
  );
}

export function Meter({ label, value }) {
  const percent = Math.round(value * 100);
  const level = value >= 0.75 ? "high" : value >= 0.5 ? "mid" : "low";

  return (
    <div className="meter">
      <div className="meter-label">
        <span>{label}</span>
        <span className="meter-value">{percent}%</span>
      </div>
      <div
        className="meter-track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className={`meter-fill ${level}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

export function ItemList({ title, items, ordered = false, emptyText = "None" }) {
  const List = ordered ? "ol" : "ul";

  return (
    <section className="item-list">
      <h3>{title}</h3>
      {items && items.length > 0 ? (
        <List>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </List>
      ) : (
        <p className="muted">{emptyText}</p>
      )}
    </section>
  );
}
