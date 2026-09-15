import { formatCompletionStatus } from '../../lib/studyLogFormatters.js'

export default function StatusBadge({ isCompleted, size = 'md' }) {
  const tone = isCompleted ? 'done' : 'ongoing'

  return (
    <span className={`badge badge--${tone} badge--${size}`}>
      {formatCompletionStatus(isCompleted)}
    </span>
  )
}
