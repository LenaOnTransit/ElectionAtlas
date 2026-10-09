import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const read=f=>JSON.parse(fs.readFileSync('scripts/uk-historical-election-import/'+f));
const records=read('records.json'),backup=read('pre-import-backup.json');
const byId=new Map(records.map(e=>[e.id,e]));
const commons=records.filter(e=>e.seriesId==='UK-HOC'),scottish=records.filter(e=>e.seriesId==='UK-LORDS-SCOTTISH'),hereditary=records.filter(e=>e.seriesId==='UK-LORDS-HEREDITARY');
assert.equal(records.length,101);assert.equal(byId.size,101);assert.equal(commons.length,58);assert.equal(scottish.length,41);assert.equal(hereditary.length,2);
for(const row of backup.filter(r=>r.kind==='world_election'))assert.deepEqual(byId.get(row.id),row.data);
for(const e of records){model.validateWorldElection(e);assert.equal(e.countryId,'gb');assert.equal(e.publication,'published');assert.equal(e.status,'held');assert.ok(e.sources.length);assert.ok(!e.body.includes('Senate'));assert.ok(e.startDate<'2026');for(const id of e.linkedElectionIds||[]){assert.ok(byId.has(id));assert.ok(byId.get(id).linkedElectionIds.includes(e.id));}if(e.resultCoverage==='complete')assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),e.totalSeats);}
const at=date=>commons.find(e=>e.startDate===date),votes=e=>e.results.reduce((n,r)=>n+(r.votes||0),0);
assert.equal(at('1802-07-05').endDate,'1802-08-28');assert.equal(at('1832-12-10').endDate,'1833-01-08');assert.equal(at('1945-07-05').endDate,'1945-07-19');
for(const year of ['1910','1974'])assert.equal(commons.filter(e=>e.startDate.startsWith(year)).length,2);
assert.equal(at('1918-12-14').totalSeats,707);assert.equal(votes(at('1918-12-14')),10786818);assert.equal(at('1918-12-14').results.find(r=>r.name.startsWith('Conservative')).seats,382);assert.equal(at('1918-12-14').weightedVotes,true);
assert.equal(at('1931-10-27').results.find(r=>r.name.startsWith('Conservative')).seats,522);assert.equal(at('1945-07-05').results.find(r=>r.name==='Labour').seats,393);
assert.equal(votes(at('1974-02-28')),31340162);assert.equal(at('1974-02-28').results.find(r=>r.name==='Labour').seats,301);assert.equal(votes(at('2005-05-05')),27148510);assert.equal(at('2005-05-05').totalSeats,646);
for(const e of scottish){assert.equal(e.totalSeats,16);assert.equal(e.electionMethod,'indirect');assert.equal(e.turnout,null);assert.equal(e.linkedElectionIds.length,1);assert.ok(e.results.every(r=>r.share===null));}
assert.ok(!scottish.some(e=>e.startDate==='1922-01-13'));
const final=scottish.find(e=>e.startDate==='1959-10-06');assert.equal(final.results.length,29);assert.equal(final.results.filter(r=>r.winner).length,16);assert.equal(final.resultCoverage,'partial');
assert.deepEqual(hereditary.map(e=>[e.startDate,e.endDate,e.totalSeats]),[['1999-10-27','1999-10-28',15],['1999-11-03','1999-11-04',75]]);
for(const e of hereditary){assert.equal(e.results.length,e.totalSeats);assert.ok(e.results.every(r=>r.seats===1&&r.winner&&r.votes===null&&r.share===null));assert.equal(e.resultCoverage,'partial');assert.ok(e.sources.some(s=>s.url.endsWith('2013comp.pdf')));}
const quotas=Object.fromEntries(['Labour','Conservative','Cross-bench','Liberal Democrat'].map(p=>[p,hereditary[1].results.filter(r=>r.party===p).length]));assert.deepEqual(quotas,{Labour:2,Conservative:42,'Cross-bench':28,'Liberal Democrat':3});
assert.equal(read('reconciliation.json').length,96);
console.log('UK historical archive: 58 Commons, 41 Scottish peer elections, two 1999 ballots; source totals, intervals, peer quotas and preservation passed.');
