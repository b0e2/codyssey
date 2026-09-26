// eslint-disable react/only-export-components
// 훅과 Provider 를 한 파일에 둔다. 나누면 파일만 늘고 설명할 것이 많아진다.
// 개발 중 이 파일을 고칠 때 화면이 통째로 새로 뜨는 것은 감수한다.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabaseClient.js'

const AuthContext = createContext(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth 는 AuthProvider 안에서만 쓸 수 있습니다.')
  return value
}

function initialsOf(name, email) {
  const source = String(name ?? '').trim() || String(email ?? '').trim()
  if (!source) return '?'
  return /^[a-zA-Z]/.test(source) ? source.slice(0, 2).toUpperCase() : source.slice(0, 1)
}

// 로그인한 사용자만 담는다. 기록 목록은 여기 넣지 않는다.
// 넣는 순간 화면마다 갖고 있던 불러오는 중과 실패 상태가 하나로 합쳐진다.
export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [isAuthLoading, setIsAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')

  // 마운트할 때 한 번만 실행한다. 지금 세션을 확인하고 이후 변화를 구독한다.
  // 로그인, 로그아웃, 토큰 갱신이 모두 이 구독으로 들어온다.
  useEffect(() => {
    let active = true

    supabase.auth.getSession().then(({ data }) => {
      if (!active) return
      setSession(data.session)
      setIsAuthLoading(false)
    })

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) return
      setSession(nextSession)
      setIsAuthLoading(false)
    })

    return () => {
      active = false
      subscription.subscription.unsubscribe()
    }
  }, [])

  const value = useMemo(() => {
    const user = session?.user ?? null
    const displayName = user?.user_metadata?.display_name || user?.email?.split('@')[0] || ''

    async function signIn(email, password) {
      setAuthError('')
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) {
        setAuthError('이메일 또는 비밀번호를 확인해 주세요.')
        return false
      }
      return true
    }

    async function signUp(email, password, name) {
      setAuthError('')
      const { error } = await supabase.auth.signUp({
        email,
        password,
        // 표시할 이름은 가입할 때 한 번 저장한다.
        // 프로필 테이블을 따로 만들지 않기 위해서다.
        options: { data: { display_name: name } },
      })
      if (error) {
        setAuthError(
          error.message?.includes('already')
            ? '이미 가입된 이메일입니다.'
            : '가입하지 못했습니다. 잠시 후 다시 시도해 주세요.',
        )
        return false
      }
      return true
    }

    async function signOut() {
      await supabase.auth.signOut()
    }

    return {
      user,
      session,
      displayName,
      initials: initialsOf(displayName, user?.email),
      isAuthLoading,
      authError,
      clearAuthError: () => setAuthError(''),
      signIn,
      signUp,
      signOut,
    }
  }, [session, isAuthLoading, authError])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
