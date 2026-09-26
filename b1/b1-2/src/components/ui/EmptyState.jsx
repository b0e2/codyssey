import Button from './Button.jsx'

// 데이터가 하나도 없는 경우와 필터 결과가 없는 경우를 같은 시각 패턴으로 보여주되,
// 문구와 액션은 호출하는 화면이 정한다.
export default function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <div className="state state--empty">
      <p className="state__title">{title}</p>
      {description ? <p className="state__message">{description}</p> : null}
      {actionLabel && onAction ? (
        <Button variant="secondary" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}
