-- Narrow self-service rights: no caller-supplied user ID and no auth secrets exposed.
create function public.ea_export_account() returns jsonb
language plpgsql security definer set search_path='' as $$
declare uid uuid := auth.uid(); result jsonb;
begin
 if uid is null or not exists(select 1 from auth.sessions s where s.user_id=uid and s.id::text=auth.jwt()->>'session_id') then
  raise exception 'Sign in again to access your data' using errcode='42501';
 end if;
 select jsonb_build_object('format','world-of-elections-account-v1','exportedAt',now(),
  'account',jsonb_build_object('id',u.id,'email',u.email,'phone',u.phone,'createdAt',u.created_at,'username',p.username),
  'submittedRevisions',coalesce((select jsonb_agg(jsonb_build_object('recordId',r.record_id,'submittedAt',r.created,'data',r.data) order by r.created) from public.ea_revisions r where r.user_id=uid),'[]'::jsonb))
 into result from auth.users u left join public.ea_profiles p on p.user_id=u.id where u.id=uid;
 if result is null then raise exception 'Account unavailable' using errcode='42501'; end if;
 return result;
end $$;
revoke all on function public.ea_export_account() from public,anon,authenticated;
grant execute on function public.ea_export_account() to authenticated;

create function public.ea_delete_account(confirmation text) returns void
language plpgsql security definer set search_path='' as $$
declare uid uuid := auth.uid();
begin
 if confirmation is distinct from 'DELETE' or uid is null or not exists(
  select 1 from auth.sessions s where s.user_id=uid and s.id::text=auth.jwt()->>'session_id'
   and s.created_at > now()-interval '5 minutes'
 ) then raise exception 'Confirm deletion after a fresh sign-in' using errcode='42501'; end if;
 -- Storage must be erased through its API if uploads are introduced in future.
 if exists(select 1 from storage.objects o where o.owner_id=uid::text) then
  raise exception 'Account has stored files; contact our privacy team for deletion';
 end if;
 -- No attribution or private revision snapshots are retained for a deleted account.
 delete from public.ea_revisions where user_id=uid;
 delete from auth.sessions where user_id=uid;
 delete from auth.users where id=uid;
 -- Profile, editor membership, identities and refresh tokens cascade with auth deletion.
end $$;
revoke all on function public.ea_delete_account(text) from public,anon,authenticated;
grant execute on function public.ea_delete_account(text) to authenticated;
