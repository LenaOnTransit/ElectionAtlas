begin;
-- All fixtures are rolled back, including public ones.
insert into public.ea_records(id,kind,data) values
('ideology-qa-left','article','{"id":"ideology-qa-left","articleType":"ideology","status":"published"}'),
('ideology-qa-right','article','{"id":"ideology-qa-right","articleType":"ideology","status":"published"}'),
('world-qa-politics','world_election','{"id":"world-qa-politics","publication":"published","type":"parliamentary","results":[{"id":"unknown","ideologyIds":[]},{"id":"right","ideologyIds":["ideology-qa-right"]},{"id":"left","ideologyIds":["ideology-qa-left"]},{"id":"middle","ideologyIds":["ideology-qa-left","ideology-qa-right"]}]}'),
('world-qa-private','world_election','{"id":"world-qa-private","publication":"draft","type":"parliamentary","results":[{"id":"hidden","ideologyIds":["ideology-qa-left"]}]}');
insert into public.ea_ideology_axes values('ideology-qa-left','{"socialistCapitalist":-8,"progressiveConservative":2}'),('ideology-qa-right','{"socialistCapitalist":8,"progressiveConservative":-2}');
select set_config('test.editor_id',(select user_id::text from public.ea_editors limit 1),true);
set local role anon;
do $$ declare ids text[]; begin
 begin perform * from public.ea_ideology_axes; raise exception 'Anonymous scores leaked'; exception when insufficient_privilege then null; end;
 select array_agg(result_id) into ids from public.ea_parliament_order('world-qa-politics',array['socialistCapitalist']);
 if ids<>array['left','middle','right','unknown'] then raise exception 'Wrong public order: %',ids; end if;
 select array_agg(result_id) into ids from public.ea_parliament_order('world-qa-politics',array['socialistCapitalist'],true);
 if ids<>array['right','middle','left','unknown'] then raise exception 'Wrong reverse order'; end if;
 select array_agg(result_id) into ids from public.ea_parliament_order('world-qa-politics',array['socialistCapitalist','progressiveConservative']);
 if ids<>array['left','middle','right','unknown'] then raise exception 'Wrong combined order'; end if;
 if exists(select 1 from public.ea_parliament_order('world-qa-private',array['socialistCapitalist'])) then raise exception 'Draft leaked'; end if;
 begin perform * from public.ea_parliament_order('world-qa-politics',array['invalid']);raise exception 'Invalid axis accepted';exception when raise_exception then if sqlerrm='Invalid axis accepted' then raise;end if;end;
 begin insert into public.ea_country_parties(id,country_id,name,color) values(gen_random_uuid(),'nl','QA','#123456');raise exception 'Anonymous party write allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_ideology_axes) then raise exception 'Reader scores leaked'; end if;
 begin insert into public.ea_ideology_axes values('ideology-qa-left','{}');raise exception 'Reader write allowed';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub',current_setting('test.editor_id'),true);
set local role authenticated;
do $$ begin
 if not exists(select 1 from public.ea_ideology_axes where ideology_id='ideology-qa-left') then raise exception 'Editor cannot see scores';end if;
 update public.ea_ideology_axes set scores='{"socialistCapitalist":-10}' where ideology_id='ideology-qa-left';
 begin update public.ea_ideology_axes set scores='{"socialistCapitalist":11}' where ideology_id='ideology-qa-left';raise exception 'Out-of-range score accepted';exception when raise_exception then if sqlerrm='Out-of-range score accepted' then raise;end if;end;
 insert into public.ea_country_parties(id,country_id,name,color) values(gen_random_uuid(),'nl','QA party','#123456');
 if not exists(select 1 from public.ea_country_parties where name='QA party') then raise exception 'Editor party save failed';end if;
 if exists(select 1 from public.ea_parliament_order('world-qa-private',array['socialistCapitalist'])) then raise exception 'Draft exposed to public ordering in editor session';end if;
end $$;
reset role;
rollback;
select 'Political data privacy, public ordering, editor writes and score bounds passed; fixtures rolled back.' as result;
