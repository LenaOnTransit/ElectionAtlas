-- Archive/atlas/calendar reads exclude the large state-candidate tables.
-- Exact-record reads use the primary key and retain public filters even when
-- called by an editor. SECURITY INVOKER preserves the existing reader RLS.
create function public.ea_world_summaries()
returns table(id text,kind text,data jsonb,updated timestamptz)
language sql stable security invoker set search_path='' as $$
 select r.id,r.kind,
 case when r.kind='world_election' then
   (r.data-'contests') || jsonb_build_object('contestCount',
      jsonb_array_length(coalesce(r.data->'contests','[]'::jsonb)))
 else r.data end,r.updated
 from public.ea_records r
 where r.kind in ('world_country','world_election') and r.is_public
 and (r.publication_at is null or r.publication_at<=now())
 order by r.updated desc,r.id;
$$;

create function public.ea_public_election(record_id text)
returns jsonb language sql stable security invoker set search_path='' as $$
 select r.data from public.ea_records r
 where r.id=record_id and r.kind='world_election' and r.is_public
 and r.data->>'publication'='published'
 and (r.publication_at is null or r.publication_at<=now());
$$;
revoke all on function public.ea_world_summaries() from public,anon,authenticated;
revoke all on function public.ea_public_election(text) from public,anon,authenticated;
grant execute on function public.ea_world_summaries() to anon,authenticated;
grant execute on function public.ea_public_election(text) to anon,authenticated;
notify pgrst,'reload schema';
