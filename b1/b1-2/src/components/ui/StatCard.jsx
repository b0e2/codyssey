export default function StatCard({ icon, label, value, unit, description, tone = 'default' }) {
  return (
    <div className={`stat-card stat-card--${tone}`}>
      {icon ? (
        <span className="stat-card__icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <div>
        <p className="stat-card__label">{label}</p>
        <p className="stat-card__value">
          {value}
          {unit ? <span className="stat-card__unit">{unit}</span> : null}
        </p>
        {description ? <p className="stat-card__description">{description}</p> : null}
      </div>
    </div>
  )
}
