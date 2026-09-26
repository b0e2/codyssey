-- 기록에 주인을 지정하고 접근 정책을 사용자 기준으로 바꾼다.
--
-- 순서가 중요하다. 예전 정책을 먼저 지우면 그 사이 화면의 모든 요청이 실패한다.
-- 주인을 지정하고 → 빠짐없이 지정됐는지 확인하고 → 컬럼을 필수로 바꾸고 →
-- 그다음에 예전 정책을 지운다.
--
-- 되돌리려면 20260911_rollback_to_anon.sql 을 실행한다.

-- ── 실행 전 ──────────────────────────────────────────
-- 1. 로그인할 계정을 앱에서 먼저 만든다.
-- 2. 아래 SQL 로 그 계정의 id 를 확인해 DEMO_USER_ID 자리에 넣는다.
--
--    select id, email from auth.users order by created_at;
--
-- 3. 기존 기록을 CSV 로 내려받아 둔다.

begin;

-- ① 주인 없는 기존 기록을 데모 계정에 붙인다.
update public.study_logs
set user_id = 'DEMO_USER_ID'::uuid
where user_id is null;

-- ② 빠진 것이 없는지 확인한다. 하나라도 남으면 여기서 멈춘다.
do $$
declare
  orphan_count integer;
begin
  select count(*) into orphan_count
  from public.study_logs
  where user_id is null;

  if orphan_count > 0 then
    raise exception '주인이 없는 기록 %건이 남아 있습니다', orphan_count;
  end if;
end
$$;

-- ③ 이제부터는 주인 없는 기록을 만들 수 없다.
alter table public.study_logs
  alter column user_id set not null;

-- ④ 예전 정책을 걷어낸다. 여기서부터 로그인 없이는 아무것도 할 수 없다.
drop policy if exists anon_select_study_logs on public.study_logs;
drop policy if exists anon_insert_study_logs on public.study_logs;
drop policy if exists anon_update_study_logs on public.study_logs;
drop policy if exists anon_delete_study_logs on public.study_logs;

-- ⑤ 사용자 기준 정책을 만든다.
--    with check 가 최종 방어선이다. 화면에서 다른 사람의 id 를 넣어 보내도 거부된다.
create policy auth_select_study_logs
  on public.study_logs for select to authenticated
  using (auth.uid() = user_id);

create policy auth_insert_study_logs
  on public.study_logs for insert to authenticated
  with check (auth.uid() = user_id);

create policy auth_update_study_logs
  on public.study_logs for update to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy auth_delete_study_logs
  on public.study_logs for delete to authenticated
  using (auth.uid() = user_id);

commit;

-- ── 실행 후 확인 ─────────────────────────────────────
-- select count(*) from public.study_logs where user_id is null;   -- 0 이어야 한다
-- select polname from pg_policies where tablename = 'study_logs'; -- auth_ 로 시작하는 4개
