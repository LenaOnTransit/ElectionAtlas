import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(fs.readFileSync('scripts/belgian-election-import/records.json'));const byId=new Map(records.map(e=>[e.id,e]));
for(const e of records){try{model.validateWorldElection(e)}catch(err){throw Error(e.id+': '+err.message)};assert.equal(e.countryId,'be');assert.equal(e.publication,'published');assert.ok(e.sources.length);assert.ok(e.startDate<'2025');for(const id of e.linkedElectionIds){const other=byId.get(id);assert.ok(other,id);assert.equal(other.startDate,e.startDate);assert.ok(other.linkedElectionIds.includes(e.id));}if(e.resultCoverage==='complete'){assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),e.totalSeats);assert.ok(Math.abs(e.results.reduce((n,r)=>n+(r.share||0),0)-100)<.2);}}
assert.equal(byId.size,records.length);assert.equal(records.length,174);
const get=(scope,date)=>byId.get(`world-belgium-${scope}-${date}`);
assert.equal(get('chamber','2024-06-09').totalSeats,150);assert.equal(get('chamber','2024-06-09').results[0].votes,1167061);
for(const [scope,seats] of [['flemish',124],['walloon',75],['brussels',89],['german',25],['european',22]]){const e=get(scope,'2024-06-09');assert.equal(e.totalSeats,seats);assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),seats);assert.equal(e.resultCoverage,'complete');assert.equal(e.linkedElectionIds.length,5);}
assert.ok(!records.some(e=>e.seriesId==='be-senate' && e.startDate>='2014'));
assert.equal(get('senate','1831-08-29').totalSeats,51);assert.equal(get('chamber','1831-08-29').results.length,0);
assert.ok(get('chamber','1884-06-10'));assert.ok(get('senate','1884-07-08'));
assert.equal(get('german','1974-03-10').results.reduce((n,r)=>n+(r.seats||0),0),25);assert.ok(!get('german','1974-03-10').results.some(r=>r.name==='Other parties'));
assert.equal(records.filter(e=>e.seriesId==='be-german').length,13);
assert.equal(get('chamber','1902-05-25').totalSeats,85);assert.equal(get('chamber','1902-05-25').round,'Partial renewal');
console.log(`Belgian archive: ${records.length} valid records; reciprocal links, institutional totals, language denominators, partial renewals and Senate scope passed.`);

assert.equal(get('chamber','1977-04-17').totalSeats,212);assert.equal(get('senate','1995-05-21').totalSeats,40);assert.ok(!get('senate','1870-06-14'));
