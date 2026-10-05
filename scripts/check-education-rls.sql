-- Run through a privileged SQL connection. Every fixture is rolled back.
begin;
select set_config('education.test.prefix','educational-rls-'||gen_random_uuid()::text,true);
select set_config('education.test.reader',gen_random_uuid()::text,true);
select set_config('education.test.editor',(select user_id::text from public.ea_editors limit 1),true);
do $$
declare prefix text:=current_setting('education.test.prefix'); suffix text; payload jsonb;
begin
 if nullif(current_setting('education.test.editor'),'') is null then raise exception 'An existing moderator is required for the test'; end if;
 foreach suffix in array array['published','draft','future','trash'] loop
  payload:=jsonb_build_object('id',prefix||'-'||suffix,'articleType','educational','educationCategory','elections-voting','category','Elections & voting','title','RLS verification fixture','summary','A test summary','body','A test body','sections','[]'::jsonb,'sources','[]'::jsonb,'author','World of Elections','date','2026-10-06','status',case when suffix in ('draft','trash') then 'draft' else 'published' end,'archived',suffix='trash');
  if suffix='future' then payload:=payload||jsonb_build_object('publishAt','2099-01-01T00:00:00Z'); end if;
  insert into public.ea_records(id,kind,data) values(payload->>'id','article',payload);
 end loop;
end $$;
set local role anon;
select set_config('request.jwt.claim.sub','',true);
do $$
declare n integer;
begin
 select count(*) into n from public.ea_public_records(array['article']) where id like current_setting('education.test.prefix')||'%';
 if n<>1 then raise exception 'Anonymous public RPC exposed nonpublic educationals'; end if;
 select count(*) into n from public.ea_records where id like current_setting('education.test.prefix')||'%';
 if n<>1 then raise exception 'Anonymous table read exposed nonpublic educationals'; end if;
 begin
  perform public.ea_save_record('article',jsonb_build_object('id',current_setting('education.test.prefix')||'-denied','articleType','educational','status','draft'));
  raise exception 'Anonymous write unexpectedly succeeded';
 exception when insufficient_privilege then null; end;
end $$;
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub',current_setting('education.test.reader'),true);
do $$
declare n integer;
begin
 select count(*) into n from public.ea_records where id like current_setting('education.test.prefix')||'%';
 if n<>1 then raise exception 'Reader exposed nonpublic educationals'; end if;
 begin
  perform public.ea_save_record('article',jsonb_build_object('id',current_setting('education.test.prefix')||'-denied','articleType','educational','status','draft'));
  raise exception 'Reader write unexpectedly succeeded';
 exception when insufficient_privilege then null; end;
end $$;
reset role;
set local role authenticated;
select set_config('request.jwt.claim.sub',current_setting('education.test.editor'),true);
do $$
declare n integer; payload jsonb;
begin
 select count(*) into n from public.ea_records where id like current_setting('education.test.prefix')||'%';
 if n<>4 then raise exception 'Moderator cannot read educational drafts'; end if;
 select data into payload from public.ea_records where id=current_setting('education.test.prefix')||'-draft';
 payload:=payload||jsonb_build_object('body','Moderator save verified');
 perform public.ea_save_record('article',payload);
 if not exists(select 1 from public.ea_records where id=payload->>'id' and data->>'body'='Moderator save verified') then raise exception 'Moderator draft save failed'; end if;
 payload:=payload||jsonb_build_object('status','published');
 perform public.ea_save_record('article',payload);
 if not exists(select 1 from public.ea_public_records(array['article']) where id=payload->>'id') then raise exception 'Published educational absent from public RPC'; end if;
 payload:=payload||jsonb_build_object('status','draft','archived',true);
 perform public.ea_save_record('article',payload);
 if exists(select 1 from public.ea_public_records(array['article']) where id=payload->>'id') then raise exception 'Removed educational still publicly readable'; end if;
end $$;
reset role;
rollback;
select 'Passed: anonymous/reader privacy and write denial; moderator draft save, publish, trash; all fixtures rolled back.' as result;
