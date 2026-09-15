import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import { SearchIcon } from '../components/ui/icons.jsx'
import { useStudyLogs } from '../hooks/useStudyLogs.js'
import { getTagInitial, getTagTone } from '../lib/studyLogFormatters.js'
import { getTagSummaries } from '../lib/studyLogSelectors.js'

const SORT_OPTIONS = [
  { value: 'count', label: '기록 많은 순' },
  { value: 'name', label: '이름순' },
]

// 태그 화면은 기록 목록을 다시 보여주지 않는다.
// 같은 목록이 두 화면에 있으면 어느 쪽을 봐야 할지 알 수 없다.
// 여기서는 어떤 주제를 얼마나 다뤘는지만 보여주고,
// 실제 기록은 학습 목록으로 넘겨 그 화면의 필터로 본다.
export default function TagsPage() {
  const navigate = useNavigate()
  const { logs, isLoading, error, refetch } = useStudyLogs()
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('count')

  const summaries = useMemo(() => getTagSummaries(logs, { sort }), [logs, sort])
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return needle ? summaries.filter(({ tag }) => tag.toLowerCase().includes(needle)) : summaries
  }, [summaries, query])

  const header = (
    <PageHeader
      title="태그"
      description="태그로 TIL을 탐색해보세요. 관심 있는 주제의 배움을 한눈에 확인할 수 있어요."
    />
  )

  if (isLoading || error || logs.length === 0) {
    return (
      <>
        {header}
        {isLoading ? <LoadingState message="태그를 불러오는 중입니다." /> : null}
        {error ? <ErrorState message="태그를 불러오지 못했습니다." onRetry={refetch} /> : null}
        {!isLoading && !error ? (
          <EmptyState
            title="아직 태그가 없습니다."
            description="TIL을 작성하면 사용한 태그가 여기에 모입니다."
            actionLabel="새 TIL 작성"
            onAction={() => navigate('/logs/new')}
          />
        ) : null}
      </>
    )
  }

  return (
    <>
      {header}

      <form className="toolbar__search tags__search" role="search" onSubmit={(e) => e.preventDefault()}>
        <label htmlFor="tag-search" className="sr-only">
          태그 검색
        </label>
        <SearchIcon />
        <input
          id="tag-search"
          type="search"
          value={query}
          placeholder="태그를 검색해보세요. (예: React, JavaScript, 개발일지 …)"
          onChange={(event) => setQuery(event.target.value)}
        />
      </form>

      <p className="tags__hint">태그를 선택하면 학습 목록에서 해당 주제만 모아볼 수 있어요.</p>

      <div className="section__head">
        <h2 className="section__title section__title--sm">
          내 태그 <span className="tags__count">{summaries.length}개</span>
        </h2>
        <label>
          <span className="sr-only">정렬</span>
          <select className="input" value={sort} onChange={(event) => setSort(event.target.value)}>
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title={`“${query}” 와 맞는 태그가 없습니다.`}
          description="다른 이름으로 찾아보세요."
          actionLabel="검색 초기화"
          onAction={() => setQuery('')}
        />
      ) : (
        <ul className="tag-grid">
          {visible.map(({ tag, count, titles }) => (
            <li key={tag}>
              <article className="tag-card">
                <span className={`log-row__thumb log-row__thumb--${getTagTone(tag)}`} aria-hidden="true">
                  {getTagInitial(tag)}
                </span>

                <div className="tag-card__body">
                  <h3 className="tag-card__name">#{tag}</h3>
                  <p className="tag-card__count">{count}개의 학습 기록</p>
                  <ul className="tag-card__titles">
                    {titles.map((title) => (
                      <li key={title}>{title}</li>
                    ))}
                  </ul>
                </div>

                <button
                  type="button"
                  className="button button--secondary button--sm"
                  onClick={() => navigate(`/logs?tag=${encodeURIComponent(tag)}`)}
                >
                  학습 보기 →
                </button>
              </article>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
