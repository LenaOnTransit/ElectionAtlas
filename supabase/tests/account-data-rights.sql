-- Synthetic accounts only. Always roll back: no real account is deleted.
begin;
insert into auth.users(id,email,raw_user_meta_data) values
 ('aaaaaaaa-1111-4000-8000-000000000001','rights-reader@example.invalid','{"username":"rights_reader_fixture"}'),
 ('aaaaaaaa-1111-4000-8000-000000000002','rights-editor@example.invalid','{"username":"rights_editor_fixture"}');
insert into public.ea_editors values('aaaaaaaa-1111-4000-8000-000000000002');
insert into auth.sessions(id,user_id,created_at) values
 ('bbbbbbbb-1111-4000-8000-000000000001','aaaaaaaa-1111-4000-8000-000000000001',now()-interval '1 hour'),
 ('bbbbbbbb-1111-4000-8000-000000000002','aaaaaaaa-1111-4000-8000-000000000002',now());
insert into public.ea_records(id,kind,data) values('rights-test-record','election','{"id":"rights-test-record"}');
insert into public.ea_revisions(record_id,user_id,data) values('rights-test-record','aaaaaaaa-1111-4000-8000-000000000002','{"id":"rights-test-record","fixture":true}');
set local role anon;
do $$begin
 begin perform public.ea_export_account();raise exception 'Anonymous export allowed';exception when insufficient_privilege then null;end;
 begin perform public.ea_delete_account('DELETE');raise exception 'Anonymous deletion allowed';exception when insufficient_privilege then null;end;
end$$;
reset role;
select set_config('request.jwt.claims','{"sub":"aaaaaaaa-1111-4000-8000-000000000001","session_id":"bbbbbbbb-1111-4000-8000-000000000001"}',true);
set local role authenticated;
do $$declare payload jsonb;begin
 payload:=public.ea_export_account();
 if payload->'account'->>'email'<>'rights-reader@example.invalid' or payload::text like '%rights-editor%' or payload::text like '%encrypted_password%' then raise exception 'Export isolation failed';end if;
 begin perform public.ea_delete_account('DELETE');raise exception 'Stale session deletion allowed';exception when insufficient_privilege then null;end;
end$$;
reset role;
select set_config('request.jwt.claims','{"sub":"aaaaaaaa-1111-4000-8000-000000000002","session_id":"bbbbbbbb-1111-4000-8000-000000000002"}',true);
set local role authenticated;
do $$begin
 if jsonb_array_length(public.ea_export_account()->'submittedRevisions')<>1 or public.ea_export_account()->'account'->>'email'<>'rights-editor@example.invalid' then raise exception 'Editor export failed';end if;
 begin perform public.ea_delete_account('wrong');raise exception 'Unconfirmed deletion allowed';exception when insufficient_privilege then null;end;
 perform public.ea_delete_account('DELETE');
 begin perform public.ea_export_account();raise exception 'Deleted session export allowed';exception when insufficient_privilege then null;end;
end$$;
reset role;
do $$begin
 if exists(select 1 from auth.users where id='aaaaaaaa-1111-4000-8000-000000000002') or exists(select 1 from public.ea_editors where user_id='aaaaaaaa-1111-4000-8000-000000000002') or exists(select 1 from public.ea_profiles where user_id='aaaaaaaa-1111-4000-8000-000000000002') then raise exception 'Deletion incomplete';end if;
 if exists(select 1 from public.ea_revisions where user_id='aaaaaaaa-1111-4000-8000-000000000002') or not exists(select 1 from public.ea_records where id='rights-test-record') then raise exception 'Revision erasure or public record preservation failed';end if;
 if not exists(select 1 from auth.users where id='aaaaaaaa-1111-4000-8000-000000000001') then raise exception 'Other account deleted';end if;
end$$;
rollback;
