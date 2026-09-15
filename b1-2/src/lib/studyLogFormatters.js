// 오늘 날짜를 로컬 기준으로 만든다.
// toISOString 은 UTC 라 자정 전후에 하루가 어긋난다.
export function todayString() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

const UNDERSTANDING_LABELS = {
  1: '거의 이해 못함',
  2: '조금 이해함',
  3: '보통',
  4: '잘 이해함',
  5: '설명할 수 있음',
}

export function formatStudyDate(value, locale = 'ko-KR') {
  if (!value) return ''
  // study_date 는 date 타입이라 시간대 변환 없이 문자열 그대로 다룬다.
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatDateTime(value, locale = 'ko-KR') {
  if (!value) return ''
  return new Date(value).toLocaleString(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function formatDuration(minutes) {
  const total = Number(minutes)
  if (!Number.isFinite(total)) return ''
  const hours = Math.floor(total / 60)
  const rest = total % 60
  if (hours && rest) return `${hours}시간 ${rest}분`
  if (hours) return `${hours}시간`
  return `${rest}분`
}

export function formatUnderstanding(value) {
  return UNDERSTANDING_LABELS[value] ?? '-'
}

export function formatCompletionStatus(isCompleted) {
  return isCompleted ? '완료' : '진행 중'
}

// ── 태그 ─────────────────────────────────────────────

// 저장값은 'React' 지만 화면에는 '#React' 로 보여준다.
export function formatTag(tag) {
  return `#${tag}`
}

export function getTagInitial(tag) {
  const text = String(tag ?? '').trim()
  if (!text) return '?'
  // 영문은 두 글자, 그 외(한글 등)는 한 글자가 자연스럽다.
  return /^[a-zA-Z]/.test(text) ? text.slice(0, 2).toUpperCase() : text.slice(0, 1)
}

const TAG_TONES = ['olive', 'sage', 'moss', 'clay', 'sand']

// 같은 태그는 언제나 같은 색을 얻는다.
// 목록에서 태그를 색으로 구분할 수 있게 하되 DB 에 색을 저장하지 않는다.
export function getTagTone(tag) {
  const text = String(tag ?? '')
  let hash = 0
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) % 100000
  }
  return TAG_TONES[hash % TAG_TONES.length]
}

export function formatMonthLabel(monthIndex) {
  return `${monthIndex + 1}월`
}
