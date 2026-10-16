import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
import {electionMetadata} from '../lib/seo.mjs';
function moduleUrl(file,imports={}){let s=fs.readFileSync(file,'utf8');for(const[a,b]of Object.entries(imports))s=s.replaceAll("'"+a+"'","'"+b+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(s,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const {validateWorldElection}=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const {validateParty}=await import(moduleUrl('lib/country-parties.ts'));
const read=n=>JSON.parse(fs.readFileSync('scripts/portugal-election-import/'+n+'.json'));
const records=read('records'),parties=read('parties'),audit=read('reconciliation');
assert.equal(new Set(records.map(e=>e.id)).size,records.length);
parties.forEach(validateParty);const pids=new Set(parties.map(p=>p.id));
for(const e of records){
 validateWorldElection(e);assert.equal(e.countryId,'pt');assert.match(e.title,/^Portugal .* election.* \d{4}$/);assert.equal(electionMetadata(e,'Portugal').title,e.title+' - World of Elections');assert.equal(e.publication,'published');
 assert.ok(!/moderator|admin-only|editor-only|TODO|publish after|review before/i.test([e.summary,e.notes,e.government].join(' ')));
 assert.ok(e.sources.length);for(const r of e.results){if(r.partyId)assert.ok(pids.has(r.partyId));if(r.ideologyIds.length){assert.equal(r.ideologyBasis.kind,'party-era');assert.ok(r.ideologyBasis.sources.length);}if(e.type==='presidential'){assert.equal(r.previousSeats,null);assert.equal(r.seats,null);}}
 const a=audit.find(a=>a.id===e.id);if(a){assert.equal(e.results.reduce((s,r)=>s+(r.seats||0),0),a.recordedSeats);if(a.expectedVotes!==null)assert.equal(e.results.reduce((s,r)=>s+(r.votes||0),0),a.expectedVotes);if(a.expectedSeats!==null)assert.equal(a.recordedSeats,a.expectedSeats);}
 if(e.type==='presidential'&&e.electionMethod==='indirect')assert.equal(e.turnout,null);
}
const get=(y,body,round='')=>records.find(e=>e.startDate.startsWith(String(y))&&e.body===body&&e.round===round);
const current=get(2025,'Assembly of the Republic');assert.equal(current.id,'world-portugal-2025-assembly');assert.equal(current.totalSeats,230);assert.equal(current.results.reduce((s,r)=>s+r.seats,0),230);assert.equal(current.results.reduce((s,r)=>s+r.votes,0),6059321);assert.equal(current.turnout,58.25);assert.equal(current.results.find(r=>r.name==='Socialist Party').previousSeats,78);assert.equal(current.results.find(r=>r.name==='Chega').votes,1438554);
assert.equal(get(1913,'Chamber of Deputies').totalSeats,37);assert.equal(get(1913,'Chamber of Deputies').results.find(r=>r.name==='Democratic Party').seats,33);
assert.equal(get(1919,'Senate').results.find(r=>r.name==='Evolutionist Party / Republican Union').seats,27);assert.equal(get(1892,'Chamber of Deputies').results.find(r=>r.name==='Regenerator Party and others').seats,103);
assert.equal(get(1828,"People's Estate").precision,'month');assert.equal(get(1919,'President','1').startDate,'1919-08-06');assert.equal(get(1822,'Chamber of Deputies').startDate,'1822-08-18');assert.equal(get(1905,'Chamber of Deputies').startDate,'1905-02-12');
assert.equal(get(1925,'Senate').totalSeats,70);assert.equal(get(1925,'Senate').results.reduce((s,r)=>s+r.seats,0),65);
assert.equal(get(2026,'President','1').results.reduce((s,r)=>s+r.votes,0),5642696);assert.equal(get(2026,'President','2').results.find(r=>r.winner).votes,3502613);assert.equal(get(2026,'President','2').turnout,50.03);
assert.equal(get(2026,'President','2').endDate,'2026-02-15');assert.equal(get(1986,'President','1').results.filter(r=>r.winner).length,0);assert.equal(get(1986,'President','2').results.find(r=>r.winner).name,'Mário Soares');
assert.equal(get(1965,'President').results[0].votes,556);assert.equal(get(1972,'President').results[0].votes,616);
assert.equal(get(1822,'Chamber of Deputies').electionMethod,'direct');assert.equal(get(1918,'Chamber of Deputies').electionMethod,'direct');assert.equal(get(1918,'Senate').electionMethod,'indirect');assert.equal(get(1851,'Chamber of Deputies').electionMethod,'indirect');
for(const y of [1976,1979,1980,1983,1985,1987,1991,1995,1999,2002,2005,2009,2011,2015,2019,2022,2024,2025])assert.ok(get(y,'Assembly of the Republic'));
console.log(`Portugal: ${records.length} records, ${records.reduce((s,e)=>s+e.results.length,0)} rows; rounds, coalition subtotals, partial renewals, certified totals, previous seats and SEO verified.`);
