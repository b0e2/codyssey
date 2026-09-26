-- 목록 화면 확인용 샘플 데이터.
-- 모든 제약을 통과하도록 content 는 10자 이상, 완료 행은 회고 10자 이상으로 둔다.

insert into public.study_logs
  (title, tags, study_date, duration_minutes, understanding, content, reflection, resource_url, is_completed)
values
  ('useEffect 의존성 배열 정리', array['React','훅'], current_date - 2, 90, 4,
   '의존성 배열이 비어 있을 때와 값이 들어갈 때 effect 가 언제 다시 실행되는지 정리했다.',
   '필터 상태를 의존성에 넣으면 입력할 때마다 요청이 나간다는 것을 확인했다.',
   'https://react.dev/reference/react/useEffect', true),

  ('PostgreSQL 제약조건', array['Database','CS'], current_date - 1, 60, 3,
   'check 제약으로 값의 범위와 조건부 필수 규칙을 어디까지 표현할 수 있는지 확인했다.',
   null, null, false),

  ('React Router 중첩 라우트', array['React','라우팅'], current_date, 45, 5,
   '레이아웃 라우트와 Outlet 으로 공통 헤더를 적용하는 구조를 익혔다.',
   null, null, false);
