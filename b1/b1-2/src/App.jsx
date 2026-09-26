import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import AppLayout from './components/AppLayout.jsx'
import LoadingState from './components/ui/LoadingState.jsx'
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'

// 화면은 필요할 때 받아온다.
// 통계나 설정처럼 처음에 열지 않는 화면까지 한 덩어리로 받으면
// 첫 화면이 뜨는 데 필요 없는 코드를 기다리게 된다.
const DashboardPage = lazy(() => import('./pages/DashboardPage.jsx'))
const StudyLogsPage = lazy(() => import('./pages/StudyLogsPage.jsx'))
const NewStudyLogPage = lazy(() => import('./pages/NewStudyLogPage.jsx'))
const StudyLogDetailPage = lazy(() => import('./pages/StudyLogDetailPage.jsx'))
const EditStudyLogPage = lazy(() => import('./pages/EditStudyLogPage.jsx'))
const TagsPage = lazy(() => import('./pages/TagsPage.jsx'))
const StatsPage = lazy(() => import('./pages/StatsPage.jsx'))
const SettingsPage = lazy(() => import('./pages/SettingsPage.jsx'))
const LoginPage = lazy(() => import('./pages/LoginPage.jsx'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage.jsx'))

function ProtectedRoute() {
  const { user, isAuthLoading } = useAuth()
  const location = useLocation()

  // 세션을 확인하는 동안 로그인 화면으로 보내면, 이미 로그인한 사람이
  // 새로고침할 때마다 로그인 화면이 한 번 깜빡인다.
  if (isAuthLoading) return <LoadingState message="확인하는 중입니다." />

  // 가려던 곳을 들고 간다. 로그인에 성공하면 그리로 돌려보낸다.
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />

  return <Outlet />
}

// 공통 레이아웃 안쪽에는 사이드바가 필요한 화면만 둔다.
// 로그인과 NotFound 는 단독으로 보여야 하므로 바깥에 둔다.
// 기록을 다루는 화면은 모두 로그인이 필요하다.
export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Suspense fallback={<LoadingState message="불러오는 중입니다." />}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/logs" element={<StudyLogsPage />} />
                <Route path="/logs/new" element={<NewStudyLogPage />} />
                <Route path="/logs/:id" element={<StudyLogDetailPage />} />
                <Route path="/logs/:id/edit" element={<EditStudyLogPage />} />
                <Route path="/tags" element={<TagsPage />} />
                <Route path="/stats" element={<StatsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </ThemeProvider>
  )
}
