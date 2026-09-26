# TIL — Today I Learned

<p align="center">
  <b>배운 것을 기록하고 회고까지 남기는 학습 기록 서비스</b><br/>
  작성부터 태그 탐색, 학습 통계까지 하나의 흐름으로 설계한 React 단일 페이지 애플리케이션
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/React%20Router-7-CA4245?style=flat-square&logo=reactrouter&logoColor=white" alt="React Router" />
  <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white" alt="Supabase" />
  <img src="https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Vercel" />
</p>

<p align="center">
  <img src="./.github/screenshots/home.png" alt="홈 화면" width="90%" />
</p>

<p align="center">
  <a href="https://b1-2-b0e2s-projects.vercel.app"><b>배포 주소</b></a> ·
  시연 계정 <code>demo@til.local</code> / <code>demo1234!</code>
</p>

---

## Overview

TIL 은 오늘 배운 것을 기록하고, 태그로 모아 보고, 회고와 함께 완료로 남기는 학습 기록 서비스입니다.

`작성 → 태그 탐색 → 학습 통계` 로 이어지는 흐름을 만드는 데 집중했습니다. 화면을 그리는 것보다 **어떤 상태를 어디에 두고 언제 서버에 물을지** 정하는 것이 이 프로젝트의 목적입니다.

## Problem

기록만 쌓아두는 도구에는 아래 한계가 있습니다.

- 적어두기만 하면 다시 열어보지 않게 됨
- 무엇을 얼마나 공부했는지 돌아볼 지표가 없음
- 회고 없이 끝내면 배운 것이 남지 않음

## Solution

- 기록할 때 학습 시간과 이해도를 함께 받아 통계로 쌓음
- 완료로 표시하려면 회고를 요구
- 태그로 어떤 주제에 시간을 썼는지 확인
- 연속 학습 일수와 월별 작성 수로 흐름을 시각화

## Core Features

- 학습 기록 작성 · 조회 · 수정 · 삭제
- 태그 여러 개 입력, 중복과 `#` 자동 정리
- 제목 · 내용 · 회고 · 태그를 아우르는 검색과 정렬
- 태그별 기록 수와 대표 제목 탐색
- 전체 개수 · 연속 학습 일수 · 월별 막대 · 태그 순위
- 회고를 함께 받는 완료 전환
- 이메일 로그인과 사용자별 데이터 격리
- 밝게 / 어둡게 / 시스템 따라가기

## Screens

| 학습 목록 | 통계 |
| --- | --- |
| <img src="./.github/screenshots/logs.png" alt="학습 목록" /> | <img src="./.github/screenshots/stats.png" alt="통계" /> |

| 주소 | 화면 |
| --- | --- |
| `/` | 최근 기록과 바로가기 |
| `/logs` | 목록 · 검색 · 태그 필터 · 정렬 |
| `/logs/new` `/logs/:id/edit` | 작성 · 수정 (같은 폼) |
| `/logs/:id` | 상세 · 완료 전환 · 삭제 |
| `/tags` | 태그별 기록 수와 대표 제목 |
| `/stats` | 개수 · 연속일 · 월별 막대 · 태그 순위 |
| `/settings` | 테마 · 로그아웃 |
| `/login` | 로그인 · 가입 |
| `*` | 정의되지 않은 주소 |

로그인 전에는 `/login` 과 `*` 만 열립니다.

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | `React 19`, `Vite 8` |
| Routing | `React Router 7` |
| Backend | `Supabase` (PostgreSQL · Auth · RLS) |
| Styling | 순수 CSS, CSS 변수 기반 테마 |
| Lint | `oxlint` |
| Deploy | `Vercel` |

상태 관리 라이브러리와 데이터 조회 라이브러리는 쓰지 않았습니다.

```text
src/
├── pages/          화면 10개. 주소 하나에 파일 하나
├── components/
│   ├── ui/         기록을 모르는 공용 컴포넌트 11개
│   └── study-logs/ 기록 객체를 다루는 컴포넌트 4개
├── hooks/          파일 3개 · 훅 4개
├── lib/            연결 · 검증 · 표시 형식 · 검색과 통계 계산
├── contexts/       AuthContext, ThemeContext
└── styles/         tokens → base → layout → ui → study-logs → pages
```

## Data

핵심 데이터는 `study_logs` 한 테이블입니다.

| 컬럼 | 타입 | 제약 |
| --- | --- | --- |
| `id` | uuid | 기본키 |
| `user_id` | uuid | 작성자. 접근 정책의 기준 |
| `title` | text | 공백 제외 2~80자 |
| `tags` | text[] | 1~5개, 빈 값 불가 |
| `study_date` | date | 오늘 이하 |
| `duration_minutes` | integer | 5~720 |
| `understanding` | smallint | 1~5 |
| `content` | text | 공백 제외 10~3000자 |
| `reflection` | text | 완료 상태면 10자 이상 필수 |
| `resource_url` | text | 선택. http(s) 주소 |
| `is_completed` | boolean | 기본 false |
| `created_at` `updated_at` | timestamptz | |

