import { useEffect, useRef } from 'react'
import Button from './Button.jsx'

// 되돌릴 수 없는 동작 앞에 한 번 더 묻는다.
// 처리 중에는 확인 버튼을 막아 같은 요청이 두 번 나가지 않게 한다.
export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = '확인',
  cancelLabel = '취소',
  tone = 'danger',
  isProcessing = false,
  error,
  onConfirm,
  onCancel,
  children,
}) {
  const dialogRef = useRef(null)

  // 열릴 때 대화상자로 초점을 옮기고 Escape 로 닫는다.
  // 브라우저 대화상자가 아니라 직접 만든 요소라 여기서 처리해야 한다.
  useEffect(() => {
    if (!open) return undefined

    dialogRef.current?.focus()

    function handleKeyDown(event) {
      if (event.key === 'Escape' && !isProcessing) onCancel()
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, isProcessing, onCancel])

  if (!open) return null

  return (
    <div className="dialog-backdrop">
      <div
        ref={dialogRef}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        tabIndex={-1}
      >
        <h2 id="dialog-title" className="dialog__title">
          {title}
        </h2>
        {description ? <p className="dialog__description">{description}</p> : null}

        {children}

        {error ? (
          <p className="dialog__error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="dialog__actions">
          <Button variant="secondary" onClick={onCancel} disabled={isProcessing}>
            {cancelLabel}
          </Button>
          <Button
            variant={tone === 'danger' ? 'danger' : 'primary'}
            isLoading={isProcessing}
            loadingLabel="처리 중"
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
