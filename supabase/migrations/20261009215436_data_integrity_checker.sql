-- Findings are private operational data; elections remain in ea_records unchanged.
create table public.ea_integrity_findings (
 finding_key text primary key, record_id text not null, rule text not null, severity text not null check(severity in ('error','warning','info')),
 scope text not null, subject text not null, explanation text not null, evidence jsonb not null,
 fingerprint text not null, active boolean not null default true, review_status text not null default 'open' check(review_status in ('open','fixed','accepted-exception')),
 review_note text not null default '', reviewed_by uuid references auth.users(id) on delete set null, reviewed_at timestamptz,
 first_seen timestamptz not null default now(), last_seen timestamptz not null default now(), resolved_at timestamptz,
 country_id text not null, election_title text not null, election_type text not null, rules_version text not null default '1'
);
alter table public.ea_integrity_findings add column search_text text generated always as (record_id||' '||election_title||' '||rule||' '||explanation||' '||evidence::text) stored;
create index ea_integrity_findings_filters on public.ea_integrity_findings(review_status,severity,country_id,record_id);
create index ea_integrity_findings_record on public.ea_integrity_findings(record_id);
create table public.ea_integrity_reviews (
 id bigint generated always as identity primary key, finding_key text not null references public.ea_integrity_findings(finding_key), status text not null,
 note text not null, fingerprint text not null, reviewed_by uuid references auth.users(id) on delete set null, reviewed_at timestamptz not null default now()
);
create table public.ea_integrity_scans (
 id uuid primary key default gen_random_uuid(), mode text not null check(mode in ('full','incremental')), status text not null default 'running' check(status in ('running','completed')),
 started_at timestamptz not null default now(), finished_at timestamptz, records_target integer not null default 0, records_scanned integer not null default 0, requested_by uuid references auth.users(id) on delete set null, rules_version text not null default '1'
);
create table public.ea_integrity_context (
 record_id text primary key references public.ea_records(id) on delete cascade, settings jsonb not null default '{}'::jsonb check(jsonb_typeof(settings)='object' and octet_length(settings::text)<20000),
 note text not null check(length(btrim(note))>0), updated_at timestamptz not null default now(), updated_by uuid references auth.users(id) on delete set null
);
create table electionatlas_private.integrity_queue (
 record_id text primary key, enqueued_at timestamptz not null default clock_timestamp(), scan_id uuid references public.ea_integrity_scans(id), attempts integer not null default 0,
 next_attempt timestamptz not null default now(), last_error text
);
create table electionatlas_private.integrity_checked (record_id text primary key, checked_at timestamptz not null, fingerprint text not null, rules_version text not null);
alter table electionatlas_private.integrity_queue enable row level security;
alter table electionatlas_private.integrity_checked enable row level security;
revoke all on electionatlas_private.integrity_queue,electionatlas_private.integrity_checked from public,anon,authenticated;
alter table public.ea_integrity_findings enable row level security;
revoke all on public.ea_integrity_findings from public,anon,authenticated;
grant select on public.ea_integrity_findings to authenticated;
create policy integrity_moderator_read on public.ea_integrity_findings for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
alter table public.ea_integrity_reviews enable row level security;
revoke all on public.ea_integrity_reviews from public,anon,authenticated;
grant select on public.ea_integrity_reviews to authenticated;
create policy integrity_moderator_read on public.ea_integrity_reviews for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
alter table public.ea_integrity_scans enable row level security;
revoke all on public.ea_integrity_scans from public,anon,authenticated;
grant select on public.ea_integrity_scans to authenticated;
create policy integrity_moderator_read on public.ea_integrity_scans for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
alter table public.ea_integrity_context enable row level security;
revoke all on public.ea_integrity_context from public,anon,authenticated;
grant select on public.ea_integrity_context to authenticated;
create policy integrity_moderator_read on public.ea_integrity_context for select to authenticated using(exists(select 1 from public.ea_editors where user_id=(select auth.uid())));
-- Reusable, read-only rules consume the existing WorldElection JSON and contest shapes.
create or replace function electionatlas_private.integrity_array(v jsonb) returns jsonb language sql immutable set search_path='' as $$ select case when jsonb_typeof(v)='array' then v else '[]'::jsonb end $$;
create or replace function electionatlas_private.integrity_number(v jsonb) returns numeric language plpgsql immutable set search_path='' as $$ begin if jsonb_typeof(v)='number' then return (v#>>'{}')::numeric; end if; return null; exception when others then return null; end $$;
create or replace function electionatlas_private.integrity_date(v text) returns boolean language plpgsql immutable set search_path='' as $$ begin return coalesce(v ~ '^\d{4}-\d{2}-\d{2}$' and to_char(v::date,'YYYY-MM-DD')=v,false); exception when others then return false; end $$;
create or replace function electionatlas_private.integrity_normal(v text) returns text language sql immutable set search_path='' as $$ select lower(regexp_replace(btrim(coalesce(v,'')),'\s+',' ','g')) $$;
create or replace function electionatlas_private.integrity_round(v text) returns integer language sql immutable set search_path='' as $$ select case when lower(btrim(v)) ~ '^(1|1st|first|round 1|first round|premier tour)$' then 1 when lower(btrim(v)) ~ '^(2|2nd|second|round 2|second round|runoff|run-off|runoff round|second tour)$' then 2 else null end $$;
create or replace function electionatlas_private.integrity_finding(rule text,severity text,scope text,subject text,explanation text,evidence jsonb) returns jsonb language sql immutable set search_path='' as $$ select jsonb_build_object('rule',rule,'severity',severity,'scope',scope,'subject',subject,'explanation',explanation,'evidence',evidence) $$;

create or replace function electionatlas_private.integrity_rules(e jsonb,settings jsonb default '{}'::jsonb,peers jsonb default '[]'::jsonb) returns setof jsonb language plpgsql immutable set search_path='' as $$
declare
 t jsonb; tables jsonb; rows jsonb; r jsonb; p jsonb; c jsonb; cfg jsonb; evidence jsonb;
 scope text; field text; label text; subject text; key text; seen jsonb; val numeric; total numeric; expected numeric;
 share_count integer; seat_count integer; row_count integer; complete boolean; comparable boolean; weighted boolean;
 round_no integer; other_round integer; age_days integer; delta numeric; previous jsonb; previous_date text:='';
 date_value text; date_field text; finalized boolean:=coalesce(e->>'resultStatus','') in ('final','certified');
begin
 -- Never interpret checked (source-review date) as a result announcement.
 for date_field in select unnest(array['startDate','endDate','checked']) loop
  date_value:=coalesce(e->>date_field,'');
  if date_value<>'' and not electionatlas_private.integrity_date(date_value) then return next electionatlas_private.integrity_finding('DATE_INVALID','error','election',date_field,'Calendar date is invalid.',jsonb_build_object('field',date_field,'value',date_value)); end if;
 end loop;
 if electionatlas_private.integrity_date(e->>'startDate') and electionatlas_private.integrity_date(e->>'endDate') and e->>'endDate'<e->>'startDate' then return next electionatlas_private.integrity_finding('DATE_ORDER','error','election','polling','Polling end precedes polling start.',jsonb_build_object('start',e->>'startDate','end',e->>'endDate')); end if;
 if (e->>'precision'='unknown' and (coalesce(e->>'startDate','')<>'' or coalesce(e->>'endDate','')<>'')) or (coalesce(e->>'precision','unknown')<>'unknown' and coalesce(e->>'startDate','')='') or (e->>'dateStatus'='confirmed' and e->>'precision'<>'day') or (e->>'precision'<>'day' and coalesce(e->>'endDate','')<>'') then
  return next electionatlas_private.integrity_finding('DATE_PRECISION','warning','election','precision','Date fields, precision and confirmation status disagree.',jsonb_build_object('precision',e->'precision','dateStatus',e->'dateStatus','start',e->'startDate','end',e->'endDate')); end if;
 if settings ? 'resultDate' then
  if not electionatlas_private.integrity_date(settings->>'resultDate') then return next electionatlas_private.integrity_finding('RESULT_DATE','error','election','resultDate','Checker result date is invalid.',jsonb_build_object('resultDate',settings->'resultDate'));
  elsif e->>'precision'='day' and electionatlas_private.integrity_date(e->>'startDate') and settings->>'resultDate'<e->>'startDate' then return next electionatlas_private.integrity_finding('RESULT_DATE','warning','election','resultDate','Result announcement precedes polling. Check whether this is a partial announcement or a date error.',jsonb_build_object('resultDate',settings->'resultDate','pollingStart',e->'startDate')); end if;
 end if;
 for field in select unnest(array['totalSeats','majorityThreshold','turnout']) loop
  val:=electionatlas_private.integrity_number(e->field);
  if e ? field and e->field<>'null'::jsonb and (val is null or val<0 or (field<>'turnout' and trunc(val)<>val) or (field='turnout' and val>100)) then return next electionatlas_private.integrity_finding('COUNT_INVALID','error','election',field,'Invalid election-level count or turnout percentage.',jsonb_build_object('field',field,'value',e->field)); end if;
 end loop;
 if jsonb_array_length(electionatlas_private.integrity_array(e->'sources'))=0 then return next electionatlas_private.integrity_finding('SOURCE_MISSING','warning','election','sources','Election has no recorded sources.',jsonb_build_object('publication',e->'publication')); end if;
 if finalized and e->>'resultCoverage'='partial' then return next electionatlas_private.integrity_finding('FINAL_PARTIAL','info','election','coverage','Entered results are final, but archive coverage is partial. This can be a valid historical exception; verify the scope and missing results.',jsonb_build_object('resultStatus',e->'resultStatus','coverage',e->'resultCoverage')); end if;
 tables:=jsonb_build_array(jsonb_build_object('scope','national','results',e->'results','sources',e->'sources','basis',e->'voteBasis','complete',e->>'resultCoverage'='complete','expected',e->'totalSeats','weighted',e->'weightedVotes','method',e->'electionMethod'));
 for c in select value from jsonb_array_elements(electionatlas_private.integrity_array(e->'contests')) loop
  tables:=tables||jsonb_build_array(jsonb_build_object('scope','contest:'||coalesce(c->>'id','unknown'),'results',c->'results','sources',c->'sources','basis',c->'voteBasis','complete',false,'expected',null,'weighted',e->'weightedVotes','method',c->'method'));
 end loop;
 if jsonb_typeof(e->'house')='object' then
  for c in select value from jsonb_array_elements(electionatlas_private.integrity_array(e#>'{house,races}')) loop
   rows:='[]'::jsonb;for r in select value from jsonb_array_elements(electionatlas_private.integrity_array(c->'candidates')) loop rows:=rows||jsonb_build_array(r||jsonb_build_object('share',null,'seats',null)); end loop;
   tables:=tables||jsonb_build_array(jsonb_build_object('scope','district:'||coalesce(c->>'id',c->>'district','unknown'),'results',rows,'sources',case when coalesce(e#>>'{house,source}','')<>'' then jsonb_build_array(e#>>'{house,source}') else '[]'::jsonb end,'complete',false,'expected',null,'basis','District candidate votes','method','direct'));
  end loop;
  if e#>>'{house,results,status}'='final' then
   total:=electionatlas_private.integrity_number(e#>'{house,results,D}')+electionatlas_private.integrity_number(e#>'{house,results,R}')+electionatlas_private.integrity_number(e#>'{house,results,O}');
   if total is distinct from 435::numeric then return next electionatlas_private.integrity_finding('SEAT_TOTAL','warning','house','allocation','The existing US House overview model expects 435 seats; final allocation differs.',jsonb_build_object('expected',435,'entered',total)); end if;
  end if;
 end if;
 for t in select value from jsonb_array_elements(tables) loop
  scope:=t->>'scope';cfg:=coalesce(settings#>array['tables',scope],'{}'::jsonb);rows:=electionatlas_private.integrity_array(t->'results');row_count:=jsonb_array_length(rows);complete:=coalesce((cfg->>'complete')::boolean,(t->>'complete')::boolean,false);weighted:=coalesce((t->>'weighted')::boolean,false);
  expected:=coalesce(electionatlas_private.integrity_number(cfg->'expectedSeats'),electionatlas_private.integrity_number(t->'expected'));
  if row_count=0 and e->>'status'='held' and (scope<>'national' or jsonb_array_length(electionatlas_private.integrity_array(e->'contests'))=0) then return next electionatlas_private.integrity_finding('RESULTS_MISSING',case when finalized and complete then 'error' else 'warning' end,scope,'results','Held election or contest has no entered result rows.',jsonb_build_object('coverageComplete',complete,'resultStatus',e->'resultStatus')); end if;
  if scope<>'national' and jsonb_array_length(electionatlas_private.integrity_array(t->'sources'))=0 then return next electionatlas_private.integrity_finding('SOURCE_MISSING','warning',scope,'sources','Contest lacks its own recorded sources; check whether parent sources cover it.',jsonb_build_object('parentSources',jsonb_array_length(electionatlas_private.integrity_array(e->'sources')))); end if;
  seen:='{}'::jsonb;
  for r in select value from jsonb_array_elements(rows) loop
   subject:=coalesce(nullif(r->>'id',''),electionatlas_private.integrity_normal(r->>'name'));
   for field in select unnest(array['votes','ballotVotes','seats','previousSeats','electoralVotes','share']) loop
    if r ? field and r->field<>'null'::jsonb then
     val:=electionatlas_private.integrity_number(r->field);
     if val is null or val<0 or (field='share' and val>100) or (field<>'share' and trunc(val)<>val and not(field='votes' and coalesce(cfg->>'countMode','integer')='weighted')) then return next electionatlas_private.integrity_finding(case when field='share' then 'SHARE_RANGE' else 'COUNT_INVALID' end,'error',scope,subject||':'||field,'Result count or share is invalid for its recorded basis.',jsonb_build_object('row',r->'name','field',field,'value',r->field,'countMode',coalesce(cfg->>'countMode','integer'))); end if;
    end if;
   end loop;
   key:=electionatlas_private.integrity_normal(r->>'name')||'|'||coalesce(nullif(r->>'partyId',''),electionatlas_private.integrity_normal(r->>'party'));
   if seen ? ('name:'||key) or (nullif(r->>'id','') is not null and seen ? ('id:'||(r->>'id'))) then return next electionatlas_private.integrity_finding('ROW_DUPLICATE','warning',scope,subject,'Potential duplicate party/candidate row within the same table. Separate candidates from the same party remain distinct.',jsonb_build_object('name',r->'name','party',r->'party','id',r->'id'));
   end if;seen:=seen||jsonb_build_object('name:'||key,true);if nullif(r->>'id','') is not null then seen:=seen||jsonb_build_object('id:'||(r->>'id'),true);end if;
  end loop;
  select count(*),coalesce(sum(electionatlas_private.integrity_number(value->'share')),0) into share_count,total from jsonb_array_elements(rows) where electionatlas_private.integrity_number(value->'share') is not null;
  comparable:=coalesce((cfg->>'commonDenominator')::boolean,not weighted and coalesce(t->>'basis','') ~* '(national vote share|valid votes|valid ballots|vote total|total votes|total ballots)' and coalesce(t->>'basis','') !~* '(different|mixed|separate|component|regional|unopposed|candidate selection)');
  if complete and row_count>0 and share_count=row_count and comparable and abs(total-100)>greatest(0.2,row_count*0.05) then return next electionatlas_private.integrity_finding('SHARE_TOTAL','warning',scope,'shares','Complete table appears to share a denominator, but percentages do not total approximately 100%. Check blank ballots, rounding and source conventions.',jsonb_build_object('sum',total,'expected',100,'tolerance',greatest(0.2,row_count*0.05),'basis',t->'basis','explicitDenominator',cfg->'commonDenominator')); end if;
  select count(*),coalesce(sum(electionatlas_private.integrity_number(value->'seats')),0) into seat_count,total from jsonb_array_elements(rows) where electionatlas_private.integrity_number(value->'seats') is not null;
  if complete and row_count>0 and expected is not null and expected>0 and coalesce(cfg->>'seatScope','allocated')<>'not-comparable' and (e->>'type'='parliamentary' or cfg ? 'expectedSeats') then
   if seat_count=row_count and total<>expected then return next electionatlas_private.integrity_finding('SEAT_TOTAL','warning',scope,'seats','Complete allocation differs from this election/component expected seat total. Verify contested seats, partial renewals, appointments and historical vacancies.',jsonb_build_object('entered',total,'expected',expected,'basis','Election-specific totalSeats or moderator context'));
   elsif seat_count<row_count and finalized then return next electionatlas_private.integrity_finding('FINAL_REQUIRED','warning',scope,'seats','Final complete parliamentary table has missing seat allocations. Verify whether these rows are ballot categories with no seat allocation.',jsonb_build_object('rows',row_count,'rowsWithSeats',seat_count,'expected',expected)); end if;
  end if;
  if finalized and complete and row_count>0 and exists(select 1 from jsonb_array_elements(rows) x where coalesce(x->'votes','null'::jsonb)='null'::jsonb and coalesce(x->'share','null'::jsonb)='null'::jsonb and coalesce(x->'seats','null'::jsonb)='null'::jsonb and coalesce(x->'electoralVotes','null'::jsonb)='null'::jsonb) then return next electionatlas_private.integrity_finding('FINAL_REQUIRED','warning',scope,'empty-values','Final complete table contains result rows with no vote, share, seat or electoral allocation.',jsonb_build_object('coverageComplete',true,'resultStatus',e->'resultStatus')); end if;
 end loop;
 round_no:=electionatlas_private.integrity_round(e->>'round');
 for p in select value from jsonb_array_elements(electionatlas_private.integrity_array(peers)) loop
  if p->>'id'=e->>'id' or p->>'countryId' is distinct from e->>'countryId' or p->>'type' is distinct from e->>'type' or electionatlas_private.integrity_normal(p->>'body')<>electionatlas_private.integrity_normal(e->>'body') or coalesce(p#>>'{geography,id}','')<>coalesce(e#>>'{geography,id}','') or coalesce(p->>'overviewId','')<>coalesce(e->>'overviewId','') then continue; end if;
  if nullif(e->>'startDate','') is not null and p->>'startDate'=e->>'startDate' and coalesce(p->>'endDate','')=coalesce(e->>'endDate','') and p->>'precision'=e->>'precision' and electionatlas_private.integrity_normal(p->>'round')=electionatlas_private.integrity_normal(e->>'round') and coalesce(p->>'electionMethod','direct')=coalesce(e->>'electionMethod','direct') and (coalesce(e->>'body','')<>'' or electionatlas_private.integrity_normal(p->>'title')=electionatlas_private.integrity_normal(e->>'title')) and (coalesce(p->>'seriesId','')=coalesce(e->>'seriesId','') or coalesce(p->>'seriesId','')='' or coalesce(e->>'seriesId','')='') then return next electionatlas_private.integrity_finding('ELECTION_DUPLICATE','warning','election',p->>'id','Potential duplicate election with matching country, type, polling interval, chamber, round and geographic/component identity. Do not merge automatically.',jsonb_build_object('otherElection',p->>'id','date',e->'startDate','round',e->'round','body',e->'body','geography',e->'geography')); end if;
  if e->>'precision'<>'day' or p->>'precision'<>'day' or not electionatlas_private.integrity_date(e->>'startDate') or not electionatlas_private.integrity_date(p->>'startDate') then continue;end if;
  age_days:=abs((e->>'startDate')::date-(p->>'startDate')::date);other_round:=electionatlas_private.integrity_round(p->>'round');
  if round_no is not null and other_round is not null and round_no<>other_round and age_days<=180 and ((coalesce(e->>'seriesId','')<>'' and e->>'seriesId'=p->>'seriesId') or electionatlas_private.integrity_array(e->'linkedElectionIds') ? (p->>'id')) and ((round_no>other_round and e->>'startDate'<p->>'startDate') or (round_no<other_round and e->>'startDate'>p->>'startDate')) then return next electionatlas_private.integrity_finding('ROUND_ORDER','warning','election',p->>'id','Numbered rounds in the same election cycle appear out of chronological order. Verify postponed/rerun rounds.',jsonb_build_object('round',e->'round','date',e->'startDate','otherElection',p->'id','otherRound',p->'round','otherDate',p->'startDate'));end if;
  if p->>'startDate'<e->>'startDate' and p->>'startDate'>previous_date and age_days>=180 and age_days<=3653 and coalesce(e->>'seriesId','')<>'' and p->>'seriesId'=e->>'seriesId' and electionatlas_private.integrity_normal(p->>'round')=electionatlas_private.integrity_normal(e->>'round') and e->>'resultCoverage'='complete' and p->>'resultCoverage'='complete' and coalesce(p->>'voteBasis','')=coalesce(e->>'voteBasis','') and coalesce(p->>'electionMethod','direct')=coalesce(e->>'electionMethod','direct') then previous:=p;previous_date:=p->>'startDate';end if;
 end loop;
 if previous is not null then
  expected:=electionatlas_private.integrity_number(e->'totalSeats');val:=electionatlas_private.integrity_number(previous->'totalSeats');
  if expected>0 and val>0 and abs(expected-val)/val>=0.25 then return next electionatlas_private.integrity_finding('CHANGE_ANOMALY','info','election','capacity','Recorded component size changed by at least 25% from the previous comparable election. Boundaries and historical reforms can explain this.',jsonb_build_object('previousElection',previous->'id','previousSeats',val,'currentSeats',expected)); end if;
  if not coalesce((e->>'weightedVotes')::boolean,false) and coalesce(e->>'electionMethod','direct')='direct' then
   for r in select value from jsonb_array_elements(electionatlas_private.integrity_array(e->'results')) loop
    if nullif(r->>'partyId','') is null then continue; end if;
    select value into p from jsonb_array_elements(electionatlas_private.integrity_array(previous->'results')) where value->>'partyId'=r->>'partyId' limit 1;
    delta:=abs(electionatlas_private.integrity_number(r->'share')-electionatlas_private.integrity_number(p->'share'));
    if delta>=25 then return next electionatlas_private.integrity_finding('CHANGE_ANOMALY','info','national',r->>'partyId','Saved party vote share changed by at least 25 percentage points from the previous comparable election. This is an anomaly, not presumed error.',jsonb_build_object('party',r->'name','previousElection',previous->'id','previousShare',p->'share','currentShare',r->'share','changePoints',delta));end if;
   end loop;
  end if;
 end if;
end $$;
create index ea_integrity_family on public.ea_records((data->>'countryId'),(data->>'type'),(data->>'body'),(data->>'seriesId')) where kind='world_election';

create or replace function electionatlas_private.integrity_enqueue_family(e jsonb) returns void language sql set search_path='' as $$
 insert into electionatlas_private.integrity_queue(record_id)
 select id from public.ea_records where kind='world_election' and (id=e->>'id' or (data->>'countryId'=e->>'countryId' and data->>'type'=e->>'type' and electionatlas_private.integrity_normal(data->>'body')=electionatlas_private.integrity_normal(e->>'body')) or electionatlas_private.integrity_array(e->'linkedElectionIds') ? id or electionatlas_private.integrity_array(data->'linkedElectionIds') ? (e->>'id'))
 on conflict(record_id) do update set enqueued_at=clock_timestamp(),attempts=0,next_attempt=now(),last_error=null;
$$;
create or replace function electionatlas_private.integrity_enqueue_trigger() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if tg_op='DELETE' then if old.kind='world_election' then perform electionatlas_private.integrity_enqueue_family(old.data);insert into electionatlas_private.integrity_queue(record_id) values(old.id) on conflict(record_id) do update set enqueued_at=clock_timestamp();end if;return old;end if;
 if new.kind='world_election' and (tg_op='INSERT' or (new.data-array['version','checked','live','publication','articleId','government','coalitionNotes','summary','legitimacy','observers']) is distinct from (old.data-array['version','checked','live','publication','articleId','government','coalitionNotes','summary','legitimacy','observers'])) then
  if tg_op='UPDATE' then perform electionatlas_private.integrity_enqueue_family(old.data);end if;
  perform electionatlas_private.integrity_enqueue_family(new.data);
 end if;return new;
end $$;
create trigger ea_integrity_enqueue after insert or update or delete on public.ea_records for each row execute function electionatlas_private.integrity_enqueue_trigger();

create or replace function electionatlas_private.integrity_full_scan() returns uuid language plpgsql set search_path='' as $$
declare sid uuid; begin
 perform pg_advisory_xact_lock(hashtextextended('electionatlas-integrity-worker',0));
 perform pg_advisory_xact_lock(hashtextextended('electionatlas-integrity-full',0));
 select id into sid from public.ea_integrity_scans where mode='full' and status='running' order by started_at desc limit 1;if sid is not null then return sid;end if;
 insert into public.ea_integrity_scans(mode,records_target,requested_by) select 'full',count(*),auth.uid() from public.ea_records where kind='world_election' returning id into sid;
 insert into electionatlas_private.integrity_queue(record_id,scan_id) select id,sid from public.ea_records where kind='world_election'
 on conflict(record_id) do update set scan_id=excluded.scan_id,enqueued_at=clock_timestamp(),attempts=0,next_attempt=now(),last_error=null;
 return sid;
end $$;

create or replace function electionatlas_private.integrity_process(batch_size integer default 100) returns integer language plpgsql set search_path='' as $$
declare q record; e jsonb; peers jsonb; cfg jsonb; f jsonb; k text; fp text; sid uuid; seen text[]; done integer:=0; scan_record record;
begin
 if not pg_try_advisory_xact_lock(hashtextextended('electionatlas-integrity-worker',0)) then return 0;end if;
 if not exists(select 1 from electionatlas_private.integrity_queue where next_attempt<=now()) then return 0;end if;
 insert into public.ea_integrity_scans(mode) values('incremental') returning id into sid;
 for q in select * from electionatlas_private.integrity_queue where next_attempt<=now() order by enqueued_at,record_id limit greatest(1,least(batch_size,200)) loop
  begin
   select data into e from public.ea_records where id=q.record_id and kind='world_election';seen:=array[]::text[];
   if e is not null then
    select settings into cfg from public.ea_integrity_context where record_id=q.record_id;
    select coalesce(jsonb_agg(data-array['contests','house','notes','sources','summary','government','legitimacy','observers','live']),'[]'::jsonb) into peers from public.ea_records where kind='world_election' and id<>q.record_id and data->>'countryId'=e->>'countryId' and data->>'type'=e->>'type' and electionatlas_private.integrity_normal(data->>'body')=electionatlas_private.integrity_normal(e->>'body') and (data->>'startDate'=e->>'startDate' or (coalesce(e->>'seriesId','')<>'' and data->>'seriesId'=e->>'seriesId') or electionatlas_private.integrity_array(e->'linkedElectionIds') ? id);
    for f in select * from electionatlas_private.integrity_rules(e,coalesce(cfg,'{}'::jsonb),peers) loop
     k:=md5(q.record_id||'|'||(f->>'rule')||'|'||(f->>'scope')||'|'||(f->>'subject'));fp:=md5((f->'evidence')::text||'|'||(f->>'explanation'));seen:=array_append(seen,k);
     insert into public.ea_integrity_findings as existing(finding_key,record_id,rule,severity,scope,subject,explanation,evidence,fingerprint,country_id,election_title,election_type)
     values(k,q.record_id,f->>'rule',f->>'severity',f->>'scope',f->>'subject',f->>'explanation',f->'evidence',fp,coalesce(e->>'countryId',''),coalesce(e->>'title',''),coalesce(e->>'type',''))
     on conflict(finding_key) do update set severity=excluded.severity,explanation=excluded.explanation,evidence=excluded.evidence,fingerprint=excluded.fingerprint,active=true,last_seen=now(),resolved_at=null,country_id=excluded.country_id,election_title=excluded.election_title,election_type=excluded.election_type,rules_version='1',
      review_status=case when existing.review_status='accepted-exception' and existing.fingerprint=excluded.fingerprint and existing.active then existing.review_status else 'open' end;
    end loop;
    insert into electionatlas_private.integrity_checked values(q.record_id,now(),md5(e::text),'1') on conflict(record_id) do update set checked_at=excluded.checked_at,fingerprint=excluded.fingerprint,rules_version=excluded.rules_version;
   else delete from electionatlas_private.integrity_checked where record_id=q.record_id;end if;
   update public.ea_integrity_findings set active=false,review_status='fixed',resolved_at=now() where record_id=q.record_id and active and not(finding_key=any(seen));
   if q.scan_id is not null then update public.ea_integrity_scans set records_scanned=records_scanned+1 where id=q.scan_id;end if;
   -- An edit committed after this snapshot must remain queued. Never lose it.
   delete from electionatlas_private.integrity_queue where record_id=q.record_id and enqueued_at=q.enqueued_at;
   update electionatlas_private.integrity_queue set scan_id=null where record_id=q.record_id and scan_id=q.scan_id;
   done:=done+1;
  exception when others then update electionatlas_private.integrity_queue set attempts=attempts+1,last_error=left(sqlerrm,500),next_attempt=now()+interval '1 minute'*least(attempts+1,10) where record_id=q.record_id;end;
 end loop;
 update public.ea_integrity_scans set records_scanned=done,records_target=done,status='completed',finished_at=now() where id=sid;
 update public.ea_integrity_scans s set status='completed',finished_at=now() where mode='full' and status='running' and not exists(select 1 from electionatlas_private.integrity_queue pending where pending.scan_id=s.id);
 return done;
end $$;

-- The only privileged API implementation lives in the non-exposed schema.
create or replace function electionatlas_private.integrity_api(action text,args jsonb default '{}'::jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare result jsonb; n integer; sid uuid; f public.ea_integrity_findings; status text; note text; rid text; cfg jsonb;
begin
 if auth.uid() is null or not exists(select 1 from public.ea_editors where user_id=auth.uid()) then raise exception 'Moderator access required' using errcode='42501';end if;
 if action='scan' then sid:=electionatlas_private.integrity_full_scan();return jsonb_build_object('scanId',sid);
 elsif action='process' then n:=electionatlas_private.integrity_process(100);return jsonb_build_object('processed',n);
 elsif action='review' then
  status:=args->>'status';note:=btrim(coalesce(args->>'note',''));
  if status not in ('open','fixed','accepted-exception') or status is null or length(note)>5000 or (status='accepted-exception' and note='') then raise exception 'Choose a review status; accepted exceptions require a note';end if;
  select * into f from public.ea_integrity_findings where finding_key=args->>'key' for update;
  if f.finding_key is null or f.fingerprint is distinct from args->>'fingerprint' then raise exception 'Finding changed; refresh before reviewing' using errcode='PT409';end if;
  if not f.active and status<>'fixed' then raise exception 'Finding no longer occurs; run a scan to verify recurrence';end if;
  insert into public.ea_integrity_reviews(finding_key,status,note,fingerprint,reviewed_by) values(f.finding_key,status,note,f.fingerprint,auth.uid());
  update public.ea_integrity_findings set review_status=status,review_note=note,reviewed_at=now(),reviewed_by=auth.uid() where finding_key=f.finding_key;
  if status='fixed' and f.active then insert into electionatlas_private.integrity_queue(record_id) values(f.record_id) on conflict(record_id) do update set enqueued_at=clock_timestamp(),next_attempt=now();end if;
  return jsonb_build_object('ok',true);
 elsif action='context' then
  rid:=args->>'recordId';cfg:=args->'settings';note:=btrim(coalesce(args->>'note',''));
  if jsonb_typeof(cfg) is distinct from 'object' or octet_length(cfg::text)>19000 or note='' or length(note)>5000 or not exists(select 1 from public.ea_records where id=rid and kind='world_election') then raise exception 'Choose an existing election and supply checker context with a rationale';end if;
  if cfg ? 'resultDate' and not electionatlas_private.integrity_date(cfg->>'resultDate') then raise exception 'Invalid result date';end if;
  if cfg ? 'tables' then
   if jsonb_typeof(cfg->'tables')<>'object' then raise exception 'Tables must be an object';end if;
   for rid,result in select key,value from jsonb_each(cfg->'tables') loop
    if jsonb_typeof(result)<>'object' or (result ? 'complete' and jsonb_typeof(result->'complete')<>'boolean') or (result ? 'commonDenominator' and jsonb_typeof(result->'commonDenominator')<>'boolean') or (result ? 'expectedSeats' and (electionatlas_private.integrity_number(result->'expectedSeats') is null or electionatlas_private.integrity_number(result->'expectedSeats')<0 or trunc(electionatlas_private.integrity_number(result->'expectedSeats'))<>electionatlas_private.integrity_number(result->'expectedSeats'))) or (result ? 'countMode' and result->>'countMode' not in ('integer','weighted')) or (result ? 'seatScope' and result->>'seatScope' not in ('allocated','not-comparable')) then raise exception 'Invalid checker table context';end if;
   end loop;
  end if;
  rid:=args->>'recordId';insert into public.ea_integrity_context(record_id,settings,note,updated_by) values(rid,cfg,note,auth.uid()) on conflict(record_id) do update set settings=excluded.settings,note=excluded.note,updated_by=excluded.updated_by,updated_at=now();
  insert into electionatlas_private.integrity_queue(record_id) values(rid) on conflict(record_id) do update set enqueued_at=clock_timestamp(),next_attempt=now(),attempts=0,last_error=null;
  return jsonb_build_object('ok',true);
 elsif action='dashboard' then
  select jsonb_build_object(
   'recordsTotal',(select count(*) from public.ea_records where kind='world_election'),
   'recordsScanned',(select count(*) from electionatlas_private.integrity_checked),
   'lastChecked',(select max(checked_at) from electionatlas_private.integrity_checked),
   'lastFullScan',(select to_jsonb(s) from public.ea_integrity_scans s where mode='full' order by started_at desc limit 1),
   'pending',(select count(*) from electionatlas_private.integrity_queue),
   'failures',(select count(*) from electionatlas_private.integrity_queue where last_error is not null),
   'counts',(select jsonb_build_object('error',count(*) filter(where active and severity='error'),'warning',count(*) filter(where active and severity='warning'),'info',count(*) filter(where active and severity='info'),'open',count(*) filter(where active and review_status='open')) from public.ea_integrity_findings),
   'countries',(select coalesce(jsonb_agg(jsonb_build_object('id',data->>'id','name',data->>'name') order by data->>'name'),'[]'::jsonb) from public.ea_records where kind='world_country')) into result;return result;
 else raise exception 'Unknown integrity operation';end if;
end $$;
-- Revoke default PUBLIC execution on every helper; callers cannot submit arbitrary rules or worker payloads.
revoke all on all functions in schema electionatlas_private from public,anon,authenticated;
grant usage on schema electionatlas_private to authenticated;
grant execute on function electionatlas_private.integrity_api(text,jsonb) to authenticated;
create or replace function public.ea_integrity(action text,args jsonb default '{}'::jsonb) returns jsonb language sql security invoker set search_path='' as $$ select electionatlas_private.integrity_api(action,args) $$;
revoke all on function public.ea_integrity(text,jsonb) from public,anon;
grant execute on function public.ea_integrity(text,jsonb) to authenticated;

-- No HTTP calls, browser session or secret API keys are needed for automation.
create extension if not exists pg_cron;
select cron.schedule('ea-data-integrity-worker','* * * * *','select electionatlas_private.integrity_process(100)');
select cron.schedule('ea-data-integrity-nightly','20 2 * * *','select electionatlas_private.integrity_full_scan()');
