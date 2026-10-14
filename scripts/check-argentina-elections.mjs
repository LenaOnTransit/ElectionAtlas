import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
import {electionMetadata} from '../lib/seo.mjs';
function moduleUrl(file,imports={}) {
 let source=fs.readFileSync(file,'utf8');
 for(const [from,to] of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");
 return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const {validateWorldElection}=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const {validateParty}=await import(moduleUrl('lib/country-parties.ts'));
const elections=JSON.parse(fs.readFileSync('scripts/argentina-election-records.json'));
const parties=JSON.parse(fs.readFileSync('scripts/argentina-party-profiles.json'));
const tables=JSON.parse(fs.readFileSync('scripts/argentina-source-tables.json'));
const get=id=>elections.find(e=>e.id===id);
assert.equal(elections.length,56);
assert.equal(elections.filter(e=>e.body==='Chamber of Deputies').length,22);
assert.equal(elections.filter(e=>e.body==='Senate').length,19);
assert.equal(elections.filter(e=>e.type==='presidential').length,15);
const ids=new Set(elections.map(e=>e.id));assert.equal(ids.size,56);
const pids=new Set(parties.map(p=>p.id));parties.forEach(validateParty);
for(const e of elections){
 validateWorldElection(e);assert.equal(e.countryId,'ar');assert.equal(e.publication,'published');
 assert.ok(e.sources.length);assert.equal(electionMetadata(e,'Argentina').title,e.title+' - World of Elections');
 assert.ok(!/moderator|admin-only|editor-only|TODO|publish after|do not publish|review before/i.test([e.summary,e.notes,e.government].join(' ')));
 for(const id of e.linkedElectionIds){assert.ok(ids.has(id));assert.ok(get(id).linkedElectionIds.includes(e.id));}
 for(const r of e.results){if(r.name==='Unfilled seats')continue;assert.ok(pids.has(r.partyId));assert.equal(r.ideologyBasis.year,+e.startDate.slice(0,4));if(r.ideologyIds.length)assert.ok(r.ideologyBasis.sources.length);}
 if(e.totalSeats!==null)assert.equal(e.results.reduce((n,r)=>n+r.seats,0),e.totalSeats);
 const t=tables.find(t=>+e.startDate.slice(0,4)===t.year&&e.body===t.body||e.type==='presidential'&&!e.snap&&e.status==='held'&&+e.startDate.slice(0,4)===t.year&&t.body==='President'&&t.round===(e.round==='Runoff'?2:1));
 if(t){assert.equal(e.turnout,t.turnout);if(t.validVotes!==null)assert.equal(e.results.reduce((n,r)=>n+r.votes,0),t.validVotes);}
 if(e.precision==='year'){assert.equal(e.electionMethod,'indirect');assert.equal(e.turnout,null);assert.ok(e.results.every(r=>r.votes===null&&r.share===null));}
}
const party=(id,name)=>get(id).results.find(r=>r.name===name);
assert.equal(party('world-argentina-deputies-1983','Radical Civic Union').seats,129);
assert.equal(party('world-argentina-deputies-1985','Radical Civic Union').previousSeats,64);
assert.equal(party('world-argentina-deputies-1987','Radical Civic Union').previousSeats,65);
assert.equal(party('world-argentina-deputies-1989','Radical Civic Union').previousSeats,65);
assert.equal(get('world-argentina-deputies-1991').totalSeats,130);
assert.equal(get('world-argentina-deputies-1991').endDate,'1991-12-01');
assert.equal(get('world-argentina-deputies-1999').startDate,'1999-08-08');
assert.equal(get('world-argentina-deputies-2003').endDate,'2003-11-23');
assert.equal(get('world-argentina-senate-2001').totalSeats,72);
assert.equal(party('world-argentina-senate-2001','Justicialist Party').seats,42);
assert.equal(party('world-argentina-deputies-2025','La Libertad Avanza').seats,64);
assert.equal(party('world-argentina-deputies-2025','La Libertad Avanza').previousSeats,2);
assert.equal(party('world-argentina-senate-2025','La Libertad Avanza').seats,13);
assert.equal(get('world-argentina-presidential-runoff-2003').results.length,0);
assert.equal(get('world-argentina-presidential-runoff-2003').status,'cancelled');
assert.equal(party('world-argentina-presidential-runoff-2023','Javier Milei').votes,14554560);
assert.equal(party('world-argentina-presidential-parliamentary-2001','Adolfo Rodríguez Saá').votes,169);
assert.equal(party('world-argentina-presidential-parliamentary-2002','Eduardo Duhalde').votes,262);
// A known historical year is displayable without inventing a polling day.
validateWorldElection({...get('world-argentina-senate-1998'),precision:'year',dateStatus:'confirmed'});
assert.throws(()=>validateWorldElection({...get('world-argentina-senate-1998'),status:'scheduled'}));
console.log('Argentina: 56 elections validated; complete vote and renewal-seat sums, cohort comparisons, runoffs, indirect selections, public copy and SEO.');
