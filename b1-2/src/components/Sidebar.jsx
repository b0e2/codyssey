import { NavLink } from 'react-router-dom'
import {
  ChartIcon,
  HomeIcon,
  LeafIcon,
  ListIcon,
  SettingsIcon,
  TagIcon,
} from './ui/icons.jsx'

const NAV_ITEMS = [
  { to: '/', label: '홈', icon: HomeIcon, end: true },
  { to: '/logs', label: '학습 목록', icon: ListIcon },
  { to: '/tags', label: '태그', icon: TagIcon },
  { to: '/stats', label: '통계', icon: ChartIcon },
  { to: '/settings', label: '설정', icon: SettingsIcon },
]

// 앱 전체 고정 내비게이션. prop 없이 항상 같은 항목을 그리므로
// 재사용 컴포넌트 수에 세지 않는다.
export default function Sidebar({ onNavigate }) {
  return (
    <div className="sidebar">
      <NavLink to="/" className="sidebar__brand" onClick={onNavigate}>
        <span className="sidebar__brand-mark">
          TIL
          <LeafIcon size={22} strokeWidth={1.7} />
        </span>
        <span className="sidebar__brand-sub">Today I Learned</span>
      </NavLink>

      <nav className="sidebar__nav" aria-label="주요 메뉴">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              isActive ? 'sidebar__link sidebar__link--active' : 'sidebar__link'
            }
          >
            <Icon />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__foot">
        <LeafIcon size={52} />
        <blockquote className="sidebar__quote">
          &ldquo;작은 배움이
          <br />큰 변화를 만든다.&rdquo;
        </blockquote>
        <p className="sidebar__note">
          오늘도,
          <br />
          조금 더 성장하는 하루가
          <br />
          되길 바라요.
        </p>
      </div>
    </div>
  )
}
