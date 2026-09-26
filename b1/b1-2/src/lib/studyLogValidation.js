// 순수 검증 계층.
// DOM, React, Supabase를 모르고 같은 입력에 항상 같은 결과를 반환한다.
// 훅이 이 결과를 소비할 뿐 판정식을 직접 쓰지 않는다.

export const DURATION_MINUTES_MIN = 5
export const DURATION_MINUTES_MAX = 720
const UNDERSTANDING_MIN = 1
const UNDERSTANDING_MAX = 5
const TAGS_MIN = 1
export const TAGS_MAX = 5
const TAG_LENGTH_MAX = 30

export const STUDY_LOG_INITIAL_VALUES = {
  title: '',
  tags: [],
  study_date: '',
  duration_minutes: '',
  understanding: 3,
  content: '',
  reflection: '',
  resource_url: '',
  is_completed: false,
}

// ── 태그 ─────────────────────────────────────────────

// 사용자는 '#React' 로도 'React' 로도 입력할 수 있지만 저장값은 'React' 다.
export function normalizeTag(value) {
  return String(value ?? '')
    .trim()
    .replace(/^#+/, '')
    .trim()
}

// 'React' 와 'react' 는 같은 태그로 본다. 다만 먼저 입력한 표기를 남긴다.
export function normalizeTags(tags) {
  const seen = new Set()
  const result = []

  for (const raw of tags ?? []) {
    const tag = normalizeTag(raw)
    if (!tag) continue

    const key = tag.toLowerCase()
    if (seen.has(key)) continue

    seen.add(key)
    result.push(tag)
  }

  return result
}

function validateTags(tags) {
  const normalized = normalizeTags(tags)

  if (normalized.length < TAGS_MIN) return '태그를 최소 1개 입력해 주세요.'
  if (normalized.length > TAGS_MAX) return `태그는 최대 ${TAGS_MAX}개까지 넣을 수 있습니다.`

  const tooLong = normalized.find((tag) => tag.length > TAG_LENGTH_MAX)
  if (tooLong) return `태그는 ${TAG_LENGTH_MAX}자 이하로 입력해 주세요.`

  return ''
}

// ── 개별 필드 ────────────────────────────────────────

function validateTitle(value) {
  const title = String(value ?? '').trim()
  if (!title) return '제목을 입력해 주세요.'
  if (title.length < 2) return '제목은 2자 이상 입력해 주세요.'
  if (title.length > 80) return '제목은 80자 이하로 입력해 주세요.'
  return ''
}

// today 를 인자로 받는다. 순수 함수를 유지하면서 '오늘'의 판정을 호출자에게 넘긴다.
function validateStudyDate(value, today) {
  const date = String(value ?? '').trim()
  if (!date) return '학습한 날짜를 선택해 주세요.'
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return '날짜 형식이 올바르지 않습니다.'
  if (today && date > today) return '학습 날짜는 오늘 이후일 수 없습니다.'
  return ''
}

function validateDurationMinutes(value) {
  if (value === '' || value === null || value === undefined) {
    return '학습 시간을 입력해 주세요.'
  }
  const minutes = Number(value)
  if (!Number.isInteger(minutes)) return '학습 시간은 정수로 입력해 주세요.'
  if (minutes < DURATION_MINUTES_MIN || minutes > DURATION_MINUTES_MAX) {
    return `학습 시간은 ${DURATION_MINUTES_MIN}분 이상 ${DURATION_MINUTES_MAX}분 이하로 입력해 주세요.`
  }
  return ''
}

function validateUnderstanding(value) {
  const level = Number(value)
  if (!Number.isInteger(level) || level < UNDERSTANDING_MIN || level > UNDERSTANDING_MAX) {
    return '이해도를 선택해 주세요.'
  }
  return ''
}

function validateContent(value) {
  const content = String(value ?? '').trim()
  if (!content) return '학습한 내용을 입력해 주세요.'
  if (content.length < 10) return '학습 내용은 10자 이상 입력해 주세요.'
  if (content.length > 3000) return '학습 내용은 3000자 이하로 입력해 주세요.'
  return ''
}

// 완료 상태에는 회고가 있어야 한다. 기록과 회고를 함께 남기는 것이 이 서비스의 목적이다.
function validateReflection(value, isCompleted) {
  const reflection = String(value ?? '').trim()

  if (isCompleted) {
    if (!reflection) return '완료로 표시하려면 회고를 입력해 주세요.'
    if (reflection.length < 10) return '회고는 10자 이상 입력해 주세요.'
  }

  if (reflection.length > 2000) return '회고는 2000자 이하로 입력해 주세요.'
  return ''
}

function isValidHttpUrl(value) {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

function validateResourceUrl(value) {
  const url = String(value ?? '').trim()
  if (!url) return ''
  if (url.length > 500) return '링크는 500자 이하로 입력해 주세요.'
  if (!isValidHttpUrl(url)) return 'http:// 또는 https:// 로 시작하는 링크를 입력해 주세요.'
  return ''
}

// ── 전체 ─────────────────────────────────────────────

export function normalizeStudyLogInput(values) {
  return {
    title: String(values.title ?? '').trim(),
    tags: normalizeTags(values.tags),
    study_date: String(values.study_date ?? '').trim(),
    duration_minutes: Number(values.duration_minutes),
    understanding: Number(values.understanding),
    content: String(values.content ?? '').trim(),
    reflection: String(values.reflection ?? '').trim() || null,
    resource_url: String(values.resource_url ?? '').trim() || null,
    is_completed: Boolean(values.is_completed),
  }
}

export function validateStudyLog(values, { today } = {}) {
  const errors = {
    title: validateTitle(values.title),
    tags: validateTags(values.tags),
    study_date: validateStudyDate(values.study_date, today),
    duration_minutes: validateDurationMinutes(values.duration_minutes),
    understanding: validateUnderstanding(values.understanding),
    content: validateContent(values.content),
    reflection: validateReflection(values.reflection, values.is_completed),
    resource_url: validateResourceUrl(values.resource_url),
  }

  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message))
}

// 완료 전환 규칙을 한 곳에 둔다.
// 목록 훅과 상세 훅이 각자 구현하면 회고 조건이 두 곳에 복제된다.
export function buildCompletionPayload(log, reflection) {
  const nextCompleted = !log.is_completed

  if (!nextCompleted) {
    // 완료를 되돌릴 때는 회고를 지우지 않는다. 다시 완료할 때 그대로 쓴다.
    return { payload: { is_completed: false, updated_at: new Date().toISOString() }, error: '' }
  }

  const text = String(reflection ?? log.reflection ?? '').trim()
  const error = validateReflection(text, true)
  if (error) return { payload: null, error }

  return {
    payload: { is_completed: true, reflection: text, updated_at: new Date().toISOString() },
    error: '',
  }
}
