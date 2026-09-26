import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import StudyLogCard from '../components/study-logs/StudyLogCard.jsx'
import Button from '../components/ui/Button.jsx'
import DeleteLogDialog, { useLogDeletion } from '../components/study-logs/DeleteLogDialog.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import TagBadge from '../components/ui/TagBadge.jsx'
import { PlusIcon, SearchIcon } from '../components/ui/icons.jsx'

import { useStudyLogs } from '../hooks/useStudyLogs.js'
import { readLogSearchParams, SORT_OPTIONS, writeLogSearchParams } from '../lib/studyLogSelectors.js'
import { filterStudyLogs, getTagCounts, sortStudyLogs } from '../lib/studyLogSelectors.js'

export default function StudyLogsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { logs, isLoading, error, refetch, deletingId, mutationError, removeLog } = useStudyLogs()
  const deletion = useLogDeletion(removeLog)

  // 카드에 넘기는 함수를 고정한다. 매 렌더마다 새 함수를 만들면
  // memo 로 감싼 카드가 매번 달라진 props 를 받아 다시 그려진다.
  const goEdit = useCallback((item) => navigate(`/logs/${item.id}/edit`), [navigate])

  // 조회 조건은 주소에 있다. 훅에 넘기지 않으므로 바꿔도 요청이 나가지 않는다.
  const { query, tag, sort } = readLogSearchParams(searchParams)
  const [draftQuery, setDraftQuery] = useState(query)

  const patchParams = (patch) => setSearchParams(writeLogSearchParams(searchParams, { query, tag, sort, ...patch }))

  const tagCounts = useMemo(() => getTagCounts(logs), [logs])
  const visibleLogs = useMemo(
    () => sortStudyLogs(filterStudyLogs(logs, { query, tag }), sort),
    [logs, query, tag, sort],
  )

  const hasCondition = Boolean(query || tag)

  function renderBody() {
    if (isLoading) return <LoadingState message="TIL을 불러오는 중입니다." />

    if (error) {
      return (
        <ErrorState
          message="TIL을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
          onRetry={refetch}
        />
      )
    }

    // 아직 하나도 없는 경우와 조건에 맞는 것이 없는 경우는 다른 상황이다.
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

    if (visibleLogs.length === 0) {
      return (
        <EmptyState
          title="조건에 맞는 TIL이 없습니다."
          description="검색어나 태그를 바꿔보세요."
          actionLabel="조건 초기화"
          onAction={() => {
            setDraftQuery('')
            patchParams({ query: '', tag: '' })
          }}
        />
      )
    }

    return (
      <ul className="log-list">
        {visibleLogs.map((log) => (
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
      <PageHeader
        title="학습 목록"
        description="지금까지 기록한 소중한 배움들을 한눈에 확인하고, 언제든지 수정할 수 있어요."
        action={
          <Button variant="primary" onClick={() => navigate('/logs/new')}>
            <PlusIcon />새 TIL 작성
          </Button>
        }
      />

      <div className="toolbar">
        <form
          className="toolbar__search"
          role="search"
          onSubmit={(event) => {
            event.preventDefault()
            patchParams({ query: draftQuery.trim() })
          }}
        >
          <label htmlFor="log-search" className="sr-only">
            TIL 검색
          </label>
          <SearchIcon />
          <input
            id="log-search"
            type="search"
            value={draftQuery}
            placeholder="TIL 제목이나 내용을 검색해보세요."
            onChange={(event) => setDraftQuery(event.target.value)}
          />
        </form>

        <div className="toolbar__row">
          <div className="filter-bar">
            <TagBadge label="전체" selected={!tag} onClick={() => patchParams({ tag: '' })} />
            {tagCounts.map(({ tag: name, count }) => (
              <TagBadge
                key={name}
                tag={name}
                count={count}
                selected={tag.toLowerCase() === name.toLowerCase()}
                onClick={() => patchParams({ tag: name })}
              />
            ))}
          </div>

          <label className="toolbar__sort">
            <span className="sr-only">정렬</span>
            <select
              className="input"
              value={sort}
              onChange={(event) => patchParams({ sort: event.target.value })}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {hasCondition && !isLoading && !error ? (
          <p className="toolbar__result">
            {query ? `“${query}” ` : ''}
            {tag ? `#${tag} ` : ''}
            검색 결과 {visibleLogs.length}건
          </p>
        ) : null}
      </div>

      {mutationError && !deletion.target ? (
        <p className="form__alert" role="alert">
          {mutationError}
        </p>
      ) : null}

      {renderBody()}

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
