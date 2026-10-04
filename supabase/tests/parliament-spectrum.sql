begin;
insert into public.ea_records(id,kind,data) values
('ideology-qa-spectrum-negative','article','{"id":"ideology-qa-spectrum-negative","articleType":"ideology","status":"published"}'),
('ideology-qa-spectrum-positive','article','{"id":"ideology-qa-spectrum-positive","articleType":"ideology","status":"published"}'),
('ideology-qa-spectrum-hidden','article','{"id":"ideology-qa-spectrum-hidden","articleType":"ideology","status":"draft"}'),
('world-qa-spectrum','world_election','{"id":"world-qa-spectrum","publication":"published","type":"parliamentary","results":[{"id":"unknown","ideologyIds":[]},{"id":"positive","ideologyIds":["ideology-qa-spectrum-positive"]},{"id":"negative","ideologyIds":["ideology-qa-spectrum-negative"]},{"id":"neutral","ideologyIds":["ideology-qa-spectrum-positive","ideology-qa-spectrum-negative"]},{"id":"hidden","ideologyIds":["ideology-qa-spectrum-hidden"]}]}'),
('world-qa-spectrum-draft','world_election','{"id":"world-qa-spectrum-draft","publication":"draft","type":"parliamentary","results":[{"id":"hidden","ideologyIds":["ideology-qa-spectrum-negative"]}]}');
insert into public.ea_ideology_axes(ideology_id,scores)
select id,jsonb_object_agg(axis,case when id='ideology-qa-spectrum-positive' then 8 else -8 end)
from unnest(array['ideology-qa-spectrum-negative','ideology-qa-spectrum-positive','ideology-qa-spectrum-hidden']) id
cross join unnest(array['socialistCapitalist','libertarianAuthoritarian','progressiveConservative','pacifistInterventionist','democracyAutocracy','plannedFreeMarket','irreligiousReligious','globalismProtectionism','bioconservativeTechprogressive']) axis group by id;
select set_config('test.editor_id',(select user_id::text from public.ea_editors limit 1),true);
set local role anon;
do $$ declare axis text; ids text[]; sides text[]; begin
 foreach axis in array array['socialistCapitalist','libertarianAuthoritarian','progressiveConservative','pacifistInterventionist','democracyAutocracy','plannedFreeMarket','irreligiousReligious','globalismProtectionism','bioconservativeTechprogressive'] loop
  select array_agg(result_id),array_agg(side) into ids,sides from public.ea_parliament_spectrum('world-qa-spectrum',array[axis]);
  if ids<>array['negative','neutral','positive','unknown','hidden'] or sides<>array['negative','neutral','positive','unassessed','unassessed'] then raise exception 'Wrong spectrum for %: %, %',axis,ids,sides; end if;
 end loop;
 select array_agg(side) into sides from public.ea_parliament_spectrum('world-qa-spectrum',array['socialistCapitalist'],true);
 if sides<>array['positive','neutral','negative','unassessed','unassessed'] then raise exception 'Reversed labels changed meaning'; end if;
 select array_agg(side) into sides from public.ea_parliament_spectrum('world-qa-spectrum',array['socialistCapitalist','progressiveConservative']);
 if sides<>array['negative','neutral','positive','unassessed','unassessed'] then raise exception 'Combined spectrum wrong'; end if;
 if exists(select 1 from public.ea_parliament_spectrum('world-qa-spectrum-draft',array['socialistCapitalist'])) then raise exception 'Draft leaked'; end if;
 if exists(select 1 from public.ea_parliament_spectrum('missing-election',array['socialistCapitalist'])) then raise exception 'Missing election returned data'; end if;
 begin perform 1 from public.ea_ideology_axes; raise exception 'Anonymous exact scores leaked'; exception when insufficient_privilege then null; end;
 begin perform * from public.ea_parliament_spectrum('world-qa-spectrum',array[]::text[]);raise exception 'Empty axes accepted';exception when raise_exception then if sqlerrm='Empty axes accepted' then raise;end if;end;
 begin perform * from public.ea_parliament_spectrum('world-qa-spectrum',array['socialistCapitalist','socialistCapitalist']);raise exception 'Duplicate axes accepted';exception when raise_exception then if sqlerrm='Duplicate axes accepted' then raise;end if;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
set local role authenticated;
do $$ begin if exists(select 1 from public.ea_ideology_axes) then raise exception 'Reader exact scores leaked'; end if; end $$;
reset role;
select set_config('request.jwt.claim.sub',current_setting('test.editor_id'),true);
set local role authenticated;
do $$ begin
 if not exists(select 1 from public.ea_ideology_axes where ideology_id='ideology-qa-spectrum-negative') then raise exception 'Editor scores unavailable'; end if;
 if exists(select 1 from public.ea_parliament_spectrum('world-qa-spectrum-draft',array['socialistCapitalist'])) then raise exception 'Editor leaked draft through public RPC'; end if;
end $$;
reset role;
rollback;
select 'Spectrum: all axes, combined/reversed ordering, neutral/unassessed groups, drafts and exact-score privacy passed; fixtures rolled back.' as result;
