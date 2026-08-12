export function StatusCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: number;
  helper?: string;
}) {
  return (
    <article className="status-card">
      <div className="status-card__label">{label}</div>
      <div className="status-card__value">{value}</div>
      {helper ? <div className="status-card__helper">{helper}</div> : null}
    </article>
  );
}
