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
const elections=JSON.parse(fs.readFileSync('scripts/south-africa-election-records.json'));
const parties=JSON.parse(fs.readFileSync('scripts/south-africa-party-profiles.json'));
assert.equal(elections.length,23);
assert.equal(elections.filter(e=>e.electionMethod==='direct').length,7);
assert.equal(elections.filter(e=>e.type==='presidential').length,9);
assert.equal(new Set(elections.map(e=>e.id)).size,23);
const allIds=new Set(elections.map(e=>e.id));
const partyIds=new Set(parties.map(p=>p.id));
for(const p of parties) {validateParty(p);assert.equal(p.country_id,'za');assert.equal(p.notes,'');}
const counts={1994:[19,19533498],1999:[16,15977142],2004:[21,15612671],2009:[26,17680729],2014:[29,18402497],2019:[48,17437379],2024:[52,16078093]};
for(const e of elections){
 validateWorldElection(e);
 assert.equal(e.countryId,'za');assert.equal(e.publication,'published');
 assert.ok(e.sources.length);assert.ok(e.title.includes('South Africa'));
 for(const r of e.results){assert.ok(partyIds.has(r.partyId));assert.equal(r.ideologyBasis.year,+e.startDate.slice(0,4));if(r.ideologyIds.length)assert.ok(r.ideologyBasis.sources.length);}
 for(const id of e.linkedElectionIds){assert.ok(allIds.has(id));assert.ok(elections.find(x=>x.id===id).linkedElectionIds.includes(e.id));}
 assert.equal(electionMetadata(e,'South Africa').title,e.title+' - World of Elections');
 // Public reader copy must contain no workflow instructions for moderators.
 assert.ok(!/moderator|admin-only|editor-only|TODO|publish after|do not publish|review before/i.test([e.summary,e.notes,e.government].join(' ')));
 if(e.totalSeats!==null)assert.equal(e.results.reduce((n,r)=>n+(r.seats??0),0),e.totalSeats);
 if(e.electionMethod==='direct'){
  const expected=counts[+e.startDate.slice(0,4)];assert.equal(e.results.length,expected[0]);assert.equal(e.results.reduce((n,r)=>n+r.votes,0),expected[1]);
  assert.ok(Math.abs(e.results.reduce((n,r)=>n+r.share,0)-100)<.05);
 }else if(e.type==='parliamentary'){
  assert.equal(e.totalSeats,e.body==='Senate'?90:54);
  assert.equal(e.turnout,null);assert.ok(e.results.every(r=>r.votes===null&&r.share===null));
 }else{
  assert.equal(e.results.filter(r=>r.winner).length,1);assert.equal(e.totalSeats,null);assert.equal(e.turnout,null);
  assert.ok(e.results.every(r=>r.seats===null&&r.previousSeats===null));
  if(e.results.length===1)assert.ok(e.results.every(r=>r.votes===null&&r.share===null));
  else assert.ok(Math.abs(e.results.reduce((n,r)=>n+r.share,0)-100)<1e-8);
 }
}
const assembly=year=>elections.find(e=>e.id==='world-south-africa-'+year);
const party=(e,name)=>e.results.find(r=>r.name===name);
assert.equal(party(assembly(1999),'New National Party').previousSeats,82);
assert.equal(party(assembly(2004),'Democratic Alliance').previousSeats,null);
assert.equal(party(assembly(2004),'Freedom Front Plus').previousSeats,3);
assert.equal(party(assembly(2024),'African National Congress').previousSeats,230);
assert.equal(party(assembly(2024),'African National Congress').seats,159);
assert.equal(party(assembly(2024),'Democratic Alliance').votes,3506864);
assert.equal(party(assembly(2024),'uMkhonto weSizwe').previousSeats,0);
assert.ok(assembly(1994).results.every(r=>r.previousSeats===null));
assert.equal(assembly(1994).endDate,'1994-04-29');
const p2024=elections.find(e=>e.id==='world-south-africa-presidential-2024');
assert.deepEqual(p2024.results.map(r=>r.votes),[283,44]);
assert.ok(p2024.results.every(r=>r.ideologyBasis.kind==='party-era'));
const importSql=fs.readFileSync('scripts/south-africa-election-import.sql','utf8');
assert.ok(importSql.startsWith('begin;'));assert.ok(importSql.includes('Election changed since baseline'));assert.ok(importSql.endsWith('commit;\n'));
console.log('South Africa: validated 23 elections, vote/seat totals, predecessor comparisons, sourced party ideology, public copy and SEO titles.');
