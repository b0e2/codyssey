-- study_logs 스키마와 1단계 RLS 정책
-- Supabase 대시보드 > SQL Editor 에 붙여넣어 실행한다.
--
-- 1단계는 로그인 없이 anon 키로 CRUD 하는 단계다.
-- RLS를 켜면서 정책을 만들지 않으면 조회가 오류 없이 빈 배열로 돌아와
-- "데이터가 없음"으로 오진하게 되므로, 활성화와 정책 생성을 함께 수행한다.

create table if not exists public.study_logs (
  id               uuid        primary key default gen_random_uuid(),

  -- 로그인은 이후 단계에서 붙이지만, 나중에 컬럼을 추가하면 기존 행을
  -- 이관해야 하므로 처음부터 만들어 둔다.
  user_id          uuid        references auth.users (id) on delete cascade,

  title            text        not null,
  tags             text[]      not null,
  study_date       date        not null,
  duration_minutes integer     not null,
  understanding    smallint    not null,
  content          text        not null,
  reflection       text,
  resource_url     text,
  is_completed     boolean     not null default false,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),

  -- 태그는 별도 테이블로 분리하지 않는다. 핵심 데이터가 하나라는 조건을 지키고,
  -- 인기 태그 집계와 태그별 목록은 클라이언트에서 계산한다.

  -- 공백만 저장되는 것을 막기 위해 양끝 공백을 제거한 길이로 검사한다.
  constraint study_logs_title_length
    check (char_length(btrim(title)) between 2 and 80),
  constraint study_logs_tags_count
    check (cardinality(tags) between 1 and 5),
  constraint study_logs_tags_no_null
    check (array_position(tags, null) is null),
  constraint study_logs_tags_no_empty
    check (array_position(tags, '') is null),
  -- CHECK 제약에는 서브쿼리를 쓸 수 없어 원소별 길이를 직접 검사하지 못한다.
  -- 전체 길이로 상한만 두고 원소별 30자 규칙은 애플리케이션이 담당한다.
  constraint study_logs_tags_total_length
    check (char_length(array_to_string(tags, ',')) <= 160),
  constraint study_logs_content_length
    check (char_length(btrim(content)) between 10 and 3000),

  constraint study_logs_duration_range
    check (duration_minutes between 5 and 720),
  constraint study_logs_understanding_range
    check (understanding between 1 and 5),

  constraint study_logs_reflection_length
    check (reflection is null or char_length(btrim(reflection)) <= 2000),

  -- 완료 상태에는 회고가 있어야 한다. 학습 기록과 회고를 함께 남기는 것이
  -- 이 서비스의 목적이므로 조건부 필수 규칙을 DB에도 둔다.
  constraint study_logs_completed_requires_reflection
    check (
      is_completed = false
      or (reflection is not null and char_length(btrim(reflection)) >= 10)
    ),

  constraint study_logs_resource_url_format
    check (
      resource_url is null
      or (
        char_length(resource_url) <= 500
        and (resource_url like 'http://%' or resource_url like 'https://%')
      )
    )
);

-- 목록 기본 정렬용
create index if not exists study_logs_study_date_idx
  on public.study_logs (study_date desc, created_at desc);

-- 로그인 도입 후 사용자별 조회용
create index if not exists study_logs_user_id_study_date_idx
  on public.study_logs (user_id, study_date desc);

alter table public.study_logs enable row level security;

-- 1단계 정책. 로그인 전이므로 user_id 가 비어 있는 행만 다룬다.
drop policy if exists anon_select_study_logs on public.study_logs;
create policy anon_select_study_logs
  on public.study_logs for select to anon
  using (true);

drop policy if exists anon_insert_study_logs on public.study_logs;
create policy anon_insert_study_logs
  on public.study_logs for insert to anon
  with check (user_id is null);

drop policy if exists anon_update_study_logs on public.study_logs;
create policy anon_update_study_logs
  on public.study_logs for update to anon
  using (user_id is null)
  with check (user_id is null);

drop policy if exists anon_delete_study_logs on public.study_logs;
create policy anon_delete_study_logs
  on public.study_logs for delete to anon
  using (user_id is null);
