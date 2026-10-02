-- All scheduling fixtures and account changes roll back.
begin;
insert into auth.users(id,email,raw_user_meta_data) values
 ('00000000-0000-4000-8000-000000000201','schedule-reader@electionatlas.invalid','{"username":"ea_schedule_reader"}'),
 ('00000000-0000-4000-8000-000000000202','schedule-editor@electionatlas.invalid','{"username":"ea_schedule_editor"}');
insert into public.ea_editors(user_id) values('00000000-0000-4000-8000-000000000202');
insert into public.ea_records(id,kind,data) values
 ('schedule-future','article',jsonb_build_object('id','schedule-future','title','Test future','status','published','publishAt',to_char(now()+interval '1 day','YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'))),
 ('schedule-due','article',jsonb_build_object('id','schedule-due','title','Test due','status','published','publishAt',to_char(now()-interval '1 day','YYYY-MM-DD"T"HH24:MI:SS"Z"'))),
 ('schedule-draft','article','{"id":"schedule-draft","title":"Draft","status":"draft"}'),
 ('schedule-trash','article','{"id":"schedule-trash","title":"Trash","status":"published","archived":true}');
set local role anon;
do $$ begin
 if exists(select 1 from public.ea_records where id in ('schedule-future','schedule-draft','schedule-trash')) then raise exception 'Anonymous private article leak';end if;
 if not exists(select 1 from public.ea_records where id='schedule-due') then raise exception 'Due article missing';end if;
 if exists(select 1 from public.ea_public_records(array['article']) where id in ('schedule-future','schedule-draft','schedule-trash')) then raise exception 'Public RPC leaked';end if;
 begin perform public.ea_save_record('article','{"id":"schedule-illegal","status":"published"}');raise exception 'Anonymous saved';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000201',true) is not null as reader_session;
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_records where id in ('schedule-future','schedule-draft','schedule-trash')) then raise exception 'Reader private article leak';end if;
 begin perform public.ea_save_record('article','{"id":"schedule-illegal","status":"published"}');raise exception 'Reader saved';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000202',true) is not null as editor_session;
set local role authenticated;
do $$ declare item jsonb;begin
 if not exists(select 1 from public.ea_records where id='schedule-future') then raise exception 'Editor cannot edit schedule';end if;
 if exists(select 1 from public.ea_public_records(array['article']) where id='schedule-future') then raise exception 'Editor public page leaked schedule';end if;
 select data into item from public.ea_records where id='schedule-future';
 perform public.ea_save_record('article',jsonb_set(item,'{publishAt}',to_jsonb(to_char(now()+interval '2 days','YYYY-MM-DD"T"HH24:MI:SS"Z"'))));
 if not exists(select 1 from public.ea_records where id='schedule-future' and publication_at>now()+interval '1 day') then raise exception 'Reschedule failed';end if;
 update public.ea_records set publication_at=now()-interval '1 day' where id='schedule-future';
 if exists(select 1 from public.ea_public_records(array['article']) where id='schedule-future') then raise exception 'Timestamp column bypass';end if;
 begin perform public.ea_save_record('article',jsonb_set(item,'{publishAt}','"tomorrow"'));raise exception 'Invalid time accepted';exception when invalid_datetime_format then null;end;
 perform public.ea_save_record('article',jsonb_set(item,'{publishAt}',to_jsonb(to_char(now()-interval '1 second','YYYY-MM-DD"T"HH24:MI:SS"Z"'))));
 if not exists(select 1 from public.ea_public_records(array['article']) where id='schedule-future') then raise exception 'Release failed';end if;
 perform public.ea_save_record('article',jsonb_set(item,'{status}','"draft"'));
 if exists(select 1 from public.ea_public_records(array['article']) where id='schedule-future') then raise exception 'Cancellation failed';end if;
end $$;
reset role;
set local role anon;
do $$ begin if exists(select 1 from public.ea_records where id='schedule-future') then raise exception 'Cancelled article exposed';end if;end $$;
reset role;
select 'Passed: anonymous/reader privacy, editor-only scheduling, due publication, reschedule, cancellation, malformed timestamps, direct-column bypass and editor public filtering' as result;
rollback;
