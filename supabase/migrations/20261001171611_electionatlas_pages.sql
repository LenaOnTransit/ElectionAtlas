create schema if not exists electionatlas_private;
revoke all on schema electionatlas_private from public, anon, authenticated;

create table public.ea_profiles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 username text not null unique check(username ~ '^[a-z0-9_]{3,30}$'),
 created timestamptz not null default now()
);
create table public.ea_editors (
 user_id uuid primary key references auth.users(id) on delete cascade
);
create table public.ea_records (
 id text primary key check(length(id) between 1 and 100),
 kind text not null check(kind in ('article','election','senate','world_country','world_election')),
 data jsonb not null check(jsonb_typeof(data)='object' and octet_length(data::text)<=1000000),
 updated timestamptz not null default now(),
 is_public boolean generated always as (
  case when kind='article' then coalesce(data->>'status'='published',false)
       when kind='world_election' then coalesce(data->>'publication'='published',false)
       else true end
 ) stored,
 check ((kind='world_country' and id='world-country-'||(data->>'id')) or (kind<>'world_country' and id=data->>'id')),
 check (kind<>'article' or data->>'status' in ('draft','published')),
 check (kind<>'world_election' or data->>'publication' in ('draft','published'))
);
create index ea_records_kind_updated on public.ea_records(kind,updated desc);
create table public.ea_revisions (
 id uuid primary key default gen_random_uuid(),
 record_id text not null references public.ea_records(id),
 user_id uuid not null references auth.users(id),
 created timestamptz not null default now(),
 data jsonb not null
);
create index ea_revisions_record_created on public.ea_revisions(record_id,created desc);
create index ea_revisions_user on public.ea_revisions(user_id);

alter table public.ea_profiles enable row level security;
alter table public.ea_editors enable row level security;
alter table public.ea_records enable row level security;
alter table public.ea_revisions enable row level security;
revoke all on public.ea_profiles,public.ea_editors,public.ea_records,public.ea_revisions from anon,authenticated;
grant select on public.ea_records to anon,authenticated;
grant select on public.ea_profiles,public.ea_editors,public.ea_revisions to authenticated;
grant update(username) on public.ea_profiles to authenticated;
grant insert,update on public.ea_records to authenticated;
grant insert on public.ea_revisions to authenticated;

create policy profiles_self_read on public.ea_profiles for select to authenticated using(user_id=(select auth.uid()));
create policy profiles_self_update on public.ea_profiles for update to authenticated using(user_id=(select auth.uid())) with check(user_id=(select auth.uid()));
create policy editors_self_read on public.ea_editors for select to authenticated using(user_id=(select auth.uid()));
create policy records_public_read on public.ea_records for select to anon,authenticated using(is_public);
create policy records_editor_read on public.ea_records for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy records_editor_insert on public.ea_records for insert to authenticated with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy records_editor_update on public.ea_records for update to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid()))) with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy revisions_editor_read on public.ea_revisions for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy revisions_editor_insert on public.ea_revisions for insert to authenticated with check(user_id=(select auth.uid()) and exists(select 1 from public.ea_editors where user_id=(select auth.uid())));

-- This non-exposed trigger creates a display profile only, never an editor grant.
create function electionatlas_private.handle_new_user() returns trigger language plpgsql security definer set search_path='' as $$
 declare requested text;
 begin
  if auth.uid() is not null and auth.uid()<>new.id then raise exception 'Invalid account context'; end if;
  requested := lower(coalesce(nullif(btrim(new.raw_user_meta_data->>'username'),''),'reader_'||left(replace(new.id::text,'-',''),20)));
  if requested !~ '^[a-z0-9_]{3,30}$' then raise exception 'Username must be 3-30 letters, numbers, or underscores'; end if;
  insert into public.ea_profiles(user_id,username) values(new.id,requested);
  return new;
 end;
$$;
revoke all on function electionatlas_private.handle_new_user() from public,anon,authenticated;
create trigger electionatlas_profile_created after insert on auth.users for each row execute function electionatlas_private.handle_new_user();
insert into public.ea_profiles(user_id,username) select id,'reader_'||left(replace(id::text,'-',''),20) from auth.users on conflict(user_id) do nothing;

create function public.ea_save_record(record_kind text,payload jsonb) returns jsonb language plpgsql security invoker set search_path='' as $$
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
   if expected is null or expected<0 or coalesce((current_row.data->>'version')::integer,0)<>expected then raise exception 'Record changed; reload before saving' using errcode='40001'; end if;
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
