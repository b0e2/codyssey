import { Link } from 'react-router-dom'

// 정의되지 않은 URL을 처리한다.
// 정상 상세 URL인데 데이터가 없는 경우는 상세 화면이 EmptyState로 따로 처리한다.
export default function NotFoundPage() {
  return (
    <main className="app-main app-main--narrow">
      <div className="state state--empty">
        <p className="state__title">페이지를 찾을 수 없습니다.</p>
        <p className="state__message">주소를 다시 확인해 주세요.</p>
        <div className="not-found__links">
          <Link to="/" className="link">
            대시보드
          </Link>
          <Link to="/logs" className="link">
            학습 기록
          </Link>
        </div>
      </div>
    </main>
  )
}
