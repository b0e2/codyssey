// eslint-disable react/only-export-components
// 삭제 대화상자와 그 상태를 다루는 훅을 한 파일에 둔다.
// 둘은 항상 함께 쓰이고 따로 쓸 일이 없다.
import { useCallback, useState } from 'react'
import ConfirmDialog from '../ui/ConfirmDialog.jsx'

// 삭제 대상 고르기와 확인 흐름을 담는다.
// 네 화면이 같은 상태와 같은 순서를 반복하고 있었다.
export function useLogDeletion(removeLog) {
  const [target, setTarget] = useState(null)

  const confirm = useCallback(async () => {
    if (!target) return
    const removed = await removeLog(target.id)
    // 실패하면 대화상자를 닫지 않는다. 오류를 그 자리에서 보여준다.
    if (removed) setTarget(null)
  }, [target, removeLog])

  return {
    target,
    ask: setTarget,
    cancel: useCallback(() => setTarget(null), []),
    confirm,
  }
}


// 삭제 확인 문구를 한 곳에 둔다.
// 홈, 목록, 태그, 상세 네 화면이 같은 문장을 쓰므로 각자 적으면 갈린다.
export default function DeleteLogDialog({ target, isDeleting, error, onCancel, onConfirm }) {
  return (
    <ConfirmDialog
      open={Boolean(target)}
      title="이 TIL을 삭제할까요?"
      description={target ? `“${target.title}” 기록이 사라집니다. 되돌릴 수 없습니다.` : ''}
      confirmLabel="삭제"
      isProcessing={isDeleting}
      error={error}
      onCancel={onCancel}
      onConfirm={onConfirm}
    />
  )
}
