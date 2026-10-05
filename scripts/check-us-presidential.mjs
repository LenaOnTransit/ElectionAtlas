import fs from 'node:fs';
import ts from 'typescript';
import test from 'node:test';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(fs.readFileSync('scripts/us-presidential-election-records.json'));
const maps=JSON.parse(fs.readFileSync('public/us-presidential-electoral.json'));
const years=[1789,...Array.from({length:59},(_,i)=>1792+i*4)];
test('all 60 elections have valid, unique published archive records and electoral maps',()=>{
 assert.equal(records.length,60);assert.equal(new Set(records.map(e=>e.id)).size,60);
 assert.deepEqual(records.map(e=>Number(e.id.slice(-4))),years);assert.equal(Object.keys(maps).length,60);
 for(const e of records){model.validateWorldElection(e);assert.equal(e.countryId,'us');assert.equal(e.publication,'published');assert.equal(e.status,'held');assert.equal(e.seriesId,'us-presidential');assert.equal(e.results.filter(r=>r.winner).length,1);assert.ok(maps[e.id]);}
});
test('every state allocation reconciles to every national candidate and the recorded electors',()=>{
 const codes=new Set([...JSON.parse(fs.readFileSync('lib/us-states-map.json')).map(s=>s.code),'DC']);
 for(const e of records){const m=maps[e.id],totals={};assert.equal(new Set(m.states.map(s=>s.code)).size,m.states.length);assert.equal(m.states.reduce((n,s)=>n+s.electors,0),m.electors);assert.equal(m.majority,Math.floor(m.electors/2)+1);
  for(const s of m.states){assert.ok(codes.has(s.code));assert.equal(Object.values(s.votes).reduce((a,b)=>a+b,0)+s.unallocated,s.electors*m.ballotsPerElector);for(const [id,n]of Object.entries(s.votes)){assert.ok(Number.isSafeInteger(n)&&n>0);assert.ok(m.candidates.some(c=>c.id===id));totals[id]=(totals[id]||0)+n;}}
  for(const r of e.results)assert.equal(r.electoralVotes,totals[r.id]||0,`${e.id}: ${r.name}`);
 }
});
test('early voting, contingent elections, rejected votes and faithless electors retain their actual outcomes',()=>{
 const election=y=>records.find(e=>e.id===`world-us-president-${y}`),map=y=>maps[`world-us-president-${y}`];
 for(const y of [1789,1792,1796,1800]){assert.equal(map(y).ballotsPerElector,2);assert.ok(election(y).results.every(r=>r.votes===null&&r.share===null));}
 assert.equal(election(1800).results.find(r=>r.winner).name,'Thomas Jefferson');assert.equal(map(1800).states.find(s=>s.code==='VA').votes['aaron-burr'],21);
 assert.equal(election(1824).results.find(r=>r.winner).name,'John Quincy Adams');assert.equal(election(1824).results.find(r=>r.id==='andrew-jackson').electoralVotes,99);
 assert.equal(election(1872).results.find(r=>r.id==='horace-greeley').electoralVotes,0);assert.equal(map(1872).states.find(s=>s.code==='GA').unallocated,3);
 assert.equal(map(2000).states.find(s=>s.code==='DC').unallocated,1);
 assert.equal(election(1964).results.find(r=>r.id==='barry-goldwater').electoralVotes,52);assert.equal(election(1984).results.find(r=>r.winner).name,'Ronald Reagan');
 assert.equal(election(2004).results.find(r=>r.id==='john-kerry').electoralVotes,251);assert.equal(election(2004).results.find(r=>r.id==='john-edwards').electoralVotes,1);
 assert.equal(election(2016).results.find(r=>r.id==='donald-trump').electoralVotes,304);assert.equal(election(2016).results.find(r=>r.id==='hillary-clinton').electoralVotes,227);
 assert.deepEqual(map(2024).states.find(s=>s.code==='ME').votes,{'kamala-harris':3,'donald-trump':1});assert.deepEqual(map(2024).states.find(s=>s.code==='NE').votes,{'kamala-harris':1,'donald-trump':4});
});
test('popular votes include residual votes and reconcile exactly to FEC totals for recent elections',()=>{
 for(const e of records.filter(e=>Number(e.id.slice(-4))>=1824)){const total=e.results.reduce((n,r)=>n+(r.votes||0),0);assert.ok(total>0);assert.ok(Math.abs(e.results.reduce((n,r)=>n+(r.share||0),0)-100)<1e-8);for(const r of e.results)if(r.votes!==null)assert.ok(Math.abs(r.share-100*r.votes/total)<1e-9);}
 for(const [year,total]of [[2016,136669276],[2020,158383403],[2024,155238302]])assert.equal(records.find(e=>e.id===`world-us-president-${year}`).results.reduce((n,r)=>n+(r.votes||0),0),total);
 assert.equal(records.find(e=>e.id==='world-us-president-2024').results.find(r=>r.id==='donald-trump').votes,77302580);
});
