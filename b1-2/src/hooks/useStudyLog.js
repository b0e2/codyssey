import { useCallback, useEffect, useRef, useState } from 'react'
import { STUDY_LOGS_TABLE, supabase } from '../lib/supabaseClient.js'
import { buildCompletionPayload } from '../lib/studyLogValidation.js'

// 기록 한 건의 조회와 변경을 담당한다.
//
// 컬렉션 훅과 생명주기가 다르다. 목록은 화면에 들어올 때 한 번 부르면 되지만
// 여기는 주소의 id 가 바뀔 때마다 다시 불러야 한다. 그래서 훅을 나눈다.
export function useStudyLog(id) {
  const [log, setLog] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isNotFound, setIsNotFound] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [mutationError, setMutationError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const mounted = useRef(true)

  const refetch = useCallback(() => setReloadKey((key) => key + 1), [])

  useEffect(() => {
    mounted.current = true
    const controller = new AbortController()

    async function loadStudyLog() {
      setIsLoading(true)
      setError(null)
      setIsNotFound(false)

      const { data, error: requestError } = await supabase
        .from(STUDY_LOGS_TABLE)
        .select('*')
        .eq('id', id)
        .abortSignal(controller.signal)
        .maybeSingle()

      // id 가 바뀌어 이 요청이 밀려났거나 화면을 벗어난 경우다.
      // 늦게 온 응답이 새 화면의 내용을 덮지 않게 여기서 멈춘다.
      if (!mounted.current || controller.signal.aborted) return

      if (requestError) {
        setError(requestError)
      } else if (!data) {
        // 주소는 올바른데 해당 기록이 없는 경우다.
        // 정의되지 않은 주소를 처리하는 NotFound 화면과 구분한다.
        setIsNotFound(true)
      } else {
        setLog(data)
      }
      setIsLoading(false)
    }

    loadStudyLog()

    return () => {
      mounted.current = false
      controller.abort()
    }
  }, [id, reloadKey])

  const applyUpdate = useCallback(async (payload) => {
    setIsUpdating(true)
    setMutationError('')

    const { data, error: requestError } = await supabase
      .from(STUDY_LOGS_TABLE)
      .update(payload)
      .eq('id', id)
      .select()
      .single()

    if (!mounted.current) return null
    setIsUpdating(false)

    if (requestError) {
      setMutationError('저장하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      return null
    }

    // 서버가 돌려준 행으로 교체한다. 화면의 값과 저장된 값이 갈리지 않게 한다.
    setLog(data)
    return data
  }, [id])

  const updateLog = useCallback(
    (values) => applyUpdate({ ...values, updated_at: new Date().toISOString() }),
    [applyUpdate],
  )

  // 완료 전환 규칙은 lib 의 순수 함수가 갖는다.
  // 목록 훅도 같은 함수를 쓰므로 회고 조건이 두 군데로 갈리지 않는다.
  const toggleComplete = useCallback(
    async (reflection) => {
      if (!log) return null
      const { payload, error: ruleError } = buildCompletionPayload(log, reflection)
      if (ruleError) {
        setMutationError(ruleError)
        return null
      }
      return applyUpdate(payload)
    },
    [log, applyUpdate],
  )

  const removeLog = useCallback(async () => {
    setIsDeleting(true)
    setMutationError('')

    const { error: requestError } = await supabase.from(STUDY_LOGS_TABLE).delete().eq('id', id)

    if (!mounted.current) return false
    setIsDeleting(false)

    if (requestError) {
      // 서버에서 지워지지 않았는데 화면에서 먼저 사라지지 않게 한다.
      setMutationError('삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.')
      return false
    }
    return true
  }, [id])

  return {
    log,
    isLoading,
    error,
    isNotFound,
    isUpdating,
    isDeleting,
    mutationError,
    refetch,
    updateLog,
    toggleComplete,
    removeLog,
  }
}

// 등록만 담당한다. 조회와 생명주기가 달라 위 훅과 나눈다.
// 조회 effect 가 없고 성공 직후 화면을 떠나므로 마운트 여부만 추적한다.
export function useCreateStudyLog() {
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState(null)
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const clearCreateError = useCallback(() => setCreateError(null), [])

  // 주인은 화면 입력값에서 받지 않는다. 지금 로그인한 사용자로 정한다.
  // 화면을 조작해 다른 사람의 id 를 보내더라도 접근 정책이 거부한다.
  const createLog = useCallback(async (values) => {
    const { data: auth } = await supabase.auth.getUser()
    if (mounted.current) {
      setIsCreating(true)
      setCreateError(null)
    }

    const { data, error } = await supabase
      .from(STUDY_LOGS_TABLE)
      .insert({ ...values, user_id: auth?.user?.id ?? null })
      .select()
      .single()

    if (mounted.current) setIsCreating(false)

    if (error) {
      if (mounted.current) setCreateError(error)
      throw new Error('저장하지 못했습니다. 입력값을 확인하고 다시 시도해 주세요.')
    }

    return data
  }, [])

  return { createLog, isCreating, createError, clearCreateError }
}
