import Button from './Button.jsx'

export default function ErrorState({
  title = '요청에 실패했습니다.',
  message = '잠시 후 다시 시도해 주세요.',
  onRetry,
}) {
  return (
    <div className="state state--error" role="alert">
      <p className="state__title">{title}</p>
      <p className="state__message">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          다시 시도
        </Button>
      ) : null}
    </div>
  )
}
