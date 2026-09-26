import { useCallback, useRef, useState } from 'react'
import { todayString } from '../lib/studyLogFormatters.js'
import { normalizeStudyLogInput, validateStudyLog } from '../lib/studyLogValidation.js'

// 폼의 입력 상태와 제출 흐름만 담당한다.
// 값이 유효한지 판정하는 규칙은 lib 의 순수 함수가 갖는다.
//
// effect 가 없다. 수정 화면은 원격 데이터가 준비된 뒤에 폼을 마운트하므로
// 비동기로 도착한 초기값을 effect 로 복사할 일이 없다.
export function useStudyLogForm({ initialValues, onSubmit }) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const mounted = useRef(true)

  const today = todayString()

  const setFieldValue = useCallback((name, value) => {
    setValues((current) => ({ ...current, [name]: value }))
  }, [])

  const handleChange = useCallback((event) => {
    const { name, type, value, checked } = event.target
    setFieldValue(name, type === 'checkbox' ? checked : value)
  }, [setFieldValue])

  // 입력을 벗어날 때와 제출할 때 같은 검증 함수를 쓴다.
  const handleBlur = useCallback((event) => {
    const { name } = event.target
    setTouched((current) => ({ ...current, [name]: true }))
    setValues((current) => {
      setErrors(validateStudyLog(current, { today }))
      return current
    })
  }, [today])

  const handleTagsChange = useCallback((tags) => {
    setFieldValue('tags', tags)
  }, [setFieldValue])

  async function handleSubmit(event) {
    event.preventDefault()
    if (isSubmitting) return // 연속 클릭이 두 번째 요청을 만들지 않게 한다.

    const nextErrors = validateStudyLog(values, { today })
    setErrors(nextErrors)
    setTouched(Object.fromEntries(Object.keys(values).map((key) => [key, true])))

    if (Object.keys(nextErrors).length > 0) {
      const [firstField] = Object.keys(nextErrors)
      document.getElementById(firstField)?.focus()
      return
    }

    setIsSubmitting(true)
    setSubmitError('')

    try {
      await onSubmit(normalizeStudyLogInput(values))
    } catch (error) {
      // 실패해도 입력값은 그대로 둔다. 다시 쓰게 만들지 않는다.
      if (mounted.current) setSubmitError(error?.message || '저장에 실패했습니다. 잠시 후 다시 시도해 주세요.')
    } finally {
      if (mounted.current) setIsSubmitting(false)
    }
  }

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    today,
    setFieldValue,
    handleChange,
    handleBlur,
    handleTagsChange,
    handleSubmit,
  }
}
