import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button.jsx'
import { TextField } from '../components/ui/FormField.jsx'
import { LeafIcon } from '../components/ui/icons.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'

const MIN_PASSWORD = 6

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthLoading, authError, clearAuthError, signIn, signUp } = useAuth()

  const [mode, setMode] = useState('signin')
  const [values, setValues] = useState({ name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [notice, setNotice] = useState('')

  const from = location.state?.from?.pathname ?? '/'
  const isSignUp = mode === 'signup'

  // 이미 로그인한 사람이 주소로 직접 들어온 경우다.
  if (!isAuthLoading && user) return <Navigate to={from} replace />

  function validate() {
    const next = {}
    if (isSignUp && !values.name.trim()) next.name = '표시할 이름을 입력해 주세요.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) next.email = '이메일 형식을 확인해 주세요.'
    if (values.password.length < MIN_PASSWORD) {
      next.password = `비밀번호는 ${MIN_PASSWORD}자 이상 입력해 주세요.`
    }
    return next
  }

  function handleChange(event) {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (isSubmitting) return

    const nextErrors = validate()
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      document.getElementById(Object.keys(nextErrors)[0])?.focus()
      return
    }

    setIsSubmitting(true)
    setNotice('')

    const ok = isSignUp
      ? await signUp(values.email, values.password, values.name.trim())
      : await signIn(values.email, values.password)

    setIsSubmitting(false)

    if (!ok) return

    if (isSignUp) {
      // 이메일 확인이 켜져 있으면 가입 직후 세션이 없다.
      // 바로 이동시키면 다시 로그인 화면으로 튕겨 혼란스럽다.
      setNotice('가입이 완료되었습니다. 이제 로그인해 주세요.')
      setMode('signin')
      setValues((current) => ({ ...current, password: '' }))
      return
    }

    navigate(from, { replace: true })
  }

  function switchMode(next) {
    setMode(next)
    setErrors({})
    setNotice('')
    clearAuthError()
  }

  return (
    <main className="auth">
      <div className="auth__card">
        <div className="auth__brand">
          <span className="auth__logo">
            TIL
            <LeafIcon size={22} strokeWidth={1.7} />
          </span>
          <p className="auth__sub">Today I Learned</p>
        </div>

        <h1 className="auth__title">{isSignUp ? '계정 만들기' : '다시 만나 반가워요'}</h1>
        <p className="auth__description">
          {isSignUp ? '기록을 계정에 안전하게 보관합니다.' : '오늘의 배움을 이어가볼까요?'}
        </p>

        {notice ? <p className="auth__notice">{notice}</p> : null}
        {authError ? (
          <p className="form__alert" role="alert">
            {authError}
          </p>
        ) : null}

        <form className="auth__form" onSubmit={handleSubmit} noValidate>
          {isSignUp ? (
            <TextField
              name="name"
              label="표시할 이름"
              required
              value={values.name}
              error={errors.name}
              maxLength={20}
              autoComplete="nickname"
              onChange={handleChange}
            />
          ) : null}

          <TextField
            name="email"
            label="이메일"
            required
            type="email"
            value={values.email}
            error={errors.email}
            autoComplete="email"
            onChange={handleChange}
          />

          <TextField
            name="password"
            label="비밀번호"
            required
            type="password"
            value={values.password}
            error={errors.password}
            hint={isSignUp ? `${MIN_PASSWORD}자 이상 입력해 주세요.` : undefined}
            autoComplete={isSignUp ? 'new-password' : 'current-password'}
            onChange={handleChange}
          />

          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            loadingLabel={isSignUp ? '가입 중' : '로그인 중'}
          >
            {isSignUp ? '가입하기' : '로그인'}
          </Button>
        </form>

        <p className="auth__switch">
          {isSignUp ? '이미 계정이 있나요?' : '아직 계정이 없나요?'}{' '}
          <button type="button" className="link" onClick={() => switchMode(isSignUp ? 'signin' : 'signup')}>
            {isSignUp ? '로그인' : '가입하기'}
          </button>
        </p>
      </div>
    </main>
  )
}
