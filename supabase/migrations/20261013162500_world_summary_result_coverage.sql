-- Summary payloads omit large state-contest tables. Preserve their coverage
-- as metadata so the hydrated archive agrees with pages built from full records.
create or replace function public.ea_world_summaries()
returns table(id text,kind text,data jsonb,updated timestamptz)
language sql stable set search_path='' as $$
 select r.id,r.kind,
 case when r.kind='world_election' then
   (r.data-'contests') || jsonb_build_object(
      'contestCount',jsonb_array_length(coalesce(r.data->'contests','[]'::jsonb)),
      'contestResultCount',coalesce((
        select sum(jsonb_array_length(coalesce(c->'results','[]'::jsonb)))
        from jsonb_array_elements(coalesce(r.data->'contests','[]'::jsonb)) c
      ),0))
 else r.data end,r.updated
 from public.ea_records r
 where r.kind in ('world_country','world_election') and r.is_public
 and (r.publication_at is null or r.publication_at<=now())
 order by r.updated desc,r.id;
$$;
-- Existing execute grants and security-invoker behavior are retained.
