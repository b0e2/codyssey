// eslint-disable react/only-export-components
// 훅과 Provider 를 한 파일에 둔다. 나누면 파일만 늘고 설명할 것이 많아진다.
// 개발 중 이 파일을 고칠 때 화면이 통째로 새로 뜨는 것은 감수한다.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext(null)

export function useTheme() {
  const value = useContext(ThemeContext)
  if (!value) throw new Error('useTheme 은 ThemeProvider 안에서만 쓸 수 있습니다.')
  return value
}

const STORAGE_KEY = 'til-theme'
const PREFERENCES = ['light', 'dark', 'system']

// 브라우저 밖에서도 불릴 수 있다. 검증 스크립트가 화면 없이 컴포넌트를
// 그려보기 때문이다. 없으면 기본값으로 넘어간다.
const media = () =>
  typeof window === 'undefined' ? null : (window.matchMedia?.('(prefers-color-scheme: dark)') ?? null)

function readStored() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return PREFERENCES.includes(stored) ? stored : 'system'
  } catch {
    // 시크릿 모드 등에서 저장소 접근이 막힐 수 있다. 기본값으로 넘어간다.
    return 'system'
  }
}

export function ThemeProvider({ children }) {
  // 초기값을 함수로 넘긴다. 매 렌더마다 저장소를 읽지 않기 위해서다.
  const [preference, setPreference] = useState(readStored)
  const [systemTheme, setSystemTheme] = useState(() => (media()?.matches ? 'dark' : 'light'))

  // 시스템을 고른 경우에만 기기 설정 변화를 따라간다.
  // 구독을 걷지 않으면 화면을 떠난 뒤에도 계속 상태를 바꾸려 한다.
  useEffect(() => {
    const query = media()
    if (!query) return undefined

    const handleChange = (event) => setSystemTheme(event.matches ? 'dark' : 'light')
    query.addEventListener('change', handleChange)
    return () => query.removeEventListener('change', handleChange)
  }, [])

  const resolvedTheme = preference === 'system' ? systemTheme : preference

  // 실제 적용은 토큰을 바꾸는 것뿐이다. 문서에 속성 하나만 세운다.
  useEffect(() => {
    if (typeof document !== 'undefined') document.documentElement.dataset.theme = resolvedTheme
  }, [resolvedTheme])

  const value = useMemo(
    () => ({
      preference,
      resolvedTheme,
      setPreference: (next) => {
        setPreference(next)
        try {
          localStorage.setItem(STORAGE_KEY, next)
        } catch {
          // 저장에 실패해도 이번 방문에는 적용된다.
        }
      },
    }),
    [preference, resolvedTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
