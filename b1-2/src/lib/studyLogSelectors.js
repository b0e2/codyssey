// 원본 목록에서 화면에 보여줄 값을 계산한다.
// React 를 모르는 순수 함수라 서버에 다시 묻지 않고 화면만 다시 그린다.

function matchesQuery(log, query) {
  if (!query) return true
  const needle = query.toLowerCase()

  return (
    log.title?.toLowerCase().includes(needle) ||
    log.content?.toLowerCase().includes(needle) ||
    log.reflection?.toLowerCase().includes(needle) ||
    (log.tags ?? []).some((tag) => tag.toLowerCase().includes(needle))
  )
}

function matchesTag(log, tag) {
  if (!tag) return true
  const needle = tag.toLowerCase()
  return (log.tags ?? []).some((item) => item.toLowerCase() === needle)
}

export function filterStudyLogs(logs, { query = '', tag = '' } = {}) {
  return logs.filter((log) => matchesQuery(log, query) && matchesTag(log, tag))
}

// 원본 배열을 건드리지 않는다. 정렬 때문에 원본 순서가 바뀌면
// 다른 화면이 기대하는 순서까지 흔들린다.
export function sortStudyLogs(logs, sortOption) {
  const copy = [...logs]

  switch (sortOption) {
    case 'oldest':
      return copy.sort((a, b) => a.study_date.localeCompare(b.study_date))
    case 'longest':
      return copy.sort((a, b) => b.duration_minutes - a.duration_minutes)
    case 'understanding':
      return copy.sort((a, b) => b.understanding - a.understanding)
    default:
      return copy.sort((a, b) => b.study_date.localeCompare(a.study_date))
  }
}

// 대소문자가 다른 같은 태그를 하나로 센다. 표기는 처음 본 것을 남긴다.
export function getTagCounts(logs) {
  const counts = new Map()

  for (const log of logs) {
    for (const tag of log.tags ?? []) {
      const key = tag.toLowerCase()
      const entry = counts.get(key) ?? { tag, count: 0 }
      entry.count += 1
      counts.set(key, entry)
    }
  }

  return [...counts.values()].sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag))
}

// 태그 하나당 개수와 대표 기록 제목을 묶어 돌려준다.
// 태그 화면이 기록 목록을 그대로 또 보여줄 필요 없이
// 어떤 주제를 얼마나 다뤘는지만 보여주면 되기 때문이다.
export function getTagSummaries(logs, { sort = 'count', preview = 2 } = {}) {
  const counts = getTagCounts(logs)

  const summaries = counts.map(({ tag, count }) => ({
    tag,
    count,
    titles: sortStudyLogs(selectLogsByTag(logs, tag), 'recent')
      .slice(0, preview)
      .map((log) => log.title),
  }))

  return sort === 'name'
    ? summaries.sort((a, b) => a.tag.localeCompare(b.tag))
    : summaries
}

function selectLogsByTag(logs, tag) {
  const needle = tag.toLowerCase()
  return logs.filter((log) => (log.tags ?? []).some((item) => item.toLowerCase() === needle))
}

export function selectRecentLogs(logs, limit = 5) {
  return sortStudyLogs(logs, 'recent').slice(0, limit)
}

// ── 통계 ─────────────────────────────────────────────

function toDateKey(value) {
  return String(value ?? '').slice(0, 10)
}

function shiftDays(dateKey, days) {
  const [y, m, d] = dateKey.split('-').map(Number)
  const date = new Date(y, m - 1, d + days)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

// 기록한 날이 아니라 학습한 날을 센다.
// 주말에 몰아서 적더라도 학습한 날짜가 이어지면 연속으로 본다.
//
// 오늘 아직 안 썼을 수 있으므로 어제부터 시작하는 경우도 연속으로 인정한다.
// 그러지 않으면 매일 자정에 기록이 끊긴 것처럼 보인다.
function calculateStudyStreak(logs, today) {
  const days = new Set(logs.map((log) => toDateKey(log.study_date)))
  if (days.size === 0) return 0

  let cursor = days.has(today) ? today : shiftDays(today, -1)
  if (!days.has(cursor)) return 0

  let streak = 0
  while (days.has(cursor)) {
    streak += 1
    cursor = shiftDays(cursor, -1)
  }
  return streak
}

export function calculateOverviewStats(logs, today) {
  const month = today.slice(0, 7)

  return {
    total: logs.length,
    streak: calculateStudyStreak(logs, today),
    thisMonth: logs.filter((log) => toDateKey(log.study_date).startsWith(month)).length,
    totalMinutes: logs.reduce((sum, log) => sum + (log.duration_minutes ?? 0), 0),
  }
}

export function getAvailableYears(logs) {
  const years = new Set(logs.map((log) => toDateKey(log.study_date).slice(0, 4)))
  return [...years].sort((a, b) => b.localeCompare(a))
}

// 기록이 없는 달도 0으로 남긴다. 있는 달만 그리면 축이 들쭉날쭉해
// 어느 달이 비었는지 읽히지 않는다.
export function getMonthlyCounts(logs, year) {
  const counts = Array.from({ length: 12 }, (_, index) => ({ month: index, count: 0 }))

  for (const log of logs) {
    const key = toDateKey(log.study_date)
    if (key.slice(0, 4) !== String(year)) continue
    const monthIndex = Number(key.slice(5, 7)) - 1
    if (counts[monthIndex]) counts[monthIndex].count += 1
  }

  return counts
}

export function rankTags(logs, limit = 5) {
  return getTagCounts(logs).slice(0, limit)
}

// 목록 화면의 조회 조건을 주소에서 읽고 쓴다.
// 헤더와 목록이 각자 규칙을 만들면 파라미터 이름이 갈리므로 여기 모은다.
//
// 이 값들은 화면 안에서만 쓰인다. 원격 조회의 의존성에 들어가지 않으므로
// 검색어를 한 글자 칠 때마다 요청이 나가지 않는다.

export const SORT_OPTIONS = [
  { value: 'recent', label: '최신순' },
  { value: 'oldest', label: '오래된순' },
  { value: 'longest', label: '학습시간 순' },
  { value: 'understanding', label: '이해도 순' },
]

const DEFAULT_SORT = 'recent'

export function readLogSearchParams(searchParams) {
  const sort = searchParams.get('sort')

  return {
    query: searchParams.get('q') ?? '',
    tag: searchParams.get('tag') ?? '',
    sort: SORT_OPTIONS.some((option) => option.value === sort) ? sort : DEFAULT_SORT,
  }
}

// 기본값은 주소에 남기지 않는다. 빈 파라미터가 붙은 주소는 공유하기 나쁘다.
export function writeLogSearchParams(current, patch) {
  const next = new URLSearchParams(current)

  const entries = {
    q: patch.query,
    tag: patch.tag,
    sort: patch.sort === DEFAULT_SORT ? '' : patch.sort,
  }

  for (const [key, value] of Object.entries(entries)) {
    if (value === undefined) continue
    if (value) next.set(key, value)
    else next.delete(key)
  }

  return next
}

export function buildGlobalSearchPath(query) {
  const trimmed = String(query ?? '').trim()
  return trimmed ? `/logs?q=${encodeURIComponent(trimmed)}` : '/logs'
}
