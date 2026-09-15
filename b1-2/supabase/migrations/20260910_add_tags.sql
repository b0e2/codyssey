-- subject 하나 대신 tags 배열로 분류 축을 바꾼다.
--
-- 태그를 별도 테이블로 분리하지 않는 이유는 핵심 데이터가 하나라는 조건을
-- 지키기 위해서다. 인기 태그 집계와 태그별 목록은 클라이언트에서 계산한다.
--
-- 이 파일은 subject 를 지우지 않는다. drop 은 되돌릴 수 없으므로
-- 전체가 안정된 뒤 배포 단계에서 별도 파일로 실행한다.
-- 그때까지는 20260910_rollback_tags.sql 로 언제든 되돌릴 수 있다.

begin;

alter table public.study_logs
  add column if not exists tags text[];

update public.study_logs
set tags = array[btrim(subject)]
where tags is null;

-- 이관이 온전한지 확인한 뒤에만 제약을 건다.
-- 하나라도 어긋나면 예외를 던져 commit 되지 않게 한다.
do $$
declare
  bad_count integer;
begin
  select count(*) into bad_count
  from public.study_logs
  where tags is null
     or cardinality(tags) = 0
     or array_position(tags, null) is not null
     or array_position(tags, '') is not null;

  if bad_count > 0 then
    raise exception 'tags 이관 검증 실패: 잘못된 행 %건', bad_count;
  end if;
end
$$;

alter table public.study_logs
  alter column tags set not null;

alter table public.study_logs
  add constraint study_logs_tags_count
    check (cardinality(tags) between 1 and 5),
  add constraint study_logs_tags_no_null
    check (array_position(tags, null) is null),
  add constraint study_logs_tags_no_empty
    check (array_position(tags, '') is null),
  -- 각 원소의 길이를 CHECK 로 직접 검사하려면 unnest 가 필요한데
  -- PostgreSQL 은 CHECK 제약에 서브쿼리를 허용하지 않는다.
  -- 대신 서브쿼리 없이 쓸 수 있는 전체 길이로 상한을 둔다.
  -- 태그 5개 * 30자 + 구분자 4개 = 154자이므로 160자면 충분하다.
  -- 원소별 30자 규칙은 lib/studyLogValidation.js 가 담당한다.
  add constraint study_logs_tags_total_length
    check (char_length(array_to_string(tags, ',')) <= 160);

-- subject 를 필수로 두면 새 기록을 만들 때 값을 넣어야 하므로 제약만 먼저 푼다.
alter table public.study_logs
  drop constraint if exists study_logs_subject_length;

alter table public.study_logs
  alter column subject drop not null;

commit;
