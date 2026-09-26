-- 과목 컬럼을 지운다.
--
-- 태그로 옮긴 뒤 한동안 남겨 두었던 컬럼이다. 그동안은 태그 전환을
-- 되돌릴 수 있게 하기 위해서였다. 이제 모든 화면이 태그로 동작하므로 지운다.
--
-- 되돌릴 수 없다. 실행 전에 데이터를 내려받아 둔다.
-- 이 시점의 값은 각 기록의 첫 태그와 같다.

begin;

do $$
declare
  leftover integer;
begin
  -- 태그가 비어 있는 기록이 있으면 과목을 지울 수 없다.
  select count(*) into leftover
  from public.study_logs
  where tags is null or cardinality(tags) = 0;

  if leftover > 0 then
    raise exception '태그가 없는 기록 %건이 있어 과목을 지울 수 없습니다', leftover;
  end if;
end
$$;

alter table public.study_logs
  drop column if exists subject;

commit;
