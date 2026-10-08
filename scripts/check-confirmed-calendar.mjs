import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const m=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const patch=JSON.parse(fs.readFileSync('scripts/calendar-2027-import/patch.json'));const ids=new Set();
for(const p of patch.elections){const e=p.after;m.validateWorldElection(e);assert.ok(!ids.has(e.id));ids.add(e.id);if(e.dateStatus==='tba'){assert.equal(e.countryId,'ht');assert.equal(e.startDate,'');assert.equal(e.precision,'unknown');assert.equal(e.dateStatus,'tba');assert.deepEqual(m.calendarDays(e,'2026-12'),[]);}else{assert.ok(e.startDate>='2026-10-08'&&e.startDate<=patch.cutoff);assert.equal(e.precision,'day');assert.equal(e.dateStatus,'confirmed');assert.equal(e.status,'scheduled');assert.ok(m.calendarDays(e,e.startDate.slice(0,7)).includes(e.startDate));}assert.equal(e.publication,'published');if(p.action==='update'){assert.equal(e.id,p.before.id);assert.equal(e.version,p.before.version+1);for(const key of ['results','house','contests','legitimacy','observers','title','countryId'])assert.deepEqual(e[key],p.before[key]);}else{assert.equal(e.results.length,0);assert.equal(e.resultStatus,'not-entered');}}
for(const c of patch.countries)m.validateCountry(c);
assert.equal(patch.elections.filter(p=>p.action==='insert').length,25);assert.equal(patch.elections.filter(p=>p.action==='update').length,7);
assert.equal(patch.elections.find(p=>p.after.countryId==='de').after.startDate,'2027-01-30');
assert.equal(patch.elections.find(p=>p.after.countryId==='kg').after.startDate,'2027-01-27');
assert.equal(patch.elections.filter(p=>p.after.countryId==='ke').length,3);
assert.ok(!ids.has('world-us-house-2026'));assert.ok(!ids.has('world-france-president-2027'));assert.ok(!ids.has('world-czech-senate-2026'));
const runoff=patch.elections.find(p=>p.after.id==='world-calendar-cz-senate-2026-runoff').after;assert.deepEqual(m.calendarDays(runoff,'2026-10'),['2026-10-16','2026-10-17']);
console.log('Confirmed calendar patch: 25 additions, 7 protected schedule updates and exact-day Calendar visibility passed.');
