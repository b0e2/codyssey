export default function LoadingState({ message = '불러오는 중입니다.', size = 'md' }) {
  return (
    <div className={`state state--${size}`} role="status" aria-live="polite">
      <span className="state__spinner" aria-hidden="true" />
      <p className="state__message">{message}</p>
    </div>
  )
}
