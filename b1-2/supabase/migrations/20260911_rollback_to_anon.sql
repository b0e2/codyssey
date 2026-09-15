-- 20260911_user_scoped_rls.sql 을 되돌린다.
-- 인증 작업을 중간에 포기하고 로그인 없이 쓰던 상태로 복귀할 때 쓴다.
--
-- 인증을 붙이기 전에 이 파일을 먼저 만들어 둔다.
-- 접근 정책과 컬럼 제약은 코드 되돌리기로 복구되지 않는다.

begin;

-- 사용자 기준 정책을 걷어낸다.
drop policy if exists auth_select_study_logs on public.study_logs;
drop policy if exists auth_insert_study_logs on public.study_logs;
drop policy if exists auth_update_study_logs on public.study_logs;
drop policy if exists auth_delete_study_logs on public.study_logs;

-- 주인 없는 기록을 다시 허용한다.
alter table public.study_logs
  alter column user_id drop not null;

-- 로그인 없이 쓰던 정책을 복구한다.
create policy anon_select_study_logs
  on public.study_logs for select to anon
  using (true);

create policy anon_insert_study_logs
  on public.study_logs for insert to anon
  with check (user_id is null);

create policy anon_update_study_logs
  on public.study_logs for update to anon
  using (user_id is null)
  with check (user_id is null);

create policy anon_delete_study_logs
  on public.study_logs for delete to anon
  using (user_id is null);

-- 주인이 지정된 기존 기록을 다시 주인 없는 상태로 되돌린다.
-- 이 줄을 실행해야 anon 정책이 그 기록들에 다시 닿는다.
update public.study_logs set user_id = null;

commit;
