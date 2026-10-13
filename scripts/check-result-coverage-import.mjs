import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){
 let source=fs.readFileSync(file,'utf8');
 for(const [from,to] of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");
 return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const root='scripts/result-coverage-import/';
const records=JSON.parse(fs.readFileSync(root+'records.json'));
const before=new Map(JSON.parse(fs.readFileSync(root+'pre-import-backup.json')).map(r=>[r.id,r.data]));
assert.equal(records.length,17);assert.equal(new Set(records.map(e=>e.id)).size,17);
const allowed=new Set(['results','totalSeats','resultStatus','resultCoverage','checked','version','voteBasis','notes','turnout','sources','linkedElectionIds','electionMethod']);
for(const e of records){
 try{model.validateWorldElection(e);}catch(error){console.error(e.id,error.message);process.exit(1);}
 const old=before.get(e.id);assert.ok(old);assert.equal(old.results.length,0);assert.equal(e.version,old.version+1);
 for(const key of new Set([...Object.keys(old),...Object.keys(e)]))if(!allowed.has(key))assert.deepEqual(e[key],old[key],e.id+' '+key);
 assert.deepEqual(e.sources.slice(0,old.sources.length),old.sources);assert.ok(e.results.length);
 assert.equal(e.publication,'published');assert.equal(e.status,'held');
}
const get=id=>records.find(e=>e.id===id);
const expectedVotes=[15977142,15612671,17680729,18402497,17437379];
for(const [i,year] of [1999,2004,2009,2014,2019].entries()){
 const e=get('world-south-africa-'+year);assert.equal(e.results.reduce((n,r)=>n+r.votes,0),expectedVotes[i]);
 assert.equal(e.results.reduce((n,r)=>n+r.seats,0),400);assert.equal(e.resultCoverage,'complete');
 assert.ok(e.results.some(r=>r.seats===0));assert.ok(Math.abs(e.results.reduce((n,r)=>n+r.share,0)-100)<.15);
}
assert.equal(get('world-south-africa-2004').results.find(r=>r.name==='African Christian Democratic Party').seats,7);
const india=get('world-india-2024');assert.equal(india.results.reduce((n,r)=>n+r.seats,0),543);assert.ok(india.results.every(r=>r.votes===null&&r.share===null));
assert.equal(india.results.find(r=>r.name==='Shiv Sena (2022–present)').seats,7);
assert.equal(india.results.find(r=>r.name==='Shiv Sena (Uddhav Balasaheb Thackeray)').seats,9);
assert.equal(india.results.find(r=>r.name==='Kerala Congress').seats,1);assert.ok(!india.results.some(r=>r.name==='Kerala Congress (Mani)'));
const brazil=get('world-brazil-president-2022-first');assert.equal(brazil.results.length,11);assert.equal(brazil.results.reduce((n,r)=>n+r.votes,0),118229719);
assert.equal(brazil.results.filter(r=>r.advanced).length,2);assert.ok(brazil.results.every(r=>!r.winner));
assert.equal(get('world-sweden-2026').results.reduce((n,r)=>n+r.seats,0),349);
const denmark=get('world-denmark-2026');assert.equal(denmark.totalSeats,179);assert.equal(denmark.results.reduce((n,r)=>n+r.seats,0),175);assert.equal(denmark.resultCoverage,'partial');assert.equal(denmark.turnout,null);
const morocco=get('world-morocco-2026');assert.equal(morocco.resultStatus,'provisional');assert.equal(morocco.results.reduce((n,r)=>n+r.seats,0),395);assert.ok(morocco.results.every(r=>r.votes===null&&r.share===null));
for(const [year,total] of [[2018,56],[2020,18],[2022,19],[2024,19],[2026,18]]){
 const e=get('world-nepal-national-assembly-'+year);assert.equal(e.results.reduce((n,r)=>n+r.seats,0),total);assert.equal(e.totalSeats,59);assert.equal(e.resultCoverage,'partial');assert.equal(e.electionMethod,'indirect');assert.ok(e.results.every(r=>r.votes===null&&r.share===null));
}
assert.equal(get('world-nepal-national-assembly-2026').results.find(r=>r.name==='Janata Samajbadi Party, Nepal').seats,1);
console.log('17 archive-gap patches passed model, source, chronology, allocation and preservation checks.');

for(const [id,total,count] of [['world-tunisia-2014-11-23-presidential-election',3267569,27],['world-tunisia-2019-09-15-presidential-election',3372973,26]]){const e=get(id);assert.equal(e.results.length,count);assert.equal(e.results.reduce((n,r)=>n+r.votes,0),total);assert.equal(e.results.filter(r=>r.advanced).length,2);assert.ok(e.results.every(r=>!r.winner));assert.equal(e.resultCoverage,'complete');}
