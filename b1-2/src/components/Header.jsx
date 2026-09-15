import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ChevronDownIcon, MenuIcon, SearchIcon } from './ui/icons.jsx'
import { buildGlobalSearchPath } from '../lib/studyLogSelectors.js'
import { useAuth } from '../contexts/AuthContext.jsx'

// 자체 검색이 있거나 검색할 대상이 없는 화면에서는 상단 검색을 숨긴다.
// 한 화면에 검색창이 둘이면 어느 쪽이 동작하는지 알기 어렵다.
//
// 정확히 일치하는 경로만 본다. 앞부분으로 비교하면 /logs 하나로
// /logs/new 와 /logs/:id 까지 묶여 버리는데, 그 화면들에는 자체 검색이 없다.
const HIDE_SEARCH_ON = ['/logs', '/tags', '/stats', '/settings']

// 상단 고정 영역. 전역 검색과 사용자 표시를 담당한다.
// 내비게이션 책임은 Sidebar 로 옮겼다.
//
// 검색은 여기서 원격 조회하지 않는다. Header 가 데이터를 조회하면
// 목록 화면과 별개의 요청이 하나 더 생기고, 타이핑마다 요청이 나가게 된다.
// 제출하면 목록 화면으로 이동만 시키고 조회는 그 화면의 훅이 한다.
export default function Header({ onOpenNav }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [term, setTerm] = useState('')
  const { displayName, initials } = useAuth()
  const showSearch = !HIDE_SEARCH_ON.includes(pathname)

  function handleSubmit(event) {
    event.preventDefault()
    navigate(buildGlobalSearchPath(term))
  }

  return (
    <header className="app-header">
      <button
        type="button"
        className="app-header__menu"
        onClick={onOpenNav}
        aria-label="메뉴 열기"
      >
        <MenuIcon />
      </button>

      {showSearch ? (
        <form className="app-header__search" role="search" onSubmit={handleSubmit}>
          <label htmlFor="global-search" className="sr-only">
            학습 기록 검색
          </label>
          <SearchIcon />
          <input
            id="global-search"
            type="search"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="궁금한 내용을 검색해보세요. (예: React, 상태관리, 프로그래밍 …)"
          />
        </form>
      ) : null}

      <button type="button" className="app-header__user" onClick={() => navigate('/settings')}>
        <span className="avatar" aria-hidden="true">
          {initials}
        </span>
        <span className="app-header__user-name">{displayName}</span>
        <ChevronDownIcon />
      </button>
    </header>
  )
}
