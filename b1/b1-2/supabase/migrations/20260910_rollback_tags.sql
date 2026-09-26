-- 20260910_add_tags.sql 을 되돌린다.
-- subject 컬럼이 아직 남아 있는 동안에만 유효하다.

begin;

-- tags 만 있고 subject 가 비어 있는 행이 생겼다면 첫 태그로 복구한다.
update public.study_logs
set subject = tags[1]
where subject is null
  and tags is not null
  and cardinality(tags) > 0;

alter table public.study_logs
  drop constraint if exists study_logs_tags_count,
  drop constraint if exists study_logs_tags_no_null,
  drop constraint if exists study_logs_tags_no_empty,
  drop constraint if exists study_logs_tags_total_length;

alter table public.study_logs
  drop column if exists tags;

alter table public.study_logs
  alter column subject set not null;

alter table public.study_logs
  add constraint study_logs_subject_length
    check (char_length(btrim(subject)) between 2 and 30);

commit;
