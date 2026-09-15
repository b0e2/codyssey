import { useState } from 'react'
import ConfirmDialog from '../components/ui/ConfirmDialog.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Button from '../components/ui/Button.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { useTheme } from '../contexts/ThemeContext.jsx'

const THEME_OPTIONS = [
  { value: 'light', label: '라이트', description: '밝고 편안한 분위기' },
  { value: 'dark', label: '다크', description: '눈이 편안한 어두운 테마' },
  { value: 'system', label: '시스템', description: '기기 설정에 따라 자동으로 변경' },
]

export default function SettingsPage() {
  const { displayName, initials, user, signOut } = useAuth()
  const { preference, setPreference } = useTheme()
  const [confirming, setConfirming] = useState(false)

  return (
    <>
      <PageHeader title="설정" description="나만의 학습 환경을 더 편안하게 만들어보세요." />

      <section className="detail__card">
        <h2 className="detail__card-title">화면 설정</h2>
        <p className="section__description">앱의 테마를 선택하세요. 언제든지 변경할 수 있습니다.</p>

        <fieldset className="theme-options">
          <legend className="sr-only">테마 선택</legend>
          {THEME_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={preference === option.value ? 'theme-option theme-option--on' : 'theme-option'}
            >
              <input
                type="radio"
                name="theme"
                value={option.value}
                checked={preference === option.value}
                onChange={() => setPreference(option.value)}
              />
              <span className="theme-option__label">{option.label}</span>
              <span className="theme-option__description">{option.description}</span>
            </label>
          ))}
        </fieldset>

        <p className="section__description">테마 변경은 즉시 반영됩니다.</p>
      </section>

      <section className="detail__card">
        <h2 className="detail__card-title">계정 관리</h2>

        <div className="account-row">
          <span className="avatar" aria-hidden="true">
            {initials}
          </span>
          <div>
            <p className="account-row__name">{displayName}</p>
            <p className="account-row__email">{user?.email}</p>
          </div>
          <Button variant="danger" onClick={() => setConfirming(true)}>
            로그아웃
          </Button>
        </div>
      </section>

      <ConfirmDialog
        open={confirming}
        title="로그아웃할까요?"
        description="다시 이용하려면 로그인이 필요합니다."
        confirmLabel="로그아웃"
        onCancel={() => setConfirming(false)}
        onConfirm={signOut}
      />
    </>
  )
}
