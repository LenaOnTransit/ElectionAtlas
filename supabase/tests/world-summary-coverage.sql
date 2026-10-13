-- Run as owner. Fixture users and editor membership are rolled back.
begin;
insert into auth.users(id,email,raw_user_meta_data) values
 ('00000000-0000-4000-8000-000000000211','summary-reader@example.invalid','{"username":"summary_test_reader"}'),
 ('00000000-0000-4000-8000-000000000212','summary-editor@example.invalid','{"username":"summary_test_editor"}');
insert into public.ea_editors(user_id) values('00000000-0000-4000-8000-000000000212');
set local role anon;
do $$ declare mismatches integer;begin
 with summaries as (select * from public.ea_world_summaries()),
 full_records as (select * from public.ea_public_records(array['world_country','world_election']))
 select count(*) into mismatches from summaries s full join full_records r using(id)
 where s.id is null or r.id is null or s.kind<>r.kind
 or (s.kind='world_election' and (
   s.data ? 'contests'
   or (s.data->>'contestCount')::integer<>jsonb_array_length(coalesce(r.data->'contests','[]'::jsonb))
   or (s.data->>'contestResultCount')::integer<>coalesce((select sum(jsonb_array_length(coalesce(c->'results','[]'::jsonb))) from jsonb_array_elements(coalesce(r.data->'contests','[]'::jsonb)) c),0)
   or s.data-array['contestCount','contestResultCount']<>r.data-'contests'
   or s.data->>'publication'<>'published'));
 if mismatches<>0 then raise exception 'Anonymous summary/full-record mismatch: %',mismatches;end if;
 end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000211',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_world_summaries() where kind='world_election' and (data->>'publication'<>'published' or data ? 'contests' or not data ? 'contestResultCount')) then raise exception 'Reader summary exposure/coverage mismatch';end if;
 if not exists(select 1 from public.ea_world_summaries() where kind='world_election' and (data->>'contestResultCount')::integer>0) then raise exception 'Reader cannot see nested-result metadata';end if;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000212',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_world_summaries() where kind='world_election' and (data->>'publication'<>'published' or data ? 'contests' or not data ? 'contestResultCount')) then raise exception 'Editor public summary exposure/coverage mismatch';end if;
 if not exists(select 1 from public.ea_world_summaries() where kind='world_election' and (data->>'contestResultCount')::integer>0) then raise exception 'Editor cannot see public nested-result metadata';end if;
end $$;
reset role;
rollback;
select 'Public summary coverage matches full records; anonymous, reader and editor checks passed; fixtures rolled back' as result;
