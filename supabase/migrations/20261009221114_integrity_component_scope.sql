-- Explicit geography wins; legacy records can encode the constituency in titles.
create or replace function electionatlas_private.integrity_scope(e jsonb) returns text language sql immutable set search_path='' as $$
 select coalesce(nullif(e#>>'{geography,id}',''),substring(electionatlas_private.integrity_normal(e->>'title') from '(?:electoral district|constituency|district|province|college) [[:alnum:]-]+'),'');
$$;
revoke all on function electionatlas_private.integrity_scope(jsonb) from public,anon,authenticated;
create index ea_integrity_overview on public.ea_records((data->>'overviewId')) where kind='world_election';
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
 if (e->>'precision'='unknown' and (coalesce(e->>'startDate','')<>'' or coalesce(e->>'endDate','')<>'' or e->>'dateStatus'<>'tba')) or (coalesce(e->>'precision','unknown')<>'unknown' and coalesce(e->>'startDate','')='') or (e->>'dateStatus'='confirmed' and e->>'precision'<>'day') or (e->>'precision'<>'day' and coalesce(e->>'endDate','')<>'') then
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
 if coalesce(e->>'regionalOverview','')<>'' and e->>'status'='held' and not exists(select 1 from jsonb_array_elements(electionatlas_private.integrity_array(peers)) child where child->>'overviewId'=e->>'id' and jsonb_array_length(electionatlas_private.integrity_array(child->'results'))>0) then return next electionatlas_private.integrity_finding('RESULTS_MISSING','warning','components','results','Regional overview has no child election with entered results. Its own empty aggregate table can be valid.',jsonb_build_object('regionalOverview',e->'regionalOverview'));end if;
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
  if row_count=0 and e->>'status'='held' and (scope<>'national' or (jsonb_array_length(electionatlas_private.integrity_array(e->'contests'))=0 and coalesce(e->>'regionalOverview','')='')) then return next electionatlas_private.integrity_finding('RESULTS_MISSING',case when finalized and complete then 'error' else 'warning' end,scope,'results','Held election or contest has no entered result rows.',jsonb_build_object('coverageComplete',complete,'resultStatus',e->'resultStatus')); end if;
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
  if p->>'id'=e->>'id' or p->>'countryId' is distinct from e->>'countryId' or p->>'type' is distinct from e->>'type' or electionatlas_private.integrity_normal(p->>'body')<>electionatlas_private.integrity_normal(e->>'body') or electionatlas_private.integrity_scope(p)<>electionatlas_private.integrity_scope(e) or coalesce(p->>'overviewId','')<>coalesce(e->>'overviewId','') then continue; end if;
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
create or replace function electionatlas_private.integrity_enqueue_family(e jsonb) returns void language sql set search_path='' as $$
 insert into electionatlas_private.integrity_queue(record_id)
 select id from public.ea_records where kind='world_election' and (id=e->>'id' or id=e->>'overviewId' or data->>'overviewId'=e->>'id' or (data->>'countryId'=e->>'countryId' and data->>'type'=e->>'type' and electionatlas_private.integrity_normal(data->>'body')=electionatlas_private.integrity_normal(e->>'body')) or electionatlas_private.integrity_array(e->'linkedElectionIds') ? id or electionatlas_private.integrity_array(data->'linkedElectionIds') ? (e->>'id'))
 on conflict(record_id) do update set enqueued_at=clock_timestamp(),attempts=0,next_attempt=now(),last_error=null;
$$;
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
    select coalesce(jsonb_agg(data-array['contests','house','notes','sources','summary','government','legitimacy','observers','live']),'[]'::jsonb) into peers from public.ea_records where kind='world_election' and id<>q.record_id and (data->>'overviewId'=e->>'id' or (data->>'countryId'=e->>'countryId' and data->>'type'=e->>'type' and electionatlas_private.integrity_normal(data->>'body')=electionatlas_private.integrity_normal(e->>'body') and (data->>'startDate'=e->>'startDate' or (coalesce(e->>'seriesId','')<>'' and data->>'seriesId'=e->>'seriesId') or electionatlas_private.integrity_array(e->'linkedElectionIds') ? id)));
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

create policy integrity_worker_only on electionatlas_private.integrity_queue for all to postgres using(true) with check(true);
create policy integrity_worker_only on electionatlas_private.integrity_checked for all to postgres using(true) with check(true);
revoke all on function electionatlas_private.integrity_rules(jsonb,jsonb,jsonb),electionatlas_private.integrity_enqueue_family(jsonb),electionatlas_private.integrity_process(integer) from public,anon,authenticated;
