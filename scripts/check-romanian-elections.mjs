import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){
 let src=fs.readFileSync(file,'utf8');
 for(const [from,to] of Object.entries(imports))src=src.replaceAll("'"+from+"'","'"+to+"'");
 return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const model=await import(moduleUrl('lib/world.ts',{'./house':moduleUrl('lib/house.ts'),'./legitimacy':moduleUrl('lib/legitimacy.ts')}));
const partyModel=await import(moduleUrl('lib/country-parties.ts'));
const root='scripts/romanian-election-import/';
const records=JSON.parse(fs.readFileSync(root+'records.json')),parties=JSON.parse(fs.readFileSync(root+'parties.json'));
const audit=JSON.parse(fs.readFileSync(root+'reconciliation.json')),primary=JSON.parse(fs.readFileSync(root+'primary-reconciliation.json'));
const ids=new Set(records.map(e=>e.id)),profiles=new Map(parties.map(p=>[p.id,p]));
assert.equal(records.length,116);assert.equal(ids.size,records.length);
for(const p of parties)partyModel.validateParty(p);
for(const e of records){
 model.validateWorldElection(e);assert.equal(e.countryId,'ro');assert.equal(e.publication,'published');assert.equal(e.live.enabled,false);
 assert.ok(e.sources.length);assert.ok(!e.legitimacy);
 for(const id of e.linkedElectionIds||[])assert.ok(ids.has(id));
 for(const r of e.results)if(r.partyId){assert.ok(profiles.has(r.partyId));assert.equal(r.color,profiles.get(r.partyId).color);assert.deepEqual(r.ideologyIds,[]);}
 const a=audit.find(a=>a.id===e.id);assert.ok(a);
 assert.equal(e.results.reduce((n,r)=>n+(r.votes||0),0),a.recordedVotes);
 assert.equal(e.results.reduce((n,r)=>n+(r.seats||0),0),a.recordedSeats);
 if(e.resultCoverage==='complete'){
  if(a.expectedVotes!==null)assert.equal(a.recordedVotes,a.expectedVotes);
  if(a.expectedSeats!==null)assert.equal(a.recordedSeats,a.expectedSeats);
 }
 if(e.precision!=='day'){assert.equal(e.dateStatus,'expected');assert.ok(e.results.every(r=>r.share===null));}
 if(e.status==='held'&&!e.results.length){assert.equal(e.resultStatus,'not-entered');assert.equal(e.resultCoverage,'partial');assert.equal(e.totalSeats,null);}
}
const get=id=>records.find(e=>e.id===id);
for(const year of [1992,1996,2000,2004,2009,2014,2019,2025]){
 const rounds=records.filter(e=>e.type==='presidential'&&e.startDate.startsWith(String(year))).sort((a,b)=>a.startDate.localeCompare(b.startDate));
 assert.equal(rounds.length,2);assert.equal(rounds[0].results.filter(r=>r.advanced).length,2);assert.equal(rounds[0].results.filter(r=>r.winner).length,0);assert.equal(rounds[1].results.filter(r=>r.winner).length,1);assert.ok(rounds[0].linkedElectionIds.includes(rounds[1].id));
}
const annulled=get('world-romania-president-2024-11-24'),cancelled=get('world-romania-president-2024-12-08');
assert.equal(annulled.status,'cancelled');assert.ok(annulled.results.length);assert.ok(annulled.results.every(r=>!r.winner&&!r.advanced));assert.match(annulled.title,/annulled/);
assert.equal(cancelled.status,'cancelled');assert.deepEqual(cancelled.results,[]);
assert.equal(get('world-romania-president-1990-05-20').results.find(r=>r.winner).name,'Ion Iliescu');
assert.equal(get('world-romania-president-2025-05-18').results.find(r=>r.winner).name,'Nicușor Dan');
for(const p of primary){
 const e=get(p.id);assert.equal(e.results.reduce((n,r)=>n+r.votes,0),p.validVotes);
 for(const r of e.results)assert.equal(r.votes,p.candidates[r.name]);
 assert.equal(e.turnout,Number((p.attendance/p.registered*100).toFixed(6)));
}
for(const year of [1974,1975,1980,1985]){
 const e=records.find(e=>e.type==='presidential'&&e.startDate.startsWith(String(year)));
 assert.equal(e.electionMethod,'indirect');assert.equal(e.resultCoverage,'partial');assert.equal(e.results[0].winner,true);assert.equal(e.results[0].votes,null);assert.equal(e.results[0].share,null);assert.equal(e.turnout,null);
}
assert.ok(get('world-romania-chamber-1922-03-01').results.every(r=>r.votes===null&&r.share===null));
assert.equal(get('world-romania-chamber-1922-03-01').totalSeats,369);
assert.equal(get('world-romania-senate-1928-12-12').totalSeats,113);
assert.match(get('world-romania-senate-1928-12-12').title,/universal-college/);
assert.equal(get('world-romania-assembly-1952-11-30').results.length,1);
assert.equal(get('world-romania-assembly-1952-11-30').results[0].votes,10187833);
assert.equal(get('world-romania-chamber-1946-11-19').results[0].seats,347);
for(const [year,chamber,senate] of [[1990,396,119],[1992,341,143],[1996,343,143],[2000,345,140],[2004,332,137],[2008,334,137],[2012,412,176],[2016,329,136],[2020,330,136],[2024,331,134]]){
 for(const [office,capacity] of [['chamber',chamber],['senate',senate]]){
  const e=records.find(e=>e.id.startsWith('world-romania-'+office+'-'+year));assert.equal(e.totalSeats,capacity);assert.equal(e.resultCoverage,'complete');assert.equal(e.results.reduce((n,r)=>n+r.seats,0),capacity);
 }
}
assert.equal(get('world-romania-senate-2024-12-01').results.find(r=>r.name==='Party of Young People').seats,7);
assert.equal(get('world-romania-chamber-2024-12-01').results.find(r=>r.name==='Party of Young People').seats,24);
assert.ok(!records.some(e=>e.status==='scheduled'));

// Exercise the real repository loader with a response limit and duplicate names.
const source=fs.readFileSync('db/politics.ts','utf8');
const loaderSource=source.slice(source.indexOf('export async function getCountryParties('),source.indexOf('export async function saveCountryParty('));
const loader=ts.transpileModule(loaderSource,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace('export async function','async function');
let requested=[],fail=false;
const rows=Array.from({length:1127},(_,i)=>({id:String(i).padStart(5,'0'),name:'Repeated name',archived:i%100===0}));
const supabase={from(table){assert.equal(table,'ea_country_parties');let start,end,filter;return {select(){return this},order(){return this},range(a,b){start=a;end=b;return this},eq(k,v){assert.equal(k,'archived');filter=v;return this},then(resolve){requested.push([start,end,filter]);return Promise.resolve(fail?{data:null,error:new Error('Query failed')}:{data:rows.filter(r=>filter===undefined||r.archived===filter).slice(start,end+1),error:null}).then(resolve)}}}};
const load=new Function('supabase',loader+';return getCountryParties;')(supabase);
assert.equal((await load(true)).length,1127);assert.deepEqual(requested.map(r=>r.slice(0,2)),[[0,499],[500,999],[1000,1499]]);
requested=[];assert.equal((await load()).length,1115);assert.ok(requested.every(r=>r[2]===false));
fail=true;await assert.rejects(load(),/Query failed/);
console.log('Romania: 116 records; modern chamber totals, separate rounds, annulment, indirect selections, coalition cells, historical gaps, party references and party-loader pagination passed.');
