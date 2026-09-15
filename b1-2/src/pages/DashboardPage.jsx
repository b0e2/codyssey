import { useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import StudyLogCard from '../components/study-logs/StudyLogCard.jsx'
import DeleteLogDialog, { useLogDeletion } from '../components/study-logs/DeleteLogDialog.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import { LeafIcon, PlusIcon } from '../components/ui/icons.jsx'

import { useStudyLogs } from '../hooks/useStudyLogs.js'
import { selectRecentLogs } from '../lib/studyLogSelectors.js'

const RECENT_LIMIT = 5

export default function DashboardPage() {
  const navigate = useNavigate()
  // 목록 화면과 같은 훅을 이 화면에서 따로 호출한다.
  // 공유 캐시를 두지 않아 화면마다 자기 로딩·에러 상태를 갖는다.
  const { logs, isLoading, error, refetch, deletingId, mutationError, removeLog } = useStudyLogs()
  const deletion = useLogDeletion(removeLog)
  const goEdit = useCallback((item) => navigate(`/logs/${item.id}/edit`), [navigate])
  const recentLogs = selectRecentLogs(logs, RECENT_LIMIT)

  function renderRecent() {
    if (isLoading) return <LoadingState message="최근 TIL을 불러오는 중입니다." />

    if (error) {
      return (
        <ErrorState
          message="최근 TIL을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
          onRetry={refetch}
        />
      )
    }

    if (logs.length === 0) {
      return (
        <EmptyState
          title="아직 작성한 TIL이 없습니다."
          description="오늘의 배움을 기록하면 여기에서 확인할 수 있어요."
          actionLabel="새 TIL 작성"
          onAction={() => navigate('/logs/new')}
        />
      )
    }

    return (
      <ul className="log-list">
        {recentLogs.map((log) => (
          <li key={log.id}>
            <StudyLogCard
              log={log}
              isDeleting={deletingId === log.id}
              onEdit={goEdit}
              onDelete={deletion.ask}
            />
          </li>
        ))}
      </ul>
    )
  }

  return (
    <>
      <section className="hero">
        <div className="hero__body">
          <p className="hero__eyebrow">A small record, a bigger tomorrow</p>
          <h1 className="hero__title">오늘도, 좋은 배움이에요.</h1>
          <p className="hero__description">
            오늘의 배움을 기록하고,
            <br />더 나은 내일을 만들어가요.
          </p>
          <div className="hero__actions">
            <Link to="/logs/new" className="button button--primary">
              <PlusIcon />새 TIL 작성
            </Link>
            <Link to="/logs" className="button button--secondary">
              학습 목록 보기
            </Link>
          </div>
        </div>

        <div className="hero__ornament" aria-hidden="true">
          <LeafIcon size={280} strokeWidth={0.6} />
          <LeafIcon size={150} strokeWidth={0.9} />
        </div>
      </section>

      <section className="section">
        <div className="section__head">
          <div>
            <h2 className="section__title">최근 작성한 TIL</h2>
            <p className="section__description">지금까지 기록한 소중한 배움들을 한눈에 확인해보세요.</p>
          </div>
          {logs.length > RECENT_LIMIT ? (
            <Link to="/logs" className="link">
              전체 보기
            </Link>
          ) : null}
        </div>
        {mutationError && !deletion.target ? (
          <p className="form__alert" role="alert">
            {mutationError}
          </p>
        ) : null}
        {renderRecent()}
      </section>

      <DeleteLogDialog
        target={deletion.target}
        isDeleting={deletion.target?.id === deletingId}
        error={mutationError}
        onCancel={deletion.cancel}
        onConfirm={deletion.confirm}
      />
    </>
  )
}
