-- Run as database owner after the migration. All fixtures, reviews and scans roll back.
begin;
create function pg_temp.assert_rules(e jsonb,required text[],forbidden text[] default array[]::text[],settings jsonb default '{}'::jsonb,peers jsonb default '[]'::jsonb) returns void language plpgsql as $$
declare found text[]; r text;begin
 select coalesce(array_agg(f->>'rule'),array[]::text[]) into found from electionatlas_private.integrity_rules(e,settings,peers) f;
 foreach r in array required loop if not r=any(found) then raise exception 'Expected rule %, got %',r,found;end if;end loop;
 foreach r in array forbidden loop if r=any(found) then raise exception 'Unexpected rule %, got %',r,found;end if;end loop;
end $$;
do $$ declare e jsonb; p jsonb; c jsonb;begin
 e:='{"id":"world-integrity-test","countryId":"test","title":"General election","type":"parliamentary","body":"Historical elected component","startDate":"2024-05-20","endDate":"","checked":"2020-01-01","precision":"day","dateStatus":"confirmed","status":"held","resultStatus":"final","resultCoverage":"complete","totalSeats":10,"electionMethod":"direct","round":"General","seriesId":"test-component","voteBasis":"National vote share","sources":[{"label":"Official","url":"https://example.org"}],"results":[{"id":"a","name":"Alpha","party":"Alpha","partyId":"saved-alpha","votes":60,"share":60,"seats":6},{"id":"b","name":"Beta","party":"Beta","votes":40,"share":40,"seats":4}]}';
 perform pg_temp.assert_rules(e,array[]::text[],array['COUNT_INVALID','SHARE_RANGE','SHARE_TOTAL','SEAT_TOTAL','FINAL_REQUIRED','SOURCE_MISSING','RESULTS_MISSING','DATE_INVALID','RESULT_DATE']);
 -- Historical capacity is the specific record's ten seats, not a modern national total.
 perform pg_temp.assert_rules(jsonb_set(e,'{totalSeats}','12'),array['SEAT_TOTAL']);
 perform pg_temp.assert_rules(jsonb_set(e,'{resultCoverage}','"partial"'),array['FINAL_PARTIAL'],array['SEAT_TOTAL','SHARE_TOTAL','FINAL_REQUIRED']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,votes}','-1'),array['COUNT_INVALID']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,seats}','2.5'),array['COUNT_INVALID']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','101'),array['SHARE_RANGE']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','50'),array['SHARE_TOTAL']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','50'),array[]::text[],array['SHARE_TOTAL'],'{"tables":{"national":{"commonDenominator":false}}}');
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','50')||'{"weightedVotes":true}',array[]::text[],array['SHARE_TOTAL']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,votes}','0.5'),array['COUNT_INVALID']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,votes}','0.5'),array[]::text[],array['COUNT_INVALID'],'{"tables":{"national":{"countMode":"weighted"}}}');
 perform pg_temp.assert_rules(e||'{"startDate":"2023-02-29"}',array['DATE_INVALID']);
 perform pg_temp.assert_rules(e||'{"endDate":"2024-05-19"}',array['DATE_ORDER']);
 perform pg_temp.assert_rules(e||'{"precision":"year"}',array['DATE_PRECISION']);
 perform pg_temp.assert_rules(e,array['RESULT_DATE'],array[]::text[],'{"resultDate":"2024-05-19"}');
 perform pg_temp.assert_rules(e||'{"sources":[],"results":[]}',array['SOURCE_MISSING','RESULTS_MISSING']);
 perform pg_temp.assert_rules(e||'{"status":"scheduled","resultStatus":"not-entered","results":[]}',array[]::text[],array['RESULTS_MISSING']);
 perform pg_temp.assert_rules(jsonb_set(e,'{results}',(e->'results')||jsonb_build_array(e#>'{results,0}')),array['ROW_DUPLICATE']);
 p:=e||'{"id":"world-integrity-other"}';
 perform pg_temp.assert_rules(e,array['ELECTION_DUPLICATE'],array[]::text[],'{}',jsonb_build_array(p));
 perform pg_temp.assert_rules(e,array[]::text[],array['ELECTION_DUPLICATE'],'{}',jsonb_build_array(p||'{"body":"Other chamber"}'));
 perform pg_temp.assert_rules(e||'{"geography":{"id":"one"}}',array[]::text[],array['ELECTION_DUPLICATE'],'{}',jsonb_build_array(p||'{"geography":{"id":"two"}}'));
 perform pg_temp.assert_rules(e||'{"round":"First round"}',array['ROUND_ORDER'],array['ELECTION_DUPLICATE'],'{}',jsonb_build_array(p||'{"round":"Second round","startDate":"2024-05-19"}'));
 perform pg_temp.assert_rules(e||'{"round":"Second round"}',array[]::text[],array['ROUND_ORDER'],'{}',jsonb_build_array(p||'{"round":"First round","startDate":"2024-05-19"}'));
 perform pg_temp.assert_rules(e||'{"title":"Council: electoral district 3"}',array[]::text[],array['ELECTION_DUPLICATE'],'{}',jsonb_build_array(p||'{"title":"Council: electoral district 6"}'));
 perform pg_temp.assert_rules(e||'{"regionalOverview":"electoral-college","results":[]}',array[]::text[],array['RESULTS_MISSING'],'{}',jsonb_build_array(p||'{"overviewId":"world-integrity-test"}'));
 perform pg_temp.assert_rules(e||'{"regionalOverview":"electoral-college","results":[]}',array['RESULTS_MISSING']);
 -- Presidential electoral allocations do not sum to a single office seat.
 perform pg_temp.assert_rules(e||'{"type":"presidential","totalSeats":1,"results":[{"name":"A","votes":60,"share":60,"electoralVotes":300},{"name":"B","votes":40,"share":40,"electoralVotes":238}]}',array[]::text[],array['SEAT_TOTAL','FINAL_REQUIRED']);
 -- Separate constituency shares sum to 200 across tables, which is valid.
 c:=jsonb_build_object('id','race-a','method','direct','voteBasis','Valid votes','sources',e->'sources','results',e->'results');
 perform pg_temp.assert_rules(e||jsonb_build_object('results','[]'::jsonb,'contests',jsonb_build_array(c,c||'{"id":"race-b"}')),array[]::text[],array['RESULTS_MISSING','SHARE_TOTAL','ROW_DUPLICATE','SEAT_TOTAL']);
 perform pg_temp.assert_rules(e||jsonb_build_object('results','[]'::jsonb,'contests',jsonb_build_array(c||'{"results":[]}')),array['RESULTS_MISSING']);
 p:=jsonb_set(e||'{"id":"world-integrity-previous","startDate":"2020-05-20"}','{results,0,share}','10');
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','90'),array['CHANGE_ANOMALY'],array[]::text[],'{}',jsonb_build_array(p));
 perform pg_temp.assert_rules(jsonb_set(e,'{results,0,share}','90')||'{"voteBasis":"Different ballot denominator"}',array[]::text[],array['CHANGE_ANOMALY'],'{}',jsonb_build_array(p));
end $$;

insert into auth.users(id,email,raw_user_meta_data) values('00000000-0000-4000-8000-000000000201','integrity-reader@example.invalid','{"username":"integrity_test_reader","role":"admin"}'),('00000000-0000-4000-8000-000000000202','integrity-moderator@example.invalid','{"username":"integrity_test_moderator"}');
insert into public.ea_editors(user_id) values('00000000-0000-4000-8000-000000000202');
insert into public.ea_records(id,kind,data) values('world-integrity-persist','world_election','{"id":"world-integrity-persist","countryId":"test","title":"Private test","type":"parliamentary","body":"Test component","startDate":"2024-05-20","endDate":"","checked":"","precision":"day","dateStatus":"confirmed","status":"held","resultStatus":"final","resultCoverage":"complete","totalSeats":10,"electionMethod":"direct","round":"General","seriesId":"test","voteBasis":"National vote share","sources":[],"results":[],"publication":"draft"}');
-- Isolate this test's worker queue transactionally, without touching the archive.
delete from electionatlas_private.integrity_queue where record_id<>'world-integrity-persist';
select electionatlas_private.integrity_process(100);
do $$ begin if not exists(select 1 from public.ea_integrity_findings where record_id='world-integrity-persist') then raise exception 'Worker did not persist findings';end if;end $$;
set local role anon;
do $$ begin
 begin perform count(*) from public.ea_integrity_findings;raise exception 'Anonymous findings access';exception when insufficient_privilege then null;end;
 begin perform public.ea_integrity('dashboard');raise exception 'Anonymous RPC access';exception when insufficient_privilege then null;end;
 begin perform electionatlas_private.integrity_process(100);raise exception 'Anonymous worker access';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000201',true);
set local role authenticated;
do $$ begin
 if exists(select 1 from public.ea_integrity_findings) or exists(select 1 from public.ea_integrity_scans) or exists(select 1 from public.ea_integrity_context) or exists(select 1 from public.ea_integrity_reviews) then raise exception 'Reader sees operational data';end if;
 begin perform public.ea_integrity('dashboard');raise exception 'Reader RPC access';exception when insufficient_privilege then null;end;
 begin perform electionatlas_private.integrity_process(100);raise exception 'Reader worker access';exception when insufficient_privilege then null;end;
 begin update public.ea_integrity_findings set review_status='fixed';raise exception 'Reader direct update';exception when insufficient_privilege then null;end;
end $$;
reset role;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000202',true);
set local role authenticated;
do $$ declare f public.ea_integrity_findings;begin
 perform public.ea_integrity('dashboard');select * into f from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING';
 begin perform public.ea_integrity('review',jsonb_build_object('key',f.finding_key,'fingerprint',f.fingerprint,'status','accepted-exception','note',''));raise exception 'Empty exception note accepted';exception when raise_exception then if sqlerrm='Empty exception note accepted' then raise;end if;end;
 perform public.ea_integrity('review',jsonb_build_object('key',f.finding_key,'fingerprint',f.fingerprint,'status','accepted-exception','note','Fixture: documented source gap'));
 begin perform public.ea_integrity('review',jsonb_build_object('key',f.finding_key,'fingerprint','stale','status','open'));raise exception 'Stale review accepted';exception when sqlstate 'PT409' then null;end;
 -- Even moderators cannot forge findings through direct writes.
 begin update public.ea_integrity_findings set evidence='{}';raise exception 'Direct findings write succeeded';exception when insufficient_privilege then null;end;
end $$;
reset role;
-- Rescan unchanged evidence: no duplicate alerts and accepted exception persists.
insert into electionatlas_private.integrity_queue(record_id) values('world-integrity-persist') on conflict(record_id) do update set enqueued_at=clock_timestamp();
select electionatlas_private.integrity_process(100);
do $$ begin
 if (select count(*) from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING')<>1 then raise exception 'Duplicate alerts';end if;
 if not exists(select 1 from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING' and review_status='accepted-exception') then raise exception 'Acceptance lost';end if;
end $$;
-- Altering evidence reopens accepted finding; removing condition resolves it.
update public.ea_records set data=data||'{"publication":"published"}' where id='world-integrity-persist';
insert into electionatlas_private.integrity_queue(record_id) values('world-integrity-persist') on conflict(record_id) do update set enqueued_at=clock_timestamp();
select electionatlas_private.integrity_process(100);
do $$ begin if not exists(select 1 from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING' and review_status='open') then raise exception 'Changed evidence did not reopen';end if;end $$;
update public.ea_records set data=data||'{"sources":[{"label":"Official","url":"https://example.org"}]}' where id='world-integrity-persist';
select electionatlas_private.integrity_process(100);
do $$ begin if not exists(select 1 from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING' and review_status='fixed' and not active) then raise exception 'Resolved finding remains open';end if;end $$;
update public.ea_records set data=data||'{"sources":[]}' where id='world-integrity-persist';
select electionatlas_private.integrity_process(100);
do $$ begin if not exists(select 1 from public.ea_integrity_findings where record_id='world-integrity-persist' and rule='SOURCE_MISSING' and review_status='open' and active) then raise exception 'Recurrence did not reopen';end if;end $$;
rollback;
select 'Passed integrity rules, historical/system exceptions, constituencies, rounds, persistence, review lifecycle and anon/reader/moderator permissions; all fixtures rolled back' as result;
