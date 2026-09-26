import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Button from '../components/ui/Button.jsx'
import DeleteLogDialog from '../components/study-logs/DeleteLogDialog.jsx'
import ConfirmDialog from '../components/ui/ConfirmDialog.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import TagBadge from '../components/ui/TagBadge.jsx'
import { useStudyLog } from '../hooks/useStudyLog.js'
import {
  formatDateTime,
  formatDuration,
  formatStudyDate,
  formatUnderstanding,
} from '../lib/studyLogFormatters.js'

export default function StudyLogDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    log,
    isLoading,
    error,
    isNotFound,
    isUpdating,
    isDeleting,
    mutationError,
    refetch,
    toggleComplete,
    removeLog,
  } = useStudyLog(id)

  const [dialog, setDialog] = useState(null) // 'complete' | 'reopen' | 'delete'
  const [reflection, setReflection] = useState('')

  if (isLoading) return <LoadingState message="TIL을 불러오는 중입니다." />

  if (error) {
    return (
      <ErrorState message="TIL을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요." onRetry={refetch} />
    )
  }

  // 주소는 올바른데 기록이 없는 경우다. 정의되지 않은 주소를 처리하는 화면과 다르다.
  if (isNotFound) {
    return (
      <EmptyState
        title="기록을 찾을 수 없습니다."
        description="이미 삭제되었거나 주소가 잘못되었을 수 있어요."
        actionLabel="학습 목록으로"
        onAction={() => navigate('/logs')}
      />
    )
  }

  function openCompleteDialog() {
    setReflection(log.reflection ?? '')
    setDialog('complete')
  }

  async function confirmComplete() {
    const updated = await toggleComplete(reflection)
    if (updated) setDialog(null)
  }

  async function confirmReopen() {
    const updated = await toggleComplete()
    if (updated) setDialog(null)
  }

  async function confirmDelete() {
    const removed = await removeLog()
    if (removed) navigate('/logs')
  }

  return (
    <>
      <nav className="breadcrumb" aria-label="현재 위치">
        <Link to="/logs" className="link">
          학습 목록
        </Link>
        <span aria-hidden="true">/</span>
        <span>상세</span>
      </nav>

      <header className="detail__head">
        <div>
          <div className="detail__title-row">
            <h1 className="detail__title">{log.title}</h1>
            <StatusBadge isCompleted={log.is_completed} />
          </div>
          <div className="detail__tags">
            {(log.tags ?? []).map((tag) => (
              <TagBadge key={tag} tag={tag} size="sm" />
            ))}
            <time className="detail__date" dateTime={log.study_date}>
              {formatStudyDate(log.study_date)}
            </time>
          </div>
        </div>

        <div className="detail__actions">
          <Button variant="secondary" onClick={() => navigate(`/logs/${log.id}/edit`)}>
            수정
          </Button>
          <Button variant="danger" onClick={() => setDialog('delete')}>
            삭제
          </Button>
        </div>
      </header>

      {mutationError && !dialog ? (
        <p className="form__alert" role="alert">
          {mutationError}
        </p>
      ) : null}

      <div className="detail__summary">
        <div className="summary-item">
          <dt>학습 시간</dt>
          <dd>{formatDuration(log.duration_minutes)}</dd>
        </div>
        <div className="summary-item">
          <dt>이해도</dt>
          <dd>
            {log.understanding} · {formatUnderstanding(log.understanding)}
          </dd>
        </div>
        <div className="summary-item">
          <dt>상태</dt>
          <dd>{log.is_completed ? '완료' : '진행 중'}</dd>
        </div>
      </div>

      <section className="detail__card">
        <h2 className="detail__card-title">학습 내용</h2>
        <p className="detail__body">{log.content}</p>
        {log.resource_url ? (
          <a className="link" href={log.resource_url} target="_blank" rel="noreferrer">
            참고 링크 열기
          </a>
        ) : null}
      </section>

      <section className="detail__card">
        <h2 className="detail__card-title">회고</h2>
        {log.reflection ? (
          <p className="detail__body">{log.reflection}</p>
        ) : (
          <p className="detail__placeholder">
            아직 회고가 없습니다. 학습을 마쳤다면 회고를 남기고 완료로 표시해보세요.
          </p>
        )}

        <div className="detail__completion">
          {log.is_completed ? (
            <Button variant="secondary" isLoading={isUpdating} onClick={() => setDialog('reopen')}>
              완료 취소
            </Button>
          ) : (
            <Button variant="primary" isLoading={isUpdating} onClick={openCompleteDialog}>
              학습 완료로 표시
            </Button>
          )}
        </div>
      </section>

      <p className="detail__meta">마지막 수정 {formatDateTime(log.updated_at)}</p>

      <ConfirmDialog
        open={dialog === 'complete'}
        title="학습을 마쳤나요?"
        description="완료로 표시하려면 회고를 열 자 이상 남겨주세요."
        confirmLabel="완료로 표시"
        tone="primary"
        isProcessing={isUpdating}
        error={mutationError}
        onCancel={() => setDialog(null)}
        onConfirm={confirmComplete}
      >
        <textarea
          className="input input--textarea"
          rows={4}
          value={reflection}
          maxLength={2000}
          placeholder="배운 점이나 다음에 해볼 것을 적어주세요"
          onChange={(event) => setReflection(event.target.value)}
        />
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === 'reopen'}
        title="완료를 취소할까요?"
        description="작성한 회고는 지우지 않습니다. 다시 완료로 표시할 때 그대로 씁니다."
        confirmLabel="완료 취소"
        tone="primary"
        isProcessing={isUpdating}
        error={mutationError}
        onCancel={() => setDialog(null)}
        onConfirm={confirmReopen}
      />

      <DeleteLogDialog
        target={dialog === 'delete' ? log : null}
        isDeleting={isDeleting}
        error={mutationError}
        onCancel={() => setDialog(null)}
        onConfirm={confirmDelete}
      />
    </>
  )
}
