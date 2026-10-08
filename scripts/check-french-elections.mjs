import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(fs.readFileSync('scripts/french-election-import/records.json'));for(const e of records){try{model.validateWorldElection(e)}catch(err){throw Error(e.id+': '+err.message)};if(e.type==='presidential')assert.equal(e.totalSeats,null);if(e.resultCoverage==='complete'){assert.ok(Math.abs(e.results.reduce((n,r)=>n+(r.share||0),0)-100)<.2);if(e.type==='parliamentary')assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),e.totalSeats);}}
assert.equal(new Set(records.map(e=>e.id)).size,records.length);
assert.ok(records.some(e=>e.startDate.startsWith('1789')));assert.ok(records.some(e=>e.startDate==='1848-12-10'));
for(const year of [1965,1969,1974,1981,1988,1995,2002,2007,2012,2017,2022]){const es=records.filter(e=>e.type==='presidential'&&e.electionMethod==='direct'&&e.startDate.startsWith(''+year));assert.equal(es.length,2);assert.equal(es[0].results.filter(r=>r.advanced).length,2);assert.equal(es[1].results.filter(r=>r.winner).length,1);}
assert.equal(records.filter(e=>e.type==='presidential'&&e.startDate.startsWith('1920')).length,2);
assert.equal(records.find(e=>e.id==='world-france-president-2022-runoff').results[0].votes,18768639);
assert.equal(records.find(e=>e.startDate==='2024-06-30').totalSeats,577);
console.log(`French archive: ${records.length} valid records; rounds, indirect ballots, identities and source-scoped totals passed.`);

assert.equal(records.length,110);assert.equal(records.filter(e=>e.type==='parliamentary').length,68);assert.equal(records.filter(e=>e.type==='presidential').length,42);assert.ok(records.every(e=>e.startDate<'2025' && e.countryId==='fr' && e.sources.length));
