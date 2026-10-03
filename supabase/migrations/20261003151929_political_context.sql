-- Reusable public party details, with editorial-only writes.
create table public.ea_country_parties (
 id uuid primary key,
 country_id text not null,
 name text not null check(length(btrim(name)) between 1 and 200),
 short_name text not null default '' check(length(short_name)<=100),
 color text not null check(color ~ '^#[a-fA-F0-9]{6}$'),
 ideology_ids text[] not null default '{}' check(cardinality(ideology_ids)<=30),
 notes text not null default '' check(length(notes)<=5000),
 archived boolean not null default false
);
create index ea_country_parties_country on public.ea_country_parties(country_id);
alter table public.ea_country_parties enable row level security;
revoke all on public.ea_country_parties from public,anon,authenticated;
grant select on public.ea_country_parties to anon,authenticated;
grant insert,update on public.ea_country_parties to authenticated;
create policy parties_public_read on public.ea_country_parties for select to anon,authenticated using(not archived);
create policy parties_editor_read on public.ea_country_parties for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy parties_editor_insert on public.ea_country_parties for insert to authenticated with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy parties_editor_update on public.ea_country_parties for update to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid()))) with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));

-- These values must never be embedded in public articles or election records.
create table public.ea_ideology_axes (
 ideology_id text primary key references public.ea_records(id),
 scores jsonb not null default '{}' check(jsonb_typeof(scores)='object')
);
alter table public.ea_ideology_axes enable row level security;
revoke all on public.ea_ideology_axes from public,anon,authenticated;
grant select,insert,update on public.ea_ideology_axes to authenticated;
create policy axes_editor_read on public.ea_ideology_axes for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy axes_editor_insert on public.ea_ideology_axes for insert to authenticated with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
create policy axes_editor_update on public.ea_ideology_axes for update to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid()))) with check(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));

create function electionatlas_private.validate_politics() returns trigger language plpgsql security invoker set search_path='' as $$
declare pair record; ideology text;
begin
 if tg_table_name='ea_ideology_axes' then
  if not exists(select 1 from public.ea_records where id=new.ideology_id and kind='article' and data->>'articleType'='ideology') then raise exception 'Unknown ideology'; end if;
  for pair in select * from jsonb_each(new.scores) loop
   if pair.key not in ('socialistCapitalist','libertarianAuthoritarian','progressiveConservative','pacifistInterventionist','democracyAutocracy','plannedFreeMarket','irreligiousReligious','globalismProtectionism','bioconservativeTechprogressive') or jsonb_typeof(pair.value)<>'number' then raise exception 'Invalid ideology axis'; end if;
   if pair.value::text::numeric < -10 or pair.value::text::numeric > 10 then raise exception 'Axis values must be between -10 and 10'; end if;
  end loop;
 else
  if not exists(select 1 from public.ea_records where id='world-country-'||new.country_id and kind='world_country') then raise exception 'Unknown country'; end if;
  if cardinality(new.ideology_ids)<>(select count(distinct id) from unnest(new.ideology_ids) id) then raise exception 'Duplicate ideology'; end if;
  foreach ideology in array new.ideology_ids loop
   if not exists(select 1 from public.ea_records where id=ideology and kind='article' and data->>'articleType'='ideology') then raise exception 'Unknown ideology'; end if;
  end loop;
 end if;
 return new;
end;
$$;
revoke all on function electionatlas_private.validate_politics() from public,anon,authenticated;
create trigger ea_validate_axes before insert or update on public.ea_ideology_axes for each row execute function electionatlas_private.validate_politics();
create trigger ea_validate_party before insert or update on public.ea_country_parties for each row execute function electionatlas_private.validate_politics();

-- Deliberately exposes ONLY row IDs in derived order, never numeric values.
-- SECURITY DEFINER is needed to read the protected classification table. The
-- explicit public-record filters prevent editor sessions from leaking drafts.
create function public.ea_parliament_order(election_id text,axes text[],reverse_order boolean default false)
returns table(result_id text) language plpgsql stable security definer set search_path='' as $$
begin
 if axes is null or cardinality(axes)<1 or cardinality(axes)>9 or exists(select 1 from unnest(axes) a where a is null or a not in ('socialistCapitalist','libertarianAuthoritarian','progressiveConservative','pacifistInterventionist','democracyAutocracy','plannedFreeMarket','irreligiousReligious','globalismProtectionism','bioconservativeTechprogressive')) or cardinality(axes)<>(select count(distinct a) from unnest(axes) a) then raise exception 'Choose distinct supported axes'; end if;
 return query
 with election as (
  select data from public.ea_records where id=election_id and kind='world_election' and is_public and data->>'publication'='published' and data->>'type'='parliamentary'
 ), results as (
  select r.value as row_data,r.ordinality as row_index from election cross join lateral jsonb_array_elements(data->'results') with ordinality r
 ), axis_values as (
  select r.row_data->>'id' as rid,r.row_index,a.axis,avg((s.scores->>a.axis)::numeric) as v
  from results r cross join unnest(axes) a(axis)
  left join lateral jsonb_array_elements_text(coalesce(r.row_data->'ideologyIds','[]'::jsonb)) i(id) on true
  left join public.ea_records guide on guide.id=i.id and guide.kind='article' and guide.is_public and guide.data->>'articleType'='ideology' and guide.data->>'status'='published' and coalesce(guide.data->>'archived','false')<>'true' and (guide.publication_at is null or guide.publication_at<=now())
  left join public.ea_ideology_axes s on s.ideology_id=guide.id
  group by rid,r.row_index,a.axis
 ), positions as (
  select rid,row_index,case when count(v)=cardinality(axes) then avg(v) else null end as v from axis_values group by rid,row_index
 ) select rid from positions order by (v is null),case when coalesce(reverse_order,false) then -v else v end,row_index;
end;
$$;
revoke all on function public.ea_parliament_order(text,text[],boolean) from public,anon,authenticated;
grant execute on function public.ea_parliament_order(text,text[],boolean) to anon,authenticated;