태그는 배열 컬럼에 있고 개수와 순위는 기록에서 계산합니다. 접근 정책은 조회 · 등록 · 수정 · 삭제 네 가지에 `auth.uid() = user_id` 를 겁니다.

## Data Flow

```text
[ 화면 진입 ]
   │  ProtectedRoute 가 세션 확인
   ▼
useStudyLogs() / useStudyLog(id)
   │  1) effect 실행 → Supabase 조회
   │  2) 불러오는 중 · 실패 · 데이터 없음 · 조건 없음 · 성공 판정
   │  3) 화면을 벗어나면 요청 중단
   ▼
[ 사용자 동작 ]
   │  검색 · 태그 · 정렬  → 주소에 저장, 받아온 배열에서 거름 (요청 없음)
   │  완료 · 수정 · 삭제  → Supabase 요청, 성공 응답으로 상태 교체
   ▼
[ 재렌더링 ]
```

## Technical Highlights

| Area | Decision | Impact |
| --- | --- | --- |
| Data Fetching | 네 화면이 `useStudyLogs()` 를 각자 호출, 전역 캐시 없음 | 화면마다 자기 로딩 · 실패 · 다시 시도 상태를 가짐 |
| Search & Filter | 검색어 · 태그 · 정렬을 주소에 두고 클라이언트에서 거름 | 입력할 때마다 요청이 나가지 않고 링크 공유와 뒤로 가기가 동작 |
| Hook Split | 목록과 단건을 생명주기 기준으로 분리 | 의존성 배열이 다른 두 흐름이 섞이지 않음 |
| Validation | 같은 규칙을 `lib` 순수 함수와 테이블 제약 양쪽에 정의 | 화면을 건너뛴 요청도 데이터베이스가 거부 |
| Component Split | `log` 객체를 아는지로 `ui/` 와 `study-logs/` 를 나눔 | `ui/` 는 다른 프로젝트로 그대로 옮길 수 있음 |
| Mutation Order | 삭제와 수정은 서버 응답을 받은 뒤에만 화면 반영 | 실패 시 사라진 행을 되살릴 필요가 없음 |
| Code Splitting | 화면을 지연 로딩하고 라이브러리를 별도 묶음으로 분리 | 앱 코드 12 kB, 화면당 1~5 kB. 배포해도 라이브러리는 재다운로드 없음 |
| Theming | 색을 CSS 변수로 모으고 `data-theme` 속성으로 전환 | 속성 하나로 전 화면 테마 변경 |

## Troubleshooting

| Issue | Approach | Result |
| --- | --- | --- |
| RLS 를 켜고 정책을 비워 조회가 빈 배열로 반환 | 테이블 생성과 정책 생성을 같은 파일에 묶음 | 정책 없는 중간 상태가 생기지 않음 |
| 배열 원소 길이를 `CHECK` 로 검사 불가 (하위 질의 금지) | 전체 길이 상한만 제약으로 두고 원소별 규칙은 검증 계층이 담당 | 제약 위반 없이 규칙 유지 |
| 접근 정책 교체 중 모든 요청 실패 위험 | 주인 지정 → 확인 → 필수 전환 → 정책 교체 순서를 SQL 에 고정, 롤백 SQL 선작성 | 중단 없는 전환과 되돌릴 수 있는 경로 확보 |
| 한글 입력에서 태그가 두 개 생성 | 조합 확정 Enter 를 태그 확정과 분리 | 글자 확정과 태그 확정이 각각 동작 |
| 다크 테마에서 히어로 제목이 보이지 않음 | 배경 색을 토큰으로 옮기고 영역에 `color` 를 선언 | 자식 전체가 상속받아 대비 확보 |
| 배포 시 `vite: command not found` | 배포 브랜치에 코드가 없던 것이 원인, 릴리스 병합 후 재배포 | 빌드 정상화 |

## Running Locally

```bash
npm install

# Supabase 연결 정보 (.env, 커밋하지 않음)
cp .env.example .env
# VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY

npm run dev
```

데이터베이스는 `supabase/schema.sql` 을 SQL Editor 에서 실행해 만듭니다. 변경 이력과 실행 순서는 `supabase/migrations/README.md` 에 있습니다.

```bash
npm run build     # 배포용 빌드
npm run preview   # 빌드 결과 미리보기
npm run lint      # 정적 검사
```

## Roadmap

- 기록 작성 시 이전 태그 자동 완성 강화
- 주간 · 월간 학습 목표 설정
- 기록 내보내기 (Markdown)
- 컴포넌트 · 훅 단위 테스트 범위 확대
