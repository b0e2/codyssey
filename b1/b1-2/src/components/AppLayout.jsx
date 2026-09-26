import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header.jsx'
import Sidebar from './Sidebar.jsx'

export default function AppLayout() {
  // 좁은 화면에서만 쓰는 서랍 상태다. 넓은 화면에서는 사이드바가 항상 보인다.
  const [isNavOpen, setIsNavOpen] = useState(false)
  const closeNav = () => setIsNavOpen(false)

  return (
    <div className="app-shell">
      <aside className={isNavOpen ? 'app-sidebar app-sidebar--open' : 'app-sidebar'}>
        {/* 이동을 일으킨 클릭에서 바로 닫는다. 경로 변경을 effect 로 감시하지 않는다. */}
        <Sidebar onNavigate={closeNav} />
      </aside>

      {isNavOpen ? (
        <button type="button" className="app-scrim" aria-label="메뉴 닫기" onClick={closeNav} />
      ) : null}

      <div className="app-body">
        <Header onOpenNav={() => setIsNavOpen(true)} />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
