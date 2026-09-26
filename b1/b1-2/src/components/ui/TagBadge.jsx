import { formatTag } from '../../lib/studyLogFormatters.js'

// 태그 하나를 배지로 보여준다.
// onClick 을 받으면 필터 칩으로, 없으면 표시 전용으로 동작한다.
// count 를 받으면 뒤에 개수를 붙이고,
// label 을 받으면 '전체' 처럼 태그가 아닌 칩으로 쓴다.
export default function TagBadge({ tag, label, count, selected = false, size = 'md', onClick }) {
  const className = [
    'tag-badge',
    `tag-badge--${size}`,
    selected ? 'tag-badge--selected' : '',
    onClick ? 'tag-badge--clickable' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const body = (
    <>
      {label ?? formatTag(tag)}
      {count === undefined ? null : <span className="tag-badge__count">{count}</span>}
    </>
  )

  if (!onClick) return <span className={className}>{body}</span>

  return (
    <button type="button" className={className} aria-pressed={selected} onClick={() => onClick(tag)}>
      {body}
    </button>
  )
}
