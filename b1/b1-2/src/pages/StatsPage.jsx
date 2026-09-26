import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import StatCard from '../components/ui/StatCard.jsx'
import TagBadge from '../components/ui/TagBadge.jsx'
import { ChartIcon, LeafIcon, ListIcon } from '../components/ui/icons.jsx'
import { useStudyLogs } from '../hooks/useStudyLogs.js'
import { formatDuration, formatMonthLabel, todayString } from '../lib/studyLogFormatters.js'
import {
  calculateOverviewStats,
  getAvailableYears,
  getMonthlyCounts,
  rankTags,
} from '../lib/studyLogSelectors.js'

export default function StatsPage() {
  const navigate = useNavigate()
  const { logs, isLoading, error, refetch } = useStudyLogs()
  const [year, setYear] = useState(null)

  const today = todayString()
  const stats = useMemo(() => calculateOverviewStats(logs, today), [logs, today])
  const years = useMemo(() => getAvailableYears(logs), [logs])
  const activeYear = year ?? years[0] ?? today.slice(0, 4)
  const monthly = useMemo(() => getMonthlyCounts(logs, activeYear), [logs, activeYear])
  const topTags = useMemo(() => rankTags(logs, 5), [logs])

  const maxCount = Math.max(...monthly.map((item) => item.count), 1)

  if (isLoading || error || logs.length === 0) {
    return (
      <>
        <StatsHeader />
        {isLoading ? <LoadingState message="통계를 계산하는 중입니다." /> : null}
        {error ? (
          <ErrorState message="통계를 불러오지 못했습니다." onRetry={refetch} />
        ) : null}
        {/* 기록이 없을 때 0으로 채운 카드와 빈 차트를 보여주면
            데이터가 있는 것처럼 읽힌다. 비어 있음을 그대로 알린다. */}
        {!isLoading && !error ? (
          <EmptyState
            title="아직 통계를 보여드릴 수 없어요."
            description="TIL을 작성하면 학습 현황을 여기에서 확인할 수 있습니다."
            actionLabel="새 TIL 작성"
            onAction={() => navigate('/logs/new')}
          />
        ) : null}
      </>
    )
  }

  return (
    <>
      <StatsHeader />

      <div className="stat-grid">
        <StatCard
          icon={<ListIcon />}
          label="작성한 TIL"
          value={stats.total}
          unit="개"
          description="지금까지 작성한 학습 기록이에요."
        />
        <StatCard
          icon={<LeafIcon size={22} strokeWidth={1.7} />}
          label="연속 학습 일수"
          value={stats.streak}
          unit="일"
          description={stats.streak > 0 ? '꾸준히 이어가고 있어요!' : '오늘 기록을 남겨 이어가보세요.'}
          tone={stats.streak > 0 ? 'accent' : 'default'}
        />
        <StatCard
          icon={<ChartIcon />}
          label="이번 달 작성"
          value={stats.thisMonth}
          unit="개"
          description={`총 학습시간 ${formatDuration(stats.totalMinutes)}`}
        />
      </div>

      <div className="stats-row">
        <section className="detail__card">
          <div className="section__head">
            <div>
              <h2 className="detail__card-title">월별 작성 수</h2>
              <p className="section__description">월별로 작성한 TIL 수를 확인해보세요.</p>
            </div>
            <label>
              <span className="sr-only">연도 선택</span>
              <select
                className="input"
                value={activeYear}
                onChange={(event) => setYear(event.target.value)}
              >
                {years.map((value) => (
                  <option key={value} value={value}>
                    {value}년
                  </option>
                ))}
              </select>
            </label>
          </div>

          {/* 외부 차트 라이브러리를 쓰지 않는다. 막대 열두 개를 그리려고
              의존성을 늘릴 이유가 없다. 화면을 못 읽는 사람을 위해
              같은 숫자를 표로도 제공한다. */}
          <div className="chart" role="img" aria-label={`${activeYear}년 월별 작성 수 막대 그래프`}>
            {monthly.map(({ month, count }) => (
              <div key={month} className="chart__col">
                <span className="chart__value">{count}</span>
                <span
                  className="chart__bar"
                  style={{ height: `${Math.round((count / maxCount) * 100)}%` }}
                />
                <span className="chart__label">{formatMonthLabel(month)}</span>
              </div>
            ))}
          </div>

          <table className="sr-only">
            <caption>{activeYear}년 월별 작성 수</caption>
            <tbody>
              {monthly.map(({ month, count }) => (
                <tr key={month}>
                  <th scope="row">{formatMonthLabel(month)}</th>
                  <td>{count}개</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="detail__card">
          <div>
            <h2 className="detail__card-title">많이 작성한 태그</h2>
            <p className="section__description">자주 다룬 주제를 확인해보세요.</p>
          </div>

          <ol className="rank-list">
            {topTags.map(({ tag, count }, index) => (
              <li key={tag} className="rank-list__item">
                <span className="rank-list__index">{index + 1}</span>
                <TagBadge tag={tag} size="sm" onClick={() => navigate(`/tags?tag=${encodeURIComponent(tag)}`)} />
                <span className="rank-list__count">{count}개</span>
              </li>
            ))}
          </ol>

          <Link to="/tags" className="button button--secondary">
            모든 태그 보기
          </Link>
        </section>
      </div>
    </>
  )
}

function StatsHeader() {
  return <PageHeader title="통계" description="지금까지의 학습 기록을 한눈에 확인해보세요." />
}
