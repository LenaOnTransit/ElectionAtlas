import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){
 let src=fs.readFileSync(file,'utf8');
 for(const [from,to] of Object.entries(imports))src=src.replaceAll("'"+from+"'","'"+to+"'");
 return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const partyModel=await import(moduleUrl('lib/country-parties.ts'));
const root='scripts/swiss-election-import/';
const records=JSON.parse(fs.readFileSync(root+'records.json')),parties=JSON.parse(fs.readFileSync(root+'parties.json'));
const audit=JSON.parse(fs.readFileSync(root+'reconciliation.json')),primary=JSON.parse(fs.readFileSync(root+'primary-reconciliation.json'));
const ids=new Set(records.map(e=>e.id)),profiles=new Map(parties.map(p=>[p.id,p]));
assert.equal(records.length,395);assert.equal(ids.size,records.length);
for(const p of parties)partyModel.validateParty(p);
for(const e of records){
 try{model.validateWorldElection(e);}catch(error){console.error(e.id,error.message);process.exit(1);}
 assert.equal(e.countryId,'ch');assert.equal(e.publication,'published');assert.equal(e.live?.enabled||false,false);assert.ok(e.sources.length);assert.ok(!e.legitimacy);
 for(const id of e.linkedElectionIds||[])assert.ok(ids.has(id));if(e.overviewId)assert.ok(ids.has(e.overviewId));
 for(const r of e.results)if(r.partyId){assert.ok(profiles.has(r.partyId));assert.equal(r.color,profiles.get(r.partyId).color);assert.deepEqual(r.ideologyIds,[]);assert.ok(!['Independent','Affiliation not verified','Unattributed ballots'].includes(r.party));}
 const a=audit.find(a=>a.id===e.id);assert.ok(a);assert.equal(e.results.reduce((n,r)=>n+(r.votes||0),0),a.recordedVotes);assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),a.recordedSeats);
 if(e.resultCoverage==='complete'){if(a.expectedVotes!==null)assert.equal(a.recordedVotes,a.expectedVotes);if(a.expectedSeats!==null)assert.equal(a.recordedSeats,a.expectedSeats);}
}
const get=id=>records.find(e=>e.id===id);
const national=records.filter(e=>e.seriesId==='ch-national-council'),states=records.filter(e=>e.seriesId==='ch-states'),ballots=records.filter(e=>e.seriesId==='ch-federal-council-ballots');
assert.equal(national.length,52);assert.equal(states.length,44);assert.equal(ballots.length,60);
for(const e of national){assert.equal(e.resultCoverage,'complete');assert.ok(e.results.every(r=>r.votes===null));if(e.startDate<'1919')assert.ok(e.results.every(r=>r.share===null));}
for(const e of states){assert.equal(e.precision,'year');assert.equal(e.dateStatus,'expected');assert.equal(e.turnout,null);assert.ok(e.results.every(r=>r.votes===null&&r.share===null));assert.equal(e.totalSeats,e.startDate<'1979'?44:46);assert.ok(!e.electionMethod);}
assert.equal(get('world-switzerland-states-1939-01-01').resultCoverage,'partial');assert.equal(get('world-switzerland-states-1939-01-01').results.reduce((n,r)=>n+r.seats,0),43);
for(const p of primary.nationalCouncil){const e=national.find(e=>e.startDate.startsWith(String(p.year)));assert.equal(e.totalSeats,200);assert.equal(e.results.length,p.rows.length);for(let i=0;i<p.rows.length;i++){assert.equal(e.results[i].seats,p.rows[i].seats);assert.equal(e.results[i].share,p.rows[i].share);}assert.ok(e.sources.some(s=>s.url.includes('pxweb.bfs.admin.ch')));}
for(const [year,date] of Object.entries(primary.nationalDates))assert.equal(national.find(e=>e.startDate.startsWith(year)).startDate,date);
assert.equal(get('world-switzerland-national-council-1848-10-01').precision,'month');assert.equal(get('world-switzerland-national-council-1848-10-01').totalSeats,111);
const latest=get('world-switzerland-national-council-2023-10-22');assert.equal(latest.results.find(r=>r.name==="Swiss People's Party").seats,62);assert.equal(latest.results.find(r=>r.name==="Swiss People's Party").share,27.93);assert.equal(latest.results.find(r=>r.name==='Social Democratic Party').seats,41);
const st=get('world-switzerland-states-2023-01-01');assert.equal(st.results.reduce((n,r)=>n+r.seats,0),46);assert.equal(st.results.find(r=>r.name==='The Centre').seats,15);assert.equal(st.results.find(r=>r.name==='FDP.The Liberals').seats,11);
for(const p of primary.presidents){const e=get('world-switzerland-president-for-'+p.term.replace('/','-'));assert.ok(e);assert.equal(e.results[0].name,p.name);assert.equal(e.results[0].votes,p.votes);assert.equal(e.results[0].winner,true);assert.equal(e.results[0].share,null);assert.equal(e.electionMethod,'indirect');assert.equal(e.resultCoverage,'partial');}
for(const p of primary.presidentialXlsVerification.rows){const e=get('world-switzerland-president-for-'+p.term);assert.ok(e);assert.equal(e.results[0].votes,p.votes);}
assert.equal(get('world-switzerland-president-for-2026').startDate,'2025-12-10');assert.equal(get('world-switzerland-president-for-2026').results[0].votes,203);
for(const term of [1870,1881]){const original=get('world-switzerland-president-for-'+term+'-original'),replacement=get('world-switzerland-president-for-'+term);assert.match(original.notes,/did not serve/);assert.equal(original.results[0].winner,true);assert.equal(replacement.precision,'unknown');assert.equal(replacement.startDate,'');}
for(const e of ballots){const a=audit.find(a=>a.id===e.id);assert.equal(e.resultCoverage,'complete');assert.equal(e.results.reduce((n,r)=>n+r.votes,0),a.expectedVotes);assert.equal(e.results.filter(r=>r.winner).length,e.results.some(r=>r.party!=='Unattributed ballots'&&r.votes>a.expectedVotes/2)?1:0);for(const r of e.results)assert.equal(r.winner,r.party!=='Unattributed ballots'&&r.votes>a.expectedVotes/2);}
assert.ok(!get('world-switzerland-federal-council-2025-03-12-ballot-1').results.some(r=>r.winner));assert.equal(get('world-switzerland-federal-council-2025-03-12-ballot-2').results.find(r=>r.winner).name,'Martin Pfister');
const council=get('world-switzerland-federal-council-2023-12-13');assert.equal(council.results.length,7);assert.equal(council.results.reduce((n,r)=>n+r.seats,0),7);assert.equal(council.results.find(r=>r.name==='Beat Jans').votes,134);assert.ok(council.results.every(r=>r.share===null));
const keller=get('world-switzerland-federal-council-2023-12-13-seat-5-ballot-1');assert.ok(keller.results.every(r=>r.winner===(r.votes>112&&r.party!=='Unattributed ballots')));
const old=get('world-switzerland-federal-council-2019-12-11');assert.ok(old.results.some(r=>r.name==='Ueli Maurer'&&r.votes===213));assert.ok(old.results.some(r=>r.name==='Simonetta Sommaruga'&&r.votes===192));assert.ok(!old.results.some(r=>r.name==='Albert Rösti'));
const existing=JSON.parse(fs.readFileSync(root+'pre-import-backup.json')).filter(r=>r.kind==='world_election');for(const r of existing)assert.deepEqual(get(r.id),r.data);assert.equal(existing.length,3);
assert.equal(records.filter(e=>e.status==='scheduled').length,6);assert.equal(get('world-switzerland-federal-council-2026-12-09').dateStatus,'expected');assert.equal(get('world-switzerland-federal-council-2027-12-15').dateStatus,'confirmed');assert.equal(get('world-switzerland-president-2027-12-15').dateStatus,'confirmed');assert.ok(records.filter(e=>e.status==='scheduled').every(e=>!e.results.length));
const primaryCouncil=JSON.parse(fs.readFileSync(root+'council-primary-reconciliation.json'));
const normal=s=>s.normalize('NFKD').replace(/[^a-zA-Z]/g,'').toLowerCase();
for(const p of primaryCouncil){const e=records.find(e=>e.seriesId==='ch-federal-council'&&e.status==='held'&&e.startDate.startsWith(String(p.year)));for(const r of e.results){assert.ok(p.candidates.some(c=>normal(c.name)===normal(r.name)&&c.votes.includes(r.votes)),p.year+' '+r.name+' primary count');}}
console.log('Switzerland: 395 records; 52 National Council cycles, 44 States compositions, annual presidency, separate Federal Council seat ballots, primary FSO allocations, historical gaps, existing Calendar IDs and confirmed 2027 dates passed.');
