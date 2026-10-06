import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const records=JSON.parse(fs.readFileSync('scripts/german-election-import/records.json'));const parties=JSON.parse(fs.readFileSync('scripts/german-election-import/parties.json'));const ids=new Set(parties.map(p=>p.id));
assert.equal(records.length,49);assert.equal(new Set(records.map(e=>e.id)).size,49);
for(const e of records){model.validateWorldElection(e);assert.equal(e.countryId,'de');assert.equal(e.publication,'published');assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),e.totalSeats);for(const r of e.results)if(r.partyId)assert.ok(ids.has(r.partyId));if(e.resultCoverage==='complete')assert.ok(Math.abs(e.results.reduce((n,r)=>n+(r.share||0),0)-100)<.01);}
const at=d=>records.find(e=>e.startDate===d);
assert.equal(records.filter(e=>e.body==='Bundestag').length,21);
assert.equal(at('1949-08-14').totalSeats,410);assert.match(at('1949-08-14').voteBasis,/Single-ballot/);assert.equal(at('2025-02-23').totalSeats,630);
assert.match(at('1987-01-25').title,/West Germany/);assert.doesNotMatch(at('1990-12-02').title,/West Germany/);
assert.ok(at('1878-07-30'));assert.equal(at('1878-06-30'),undefined);
assert.equal(at('1919-01-19').totalSeats,423);assert.equal(at('1920-06-06').totalSeats,459);
for(const d of ['1933-03-05','1933-11-12','1936-03-29','1938-04-10','1938-12-04'])assert.equal(at(d).legitimacy.level,'uncompetitive');
assert.equal(at('1938-04-10').totalSeats+at('1938-12-04').totalSeats,855);assert.equal(at('1938-12-04').round,'Territorial supplementary election');assert.ok(!records.some(e=>e.startDate.startsWith('1945')||e.startDate==='1868-04-27'));
console.log('German archive: 49 validated records; territorial scope, seat sums, party references and single-list distinctions passed.');
