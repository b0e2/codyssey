// variant로 의미를, isLoading으로 진행 중 상태를 표현한다.
// 제출 중에는 문구만 바꾸지 않고 실제로 disabled를 걸어 중복 요청을 막는다.
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  isLoading = false,
  loadingLabel = '처리 중',
  onClick,
  ...rest
}) {
  const className = `button button--${variant} button--${size}`

  return (
    <button
      type={type}
      className={className}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      onClick={onClick}
      {...rest}
    >
      {isLoading ? loadingLabel : children}
    </button>
  )
}
