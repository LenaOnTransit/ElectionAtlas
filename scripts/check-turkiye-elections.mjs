import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
import {electionMetadata} from '../lib/seo.mjs';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const[from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const {validateWorldElection}=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const {validateParty}=await import(moduleUrl('lib/country-parties.ts'));
const read=name=>JSON.parse(fs.readFileSync('scripts/turkiye-election-import/'+name+'.json'));
const elections=read('records'),parties=read('parties'),audit=read('reconciliation'),primary=read('primary-reconciliation');
assert.equal(elections.length,42);assert.equal(elections.filter(e=>e.type==='parliamentary').length,28);assert.equal(elections.filter(e=>e.electionMethod==='indirect').length,10);
const ids=new Set(elections.map(e=>e.id)),pids=new Set(parties.map(p=>p.id));assert.equal(ids.size,42);parties.forEach(validateParty);
const get=(office,date)=>elections.find(e=>e.id===`world-turkiye-${office}-${date}`);
for(const e of elections){
 validateWorldElection(e);assert.equal(e.countryId,'tr');assert.equal(e.publication,'published');assert.ok(e.sources.length);
 assert.equal(electionMetadata(e,'Türkiye').title,e.title+' - World of Elections');
 assert.match(e.title,/^Türkiye .* election .*\d{4}$/);
 assert.ok(!/moderator|admin-only|editor-only|TODO|publish after|do not publish|review before/i.test([e.summary,e.notes,e.government].join(' ')));
 for(const id of e.linkedElectionIds){assert.ok(ids.has(id));assert.ok(elections.find(x=>x.id===id).linkedElectionIds.includes(e.id));}
 const a=audit.find(x=>x.id===e.id);assert.ok(a);assert.equal(e.results.reduce((n,r)=>n+r.votes,0),a.recordedVotes);
 if(e.totalSeats!==null)assert.equal(e.results.reduce((n,r)=>n+r.seats,0),a.recordedSeats);
 if(e.electionMethod==='indirect'){assert.equal(e.turnout,null);assert.equal(e.totalSeats,null);assert.match(e.voteBasis,/Legislators/);assert.equal(a.recordedVotes+a.nonCandidateBallots,a.ballotsCast);assert.ok(e.results.every(r=>Math.abs(r.share-r.votes/a.ballotsCast*100)<.000001));}
 for(const r of e.results){if(r.partyId)assert.ok(pids.has(r.partyId));if(r.ideologyIds.length){assert.ok(r.ideologyBasis.sources.length);assert.equal(r.ideologyBasis.kind,'party-era');}}
 if(e.resultCoverage==='complete'&&e.electionMethod==='direct'){assert.equal(a.recordedVotes,a.expectedVotes);if(e.totalSeats!==null)assert.equal(a.recordedSeats,a.expectedSeats);}
}
assert.equal(get('assembly','1983-11-06').totalSeats,400);assert.equal(get('assembly','1983-11-06').results.reduce((s,r)=>s+r.seats,0),399);
assert.equal(get('assembly','1961-10-15').resultCoverage,'partial');assert.equal(get('assembly','1969-10-12').resultCoverage,'partial');
const row=(office,date,name)=>get(office,date).results.find(r=>r.name===name);
assert.equal(row('assembly','2002-11-03','Justice and Development Party').seats,363);assert.equal(row('assembly','2002-11-03','Justice and Development Party').previousSeats,0);
assert.equal(row('assembly','2011-06-12','Justice and Development Party').seats,327);assert.equal(row('assembly','2011-06-12','Independents').seats,35);
assert.equal(row('assembly','2015-11-01','Justice and Development Party').previousSeats,258);
assert.equal(row('assembly','2023-05-14','Justice and Development Party').votes,19392462);assert.equal(row('assembly','2023-05-14',"Republican People's Party").seats,169);assert.equal(row('assembly','2023-05-14',"Republican People's Party").previousSeats,146);
assert.equal(row('assembly','2023-05-14','Party of Greens and the Left Future').previousSeats,null);
assert.equal(row('president','1950-05-22','İsmet İnönü').votes,64);assert.equal(get('president','1954-05-14').results.length,1);
assert.equal(row('president','2007-08-28','Abdullah Gül').votes,339);assert.equal(row('president','2023-05-28','Recep Tayyip Erdoğan').votes,27834589);
assert.equal(get('president','2023-05-14').results.filter(r=>r.winner).length,0);assert.equal(get('president','2023-05-14').results.filter(r=>r.advanced).length,2);
assert.notEqual(row('assembly','1957-10-27','Democrat Party').partyId,row('assembly','2007-07-22','Democrat Party').partyId);
assert.ok(row('assembly','1950-05-14',"Republican People's Party").ideologyIds.includes('ideology-republicanism'));assert.ok(!row('assembly','1950-05-14',"Republican People's Party").ideologyIds.includes('ideology-social-democracy'));
assert.equal(primary.every(x=>x.matched),true);assert.equal(primary.length,8);
console.log('Türkiye: 42 elections, historical and modern vote controls, list seats, indirect ballots, public copy and SEO validated.');
