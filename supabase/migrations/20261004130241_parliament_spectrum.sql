-- Public categorical sides are intentional; exact scores remain protected.
-- SECURITY DEFINER is needed to read the protected classification table. The
-- explicit public-record filters prevent editor sessions from leaking drafts.
create function public.ea_parliament_spectrum(election_id text,axes text[],reverse_order boolean default false)
returns table(result_id text,side text) language plpgsql stable security definer set search_path='' as $$
begin
 if axes is null or cardinality(axes)<1 or cardinality(axes)>9 or exists(select 1 from unnest(axes) a where a is null or a not in ('socialistCapitalist','libertarianAuthoritarian','progressiveConservative','pacifistInterventionist','democracyAutocracy','plannedFreeMarket','irreligiousReligious','globalismProtectionism','bioconservativeTechprogressive')) or cardinality(axes)<>(select count(distinct a) from unnest(axes) a) then raise exception 'Choose distinct supported axes'; end if;
 return query
 with election as (
  select data from public.ea_records where id=election_id and kind='world_election' and is_public and data->>'publication'='published' and data->>'type'='parliamentary' and (publication_at is null or publication_at<=now())
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
 ) select rid,case when v is null then 'unassessed' when v<0 then 'negative' when v>0 then 'positive' else 'neutral' end from positions order by (v is null),case when coalesce(reverse_order,false) then -v else v end,row_index;
end;
$$;
revoke all on function public.ea_parliament_spectrum(text,text[],boolean) from public,anon,authenticated;
grant execute on function public.ea_parliament_spectrum(text,text[],boolean) to anon,authenticated;

notify pgrst, 'reload schema';
