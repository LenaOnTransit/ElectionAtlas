import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import ts from 'typescript';
import test from 'node:test';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(gunzipSync(fs.readFileSync('scripts/us-midterm-election-records.json.gz')));
const years=Array.from({length:59},(_,i)=>1790+4*i);
const election=(office,year)=>records.find(e=>e.id===`world-us-${office}-${year}`);
test('all 59 completed midterm cycles have valid House, Senate and governor records',()=>{
 assert.equal(records.length,177);assert.equal(new Set(records.map(e=>e.id)).size,177);
 for(const office of ['house','senate','governor'])assert.deepEqual(records.filter(e=>e.seriesId===`us-${office}-midterms`).map(e=>Number(e.startDate.slice(0,4))),years);
 for(const e of records){try{model.validateWorldElection(e)}catch(error){throw Error(e.id+': '+error.message)}assert.equal(e.publication,'published');assert.equal(e.status,'held');assert.ok(e.sources.length);assert.equal(e.precision,'year');assert.ok(JSON.stringify(e).length<900000);}
});
test('House seats reconcile without invented popular-vote shares or district records',()=>{
 for(const e of records.filter(e=>e.seriesId==='us-house-midterms')){assert.equal(e.results.reduce((n,r)=>n+r.seats,0),e.totalSeats);assert.equal(e.contests,undefined);assert.ok(e.results.every(r=>r.share===null));}
 assert.equal(election('house',2022).results.find(r=>r.party==='Republican').seats,222);
 assert.equal(election('house',2018).results.find(r=>r.party==='Democratic').seats,235);
 assert.ok(election('house',2018).results.some(r=>r.name==='Unallocated in initial source divisions'&&r.seats===1));
});
test('state percentages and calls remain separate; Senate diagrams exclude continuing and special seats',()=>{
 const ids=new Set();
 for(const e of records.filter(e=>e.contests)){
  assert.ok(e.contests.length>0);
  for(const c of e.contests){assert.ok(!ids.has(c.id));ids.add(c.id);assert.ok(c.results.reduce((n,r)=>n+(r.share||0),0)<=100.2);assert.ok(c.results.every(r=>!(r.winner&&r.advanced)));}
  if(e.seriesId==='us-senate-midterms'){
   const regular=e.contests.filter(c=>!c.special&&!c.diagramExcluded);assert.equal(e.totalSeats,regular.length);assert.equal(e.results.length,regular.reduce((n,c)=>n+c.results.filter(r=>r.winner).length,0));assert.ok(e.results.every(r=>r.seats===1&&r.votes===null&&r.share===null));
  }
 }
 assert.equal(election('senate',2022).totalSeats,34);assert.equal(election('governor',2022).contests.length,36);
 for(const c of election('senate',1790).contests){assert.equal(c.method,'indirect');assert.ok(c.results.every(r=>r.votes===null&&r.share===null));}
});
test('general-election results, fusion ballots and legislative selection retain their real winners',()=>{
 const race=(office,y,state)=>election(office,y).contests.find(c=>c.stateCode===state&&!c.special);
 assert.equal(race('senate',2022,'AL').results.find(r=>r.winner).votes,942154);
 assert.equal(race('senate',2022,'AZ').results.find(r=>r.winner).votes,1322027);
 assert.equal(race('governor',1850,'MA').results.find(r=>r.winner).name,'George S. Boutwell');
 assert.equal(race('governor',2022,'NY').results.filter(r=>r.winner).length,1);
 assert.equal(race('governor',2022,'NY').results.find(r=>r.winner).votes,3140415);
 assert.ok(race('governor',2022,'MA').results.every(r=>!['Blank','Void','Undervote','Overvote'].includes(r.name)));
});
test('election-era fallback differs across party realignments and sourced candidates override it',()=>{
 const republican=y=>election('house',y).results.find(r=>r.party==='Republican');
 assert.ok(republican(1862).ideologyIds.includes('ideology-social-progressivism'));assert.ok(!republican(1862).ideologyIds.includes('ideology-national-conservatism'));
 assert.ok(republican(2022).ideologyIds.includes('ideology-national-conservatism'));
 const senators=election('senate',2018).contests.flatMap(c=>c.results);assert.equal(senators.find(r=>r.name==='Bernie Sanders').ideologyBasis.kind,'candidate');
 assert.ok(senators.find(r=>r.name==='Bernie Sanders').ideologyIds.includes('ideology-democratic-socialism'));
 const governors=election('governor',1998).contests.flatMap(c=>c.results);assert.equal(governors.find(r=>r.name==='Jesse Ventura').ideologyBasis.kind,'candidate');
 for(const e of records)for(const r of [...e.results,...(e.contests||[]).flatMap(c=>c.results)]){assert.equal(r.ideologyBasis.year,Number(e.startDate.slice(0,4)));assert.ok(r.ideologyBasis.kind==='unassessed'||r.ideologyBasis.sources.length>0);}
});
test('invalid cross-race percentages, duplicate race IDs and unsafe ideology source URLs are rejected',()=>{
 const e=structuredClone(election('governor',2022));e.contests[0].results[0].share=100;e.contests[0].results[1].share=100;assert.throws(()=>model.validateWorldElection(e));
 const duplicate=structuredClone(election('governor',2022));duplicate.contests.push(duplicate.contests[0]);assert.throws(()=>model.validateWorldElection(duplicate));
 const unsafe=structuredClone(election('house',2022));unsafe.results[0].ideologyBasis.sources[0].url='javascript:alert(1)';assert.throws(()=>model.validateWorldElection(unsafe));
});
test('runoff rounds preserve advances without adding a second regular Senate seat',()=>{
 const ga=election('senate',2022).contests.filter(c=>c.stateCode==='GA');
 const first=ga.find(c=>c.diagramExcluded),final=ga.find(c=>c.round==='Runoff');
 assert.ok(first&&final);assert.equal(first.special,false);assert.equal(first.results.filter(r=>r.advanced).length,2);assert.equal(first.results.filter(r=>r.winner).length,0);assert.equal(final.results.filter(r=>r.winner).length,1);
});
