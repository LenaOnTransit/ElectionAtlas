-- Stale editor versions are application conflicts, never retryable serialization failures.
create or replace function public.ea_save_record(record_kind text,payload jsonb) returns jsonb language plpgsql security invoker set search_path='' as $$
 declare rid text; current_row public.ea_records; next_payload jsonb; expected integer;
 begin
  if auth.uid() is null or not exists(select 1 from public.ea_editors where user_id=auth.uid()) then raise exception 'Editorial access required' using errcode='42501'; end if;
  if record_kind not in ('article','election','senate','world_country','world_election') or jsonb_typeof(payload)<>'object' or nullif(payload->>'id','') is null then raise exception 'Invalid record'; end if;
  rid:=case when record_kind='world_country' then 'world-country-'||(payload->>'id') else payload->>'id' end;
  if length(rid)>100 then raise exception 'Invalid record ID'; end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(rid,0));
  select * into current_row from public.ea_records where id=rid for update;
  if current_row.id is not null and current_row.kind<>record_kind then raise exception 'Record type cannot change'; end if;
  next_payload:=payload;
  if record_kind='world_election' then
   expected:=(payload->>'version')::integer;
   if expected is null or expected<0 or coalesce((current_row.data->>'version')::integer,0)<>expected then raise exception 'Record changed; reload before saving' using errcode='PT409'; end if;
   if not exists(select 1 from public.ea_records where kind='world_country' and data->>'id'=payload->>'countryId') then raise exception 'Unknown country'; end if;
   next_payload:=jsonb_set(payload,'{version}',to_jsonb(expected+1));
   if payload ? 'live' then next_payload:=jsonb_set(next_payload,'{live,updated}',to_jsonb(now()::text)); end if;
  end if;
  insert into public.ea_records(id,kind,data,updated) values(rid,record_kind,next_payload,now()) on conflict(id) do update set data=excluded.data,updated=excluded.updated;
  if record_kind='world_election' then insert into public.ea_revisions(record_id,user_id,data) values(rid,auth.uid(),next_payload); end if;
  return next_payload;
 end;
$$;
revoke all on function public.ea_save_record(text,jsonb) from public,anon,authenticated;
grant execute on function public.ea_save_record(text,jsonb) to authenticated;

notify pgrst, 'reload schema';
