-- Run as the database owner. All temporary users and records roll back.
begin;
insert into auth.users(id,email,raw_user_meta_data)
values ('00000000-0000-4000-8000-000000000101','reader-test@electionatlas.invalid','{"username":"ea_access_reader","role":"admin"}'),
       ('00000000-0000-4000-8000-000000000102','editor-test@electionatlas.invalid','{"username":"ea_access_editor"}');
insert into public.ea_editors(user_id) values('00000000-0000-4000-8000-000000000102');
insert into public.ea_records(id,kind,data) values
 ('access-draft','article','{"id":"access-draft","title":"Private test","status":"draft"}'),
 ('access-public','article','{"id":"access-public","title":"Public test","status":"published"}');

set local role anon;
do $$ begin
 if exists(select 1 from public.ea_records where id='access-draft') then raise exception 'Anonymous draft leak'; end if;
 if not exists(select 1 from public.ea_records where id='access-public') then raise exception 'Public content inaccessible'; end if;
 begin insert into public.ea_records(id,kind,data) values('illegal','article','{"id":"illegal","status":"published"}');raise exception 'Anonymous write succeeded';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000101',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_records where id='access-draft') then raise exception 'Reader draft leak'; end if;
 if exists(select 1 from public.ea_editors) then raise exception 'Metadata escalated role'; end if;
 begin insert into public.ea_editors(user_id) values(auth.uid());raise exception 'Self-promotion succeeded';exception when insufficient_privilege then null;end;
 begin perform public.ea_save_record('article','{"id":"illegal","status":"published"}');raise exception 'Reader write succeeded';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000102',true);
set local role authenticated;
do $$ declare result jsonb; original jsonb; begin
 if not exists(select 1 from public.ea_records where id='access-draft') then raise exception 'Editor cannot read draft'; end if;
 perform public.ea_save_record('article','{"id":"access-draft","title":"Published test","status":"published"}');
 select data into original from public.ea_records where kind='world_election' order by id limit 1;
 if original is null then raise exception 'World seeds missing'; end if;
 result:=public.ea_save_record('world_election',original);
 if (result->>'version')::integer<>(original->>'version')::integer+1 then raise exception 'Version was not incremented'; end if;
 if not exists(select 1 from public.ea_revisions where record_id=original->>'id' and data=result) then raise exception 'Revision missing'; end if;
 begin perform public.ea_save_record('world_election',original);raise exception 'Stale write succeeded';exception when serialization_failure then null;end;
end $$;
reset role;
set local role anon;
do $$ begin
 if not exists(select 1 from public.ea_records where id='access-draft') then raise exception 'Published record missing'; end if;
end $$;
reset role;
select 'Passed: anonymous/reader draft privacy and write denial, no metadata escalation or self-promotion, editor save/publish, atomic world revision, stale-write rejection' as result;
rollback;
