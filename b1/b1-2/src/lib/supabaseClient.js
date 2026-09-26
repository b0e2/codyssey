import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Vite는 VITE_ 접두사가 붙은 값만 클라이언트 번들에 넣는다.
// 이름을 잘못 쓰면 undefined 가 되어 배포 환경에서만 조용히 실패하므로
// 앱을 띄우는 시점에 바로 알 수 있도록 여기서 막는다.
if (!url || !anonKey) {
  throw new Error(
    'Supabase 환경변수가 없습니다. .env 에 VITE_SUPABASE_URL 과 VITE_SUPABASE_ANON_KEY 를 설정하세요.',
  )
}

export const supabase = createClient(url, anonKey)

export const STUDY_LOGS_TABLE = 'study_logs'
