import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
import {electionMetadata} from '../lib/seo.mjs';

function moduleUrl(file,imports={}) {
  let source=fs.readFileSync(file,'utf8');
  for(const [from,to] of Object.entries(imports)) source=source.replaceAll("'"+from+"'","'"+to+"'");
  return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const {validateWorldElection}=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const {validateParty}=await import(moduleUrl('lib/country-parties.ts'));
const read=name=>JSON.parse(fs.readFileSync('scripts/'+name+'.json','utf8'));
const elections=read('timor-leste-election-records'),parties=read('timor-leste-party-profiles'),audits=read('timor-leste-election-audit');
assert.equal(elections.length,14);
assert.equal(elections.filter(e=>e.type==='parliamentary').length,6);
assert.equal(elections.filter(e=>e.type==='presidential').length,8);
assert.equal(new Set(elections.map(e=>e.id)).size,elections.length);
assert.equal(new Set(parties.map(p=>p.id)).size,parties.length);
for(const p of parties) { validateParty(p); assert.equal(p.country_id,'tl'); assert.deepEqual(p.ideology_ids,[]); }
const expectedDates=['2001-08-30','2002-04-14','2007-04-09','2007-05-09','2007-06-30','2012-03-17','2012-04-16','2012-07-07','2017-03-20','2017-07-22','2018-05-12','2022-03-19','2022-04-19','2023-05-21'];
assert.deepEqual(elections.map(e=>e.startDate),expectedDates);
for(const e of elections) {
  validateWorldElection(e);
  assert.equal(e.countryId,'tl'); assert.equal(e.precision,'day'); assert.equal(e.publication,'published');
  assert.equal(e.resultStatus,'final'); assert.equal(e.electionMethod,'direct');
  const audit=audits.find(a=>a.id===e.id);
  assert.ok(audit);
  assert.equal(e.results.reduce((n,r)=>n+(r.votes??0),0),audit.validVotes);
  assert.ok(Math.abs(e.results.reduce((n,r)=>n+(r.share??0),0)-100)<1e-8);
  if(e.totalSeats!==null) {
    assert.equal(e.results.reduce((n,r)=>n+(r.seats??0),0),e.totalSeats);
    assert.equal(e.majorityThreshold,Math.floor(e.totalSeats/2)+1);
  } else assert.ok(e.results.every(r=>r.seats===null&&r.previousSeats===null&&r.electoralVotes===null));
  if(audit.registeredVoters!==null) assert.equal(e.turnout,audit.ballotsCast/audit.registeredVoters*100);
  else assert.equal(e.turnout,null);
  for(const r of e.results) {
    assert.ok(!r.winner||!r.advanced);
    if(r.votes!==null) assert.equal(r.share,r.votes/audit.validVotes*100);
    else assert.equal(r.share,null);
    if(r.partyId) {
      const p=parties.find(p=>p.id===r.partyId);
      assert.ok(p); assert.equal(p.short_name,r.party); assert.equal(p.color,r.color);
    }
    if(e.startDate.startsWith('2007')&&r.party==='PST') { assert.deepEqual(r.ideologyIds,['ideology-marxism-leninism']); assert.equal(r.ideologyBasis.kind,'party-era'); assert.equal(r.ideologyBasis.year,2007); assert.ok(r.ideologyBasis.sources.length); }
    else { assert.deepEqual(r.ideologyIds,[]); if(e.type==='presidential') assert.equal(r.ideologyBasis.kind,'unassessed'); }
    if(e.type==='presidential') assert.equal(r.ideologyBasis.year,+e.startDate.slice(0,4));
  }
  for(const id of e.linkedElectionIds) {
    const other=elections.find(x=>x.id===id);
    assert.ok(other); assert.equal(e.seriesId,other.seriesId); assert.ok(other.linkedElectionIds.includes(e.id));
  }
  if(e.type==='presidential') {
    if(e.linkedElectionIds.length&&e.round==='First round') { assert.equal(e.results.filter(r=>r.advanced).length,2); assert.equal(e.results.filter(r=>r.winner).length,0); }
    else { assert.equal(e.results.filter(r=>r.winner).length,1); assert.equal(e.results.filter(r=>r.advanced).length,0); }
  }
  for(const s of e.sources) assert.equal(new URL(s.url).protocol,'https:');
  const seo=electionMetadata(e,'Timor-Leste');
  assert.equal((seo.title.match(/Timor-Leste/g)||[]).length,1);
  assert.ok(seo.title.includes(e.startDate.slice(0,4))&&seo.title.includes('election'));
}
const first=elections[0];
assert.equal(first.results.find(r=>r.id==='fretilin').seats,55);
assert.equal(first.results.at(-1).votes,null);
assert.equal(first.results.at(-1).seats,1);
assert.equal(first.results.at(-2).votes,5341);
assert.equal(first.results.at(-2).seats,0);
assert.ok(elections.filter(e=>e.startDate<'2012-01-01').every(e=>e.results.every(r=>r.previousSeats===null)));
assert.deepEqual(elections.filter(e=>e.resultCoverage==='partial').map(e=>e.startDate),['2001-08-30','2012-04-16','2023-05-21']);
for(const date of ['2018-05-12','2023-05-21']) {
  const e=elections.find(e=>e.startDate===date);
  for(const r of e.results.filter(r=>['AMP','FDD','CNRT','PLP','KHUNTO','PUDD','UDT'].some(p=>r.party.startsWith(p)))) assert.equal(r.previousSeats,null);
}
console.log(JSON.stringify({validated:true,elections:elections.length,results:elections.reduce((n,e)=>n+e.results.length,0),parties:parties.length,coverage:{complete:11,partial:3},checks:['current WorldElection validator','party validator','dates and unique IDs','round links and elected/advanced flags','exact vote reconciliation','unrounded shares','seat and majority totals','previous-seat comparability','HTTPS sources','publication and SEO']}));
