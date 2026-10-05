import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(fs.readFileSync('scripts/china-election-records.json','utf8'));
assert.equal(records.length,26);assert.equal(new Set(records.map(e=>e.id)).size,26);
const npc=records.filter(e=>e.type==='parliamentary');const presidents=records.filter(e=>e.type==='presidential');
assert.deepEqual(npc.map(e=>+e.startDate.slice(0,4)),[1954,1959,1964,1975,1978,1983,1988,1993,1998,2003,2008,2013,2018,2023]);
assert.equal(presidents.length,12);
for(const e of records){model.validateWorldElection(e);assert.equal(e.countryId,'cn');assert.equal(e.publication,'published');assert.equal(e.electionMethod,'indirect');assert.equal(e.turnout,null);assert.ok(e.sources.length);for(const id of e.linkedElectionIds)assert.ok(records.some(x=>x.id===id&&x.linkedElectionIds.includes(e.id)));}
for(const e of npc){assert.equal(e.precision,'year');assert.equal(e.resultCoverage,'partial');assert.equal(e.results.reduce((n,r)=>n+(r.seats??0),0),e.totalSeats);assert.ok(e.results.every(r=>r.votes===null&&r.share===null&&!r.winner&&r.ideologyIds.length===0));}
assert.equal(npc.find(e=>e.id==='world-cn-npc-1988').totalSeats,2970);
assert.match(npc.find(e=>e.id==='world-cn-npc-1975').summary,/consultation/);
assert.equal(records.some(e=>/world-cn-president-(1949|1975|1978)/.test(e.id)),false);
assert.deepEqual(presidents.filter(e=>e.resultCoverage==='complete').map(e=>[e.startDate,e.results[0].votes,e.results[0].share]),[['2018-03-17',2970,100],['2023-03-10',2952,100]]);
assert.equal(records.find(e=>e.id==='world-cn-president-1965').linkedElectionIds[0],'world-cn-npc-1964');
console.log('Validated 26 sourced PRC national institution records, chronological gaps, method and ballot denominators.');

const latest=npc.find(e=>e.id==='world-cn-npc-2023');assert.equal(latest.results.length,10);assert.equal(latest.results.find(r=>r.id==='cn-tdsgl').seats,14);assert.equal(latest.results.find(r=>r.id==='cn-jiusan').seats,56);assert.equal(latest.results.find(r=>r.id==='cn-cpc').seats,null);assert.equal(latest.results.find(r=>r.id==='npc-unclassified').seats,2696);assert.equal(npc.find(e=>e.id==='world-cn-npc-1954').results[0].seats,668);
