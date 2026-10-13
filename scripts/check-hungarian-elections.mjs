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
const root='scripts/hungarian-election-import/';
const records=JSON.parse(fs.readFileSync(root+'records.json')),parties=JSON.parse(fs.readFileSync(root+'parties.json'));
const audit=JSON.parse(fs.readFileSync(root+'reconciliation.json')),primary=JSON.parse(fs.readFileSync(root+'primary-reconciliation.json'));
const ids=new Set(records.map(e=>e.id)),profiles=new Map(parties.map(p=>[p.id,p]));
assert.equal(records.length,68);assert.equal(ids.size,records.length);
for(const p of parties)partyModel.validateParty(p);
for(const e of records){
 model.validateWorldElection(e);assert.equal(e.countryId,'hu');assert.equal(e.publication,'published');assert.equal(e.live.enabled,false);
 assert.ok(e.sources.length);assert.ok(!e.legitimacy);
 for(const id of e.linkedElectionIds||[])assert.ok(ids.has(id));
 for(const r of e.results)if(r.partyId){assert.ok(profiles.has(r.partyId));assert.equal(r.color,profiles.get(r.partyId).color);assert.deepEqual(r.ideologyIds,[]);}
 const a=audit.find(a=>a.id===e.id);assert.ok(a);
 assert.equal(e.results.reduce((n,r)=>n+(r.votes||0),0),a.recordedVotes);
 assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),a.recordedSeats);
 if(e.resultCoverage==='complete'){
  if(a.expectedVotes!==null)assert.equal(a.recordedVotes,a.expectedVotes);
  if(a.expectedSeats!==null)assert.equal(a.recordedSeats,a.expectedSeats);
 }
 if(e.precision!=='day'){assert.equal(e.dateStatus,'expected');assert.ok(e.results.every(r=>r.share===null));}
 if(e.status==='held'&&!e.results.length){assert.equal(e.resultStatus,'not-entered');assert.equal(e.resultCoverage,'partial');assert.equal(e.totalSeats,null);}
}
const get=id=>records.find(e=>e.id===id);
assert.equal(records.filter(e=>e.type==='parliamentary').length,50);
assert.equal(records.filter(e=>e.type==='presidential').length,18);
for(const year of [1990,1994,1998,2002,2006,2010,2014,2018,2022,2026]){
 const e=records.find(e=>e.type==='parliamentary'&&e.startDate.startsWith(String(year)));
 const capacity=year<=2010?386:199;
 assert.equal(e.totalSeats,capacity);assert.equal(e.resultCoverage,'complete');assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),capacity);
 assert.match(e.voteBasis,/proportional\/list ballots/);
 assert.ok(e.sources.some(s=>s.url.includes('valasztas.hu')));
 if(year<=2010){assert.ok(e.endDate>e.startDate);assert.match(e.round,/two rounds/);}
}
assert.equal(get('world-hungary-parliament-1920-01-01').totalSeats,219);
assert.ok(get('world-hungary-parliament-1920-01-01').results.every(r=>r.votes===null&&r.share===null));
assert.match(get('world-hungary-parliament-1920-01-01').notes,/October 1921/);
assert.equal(get('world-hungary-parliament-1944-01-01').totalSeats,498);
assert.equal(get('world-hungary-parliament-1944-01-01').electionMethod,'indirect');
assert.equal(get('world-hungary-parliament-1985-06-08').totalSeats,387);
assert.equal(get('world-hungary-parliament-1985-06-08').results.find(r=>r.name==='Vacant').seats,1);
assert.ok(!get('world-hungary-parliament-1985-06-08').results.find(r=>r.name==='Vacant').partyId);
assert.ok(get('world-hungary-parliament-1985-06-08').results.every(r=>r.votes===null&&r.share===null));
const front=get('world-hungary-parliament-1953-05-17');
assert.equal(front.results[0].votes,6256653);assert.equal(front.results[0].seats,298);
assert.equal(front.results.reduce((n,r)=>n+r.votes,0),6317910);
const early=get('world-hungary-parliament-1825-08-01');assert.ok(early.results.every(r=>r.votes===null&&r.share===null));assert.match(early.notes,/estates-based/);
for(const year of [2000,2005,2017]){
 const ballots=records.filter(e=>e.type==='presidential'&&e.startDate.startsWith(String(year))).sort((a,b)=>a.id.localeCompare(b.id));
 assert.equal(ballots.length,year===2017?2:3);
 for(const e of ballots.slice(0,-1))assert.ok(e.results.every(r=>!r.winner));
 assert.equal(ballots.at(-1).results.filter(r=>r.winner).length,1);
 for(const e of ballots){assert.equal(e.electionMethod,'indirect');assert.equal(e.turnout,null);assert.ok(e.linkedElectionIds.includes(ballots.find(b=>b.id!==e.id).id));}
}
assert.equal(get('world-hungary-president-2000-06-06-ballot-2').results[0].votes,238);
assert.equal(get('world-hungary-president-2005-06-06-ballot-1').results.find(r=>r.name==='Katalin Szili').winner,false);
assert.equal(get('world-hungary-president-2005-06-07-ballot-3').results.find(r=>r.winner).name,'László Sólyom');
assert.equal(get('world-hungary-president-2017-03-13-ballot-1').results.find(r=>r.name==='János Áder').winner,false);
const sulyok=get('world-hungary-president-2024-02-26');assert.equal(sulyok.results[0].party,'Independent');assert.ok(!sulyok.results[0].partyId);assert.equal(sulyok.results[0].votes,134);
const baka=get('world-hungary-president-2026-08-11');assert.equal(baka.results[0].name,'András Baka');assert.equal(baka.results[0].votes,140);assert.equal(baka.results[1].votes,6);assert.equal(baka.results[0].winner,true);assert.equal(baka.electionMethod,'indirect');
const p=JSON.parse(fs.readFileSync(root+'primary-reconciliation.json'));const latest=get('world-hungary-parliament-2026-04-12');
assert.deepEqual(latest.results.filter(r=>r.votes!==null).map(r=>r.votes).sort((a,b)=>a-b),p.allListVoteCounts);
assert.equal(latest.results.reduce((n,r)=>n+(r.votes||0),0),p.validListVotes);
for(const [name,v] of Object.entries(p.majorParties)){const r=latest.results.find(r=>r.name===name);assert.equal(r.votes,v.listVotes);assert.equal(r.seats,v.totalSeats);}
assert.equal(latest.turnout,Number((p.participatingListVoters/p.registeredListVoters*100).toFixed(6)));
assert.equal(records.filter(e=>!e.results.length).length,2);assert.ok(!records.some(e=>e.status==='scheduled'));
console.log('Hungary: 68 records; historical scope, modern list denominators, complete seat allocations, vacancies, Communist front cells, separate assembly ballots and independently verified 2026 totals passed.');
