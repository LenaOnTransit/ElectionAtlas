import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file, imports={}) {
  let src=fs.readFileSync(file,'utf8');
  for(const [from,to] of Object.entries(imports)) src=src.replaceAll("'"+from+"'","'"+to+"'");
  return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const partyModel=await import(moduleUrl('lib/country-parties.ts'));
const root='scripts/polish-election-import/';
const records=JSON.parse(fs.readFileSync(root+'records.json'));
const parties=JSON.parse(fs.readFileSync(root+'parties.json'));
const audit=JSON.parse(fs.readFileSync(root+'reconciliation.json'));
const primary=JSON.parse(fs.readFileSync(root+'primary-reconciliation.json'));
const ids=new Set(records.map(e=>e.id)), profiles=new Map(parties.map(p=>[p.id,p]));
assert.equal(ids.size,records.length);
assert.equal(records.length,67);
assert.equal(records.filter(e=>e.status==='held').length,65);
assert.equal(records.filter(e=>e.status==='held'&&e.body==='Sejm').length,27);
assert.equal(records.filter(e=>e.status==='held'&&e.body==='Senate').length,16);
assert.equal(records.filter(e=>e.status==='held'&&e.type==='presidential').length,22);
for(const p of parties) partyModel.validateParty(p);
for(const e of records) {
  model.validateWorldElection(e);
  assert.equal(e.countryId,'pl');
  assert.equal(e.publication,'published');
  assert.equal(e.live.enabled,false);
  assert.ok(e.sources.length>0);
  for(const id of e.linkedElectionIds||[]) assert.ok(ids.has(id));
  for(const r of e.results) if(r.partyId) {
    assert.ok(profiles.has(r.partyId));
    assert.equal(r.color,profiles.get(r.partyId).color);
    assert.deepEqual(r.ideologyIds,[]);
  }
  const a=audit.find(a=>a.id===e.id);
  if(a) {
    assert.equal(e.results.reduce((n,r)=>n+(r.votes||0),0),a.recordedVotes);
    assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),a.recordedSeats);
    if(e.resultCoverage==='complete') {
      if(a.expectedVotes!==null) assert.equal(a.recordedVotes,a.expectedVotes);
      if(a.expectedSeats!==null) assert.equal(a.recordedSeats,a.expectedSeats);
    }
  }
}
const get=id=>records.find(e=>e.id===id);
assert.equal(get('world-poland-sejm-1919-01-26').totalSeats,null);
assert.equal(get('world-poland-sejm-1952-10-26').totalSeats,425);
assert.equal(get('world-poland-sejm-1957-01-20').totalSeats,460);
assert.equal(get('world-poland-sejm-1957-01-20').results.reduce((n,r)=>n+(r.seats||0),0),459);
assert.equal(get('world-poland-senate-1935-09-15').electionMethod,'indirect');
assert.match(get('world-poland-senate-1935-09-15').notes,/32 were appointed/);
assert.match(get('world-poland-senate-2007-10-21').voteBasis,/multiple votes per elector/);
assert.ok(get('world-poland-sejm-1989-06-04').results.every(r=>r.votes===null&&r.share===null));
assert.equal(get('world-poland-senate-1989-06-04').results[0].seats,99);
for(const year of [1990,1995,2005,2010,2015,2020,2025]) {
  const rounds=records.filter(e=>e.status==='held'&&e.type==='presidential'&&e.startDate.startsWith(String(year))).sort((a,b)=>a.startDate.localeCompare(b.startDate));
  assert.equal(rounds.length,2);
  assert.equal(rounds[0].results.filter(r=>r.advanced).length,2);
  assert.equal(rounds[0].results.filter(r=>r.winner).length,0);
  assert.equal(rounds[1].results.filter(r=>r.winner).length,1);
  assert.ok(rounds[0].linkedElectionIds.includes(rounds[1].id));
}
assert.equal(get('world-poland-president-2020-05-10').status,'cancelled');
assert.deepEqual(get('world-poland-president-2020-05-10').results,[]);
const future=get('world-poland-senate-district-20-2026-11-22');
assert.equal(future.status,'scheduled');assert.equal(future.dateStatus,'confirmed');assert.equal(future.totalSeats,1);assert.deepEqual(future.results,[]);
for(const p of primary) {
  const e=get(p.id);
  assert.equal(e.results.reduce((n,r)=>n+r.votes,0),p.validVotes);
  for(const row of e.results) assert.equal(row.votes,p.candidates[row.name.split(' ').at(-1).toUpperCase()]);
}
assert.equal(get('world-poland-president-2025-06-01').results.find(r=>r.winner).name,'Karol Nawrocki');
assert.equal(get('world-poland-sejm-2023-10-15').results.reduce((n,r)=>n+r.votes,0),21596674);
assert.equal(get('world-poland-sejm-2023-10-15').results.find(r=>r.name==='United Right').seats,194);
assert.equal(get('world-poland-president-1926-05-31').results.find(r=>r.winner).name,'Józef Piłsudski');
assert.match(get('world-poland-president-1926-05-31').notes,/refused to take office/);
console.log('Poland: 67 records, 65 historical results, source reconciliation, chamber capacities, coalition cells, multiple rounds, party references and confirmed Calendar date passed.');
