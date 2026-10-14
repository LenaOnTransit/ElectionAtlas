import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {validateGeographyDataset,geographyView,comparisonElections,combinedResult} from '../lib/election-geography.mjs';
import {netherlandsMunicipalRoute,netherlandsMunicipalYears} from '../lib/netherlands-geography.mjs';
const raw=await fs.readFile('public/nl-municipal-history.json','utf8');
const data=validateGeographyDataset(JSON.parse(raw));
const audit=JSON.parse(await fs.readFile('scripts/netherlands-municipal-history-sources.json','utf8'));
const election=id=>data.elections.find(e=>e.id===id);
const sum=results=>{const votes={};for(const r of results)for(const [p,n]of Object.entries(r.votes))votes[p]=(votes[p]||0)+n;return votes;};
test('eight Dutch elections preserve every local denominator and reconcile documented national differences',()=>{
 assert.deepEqual(data.elections.map(e=>Number(e.id)),[2003,2006,2010,2012,2017,2021,2023,2025]);
 assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),audit.sha256);
 const mapped=[489,458,430,415,388,352,342,342];
 for(const [i,e]of data.elections.entries()){
  const view=geographyView(data,e.id),a=audit.elections[e.id];assert.equal(view.units.length,mapped[i]);assert.ok(view.units.every(u=>u.result));
  assert.equal(Object.keys(e.results).length,a.resultAreas);assert.ok(view.units.some(u=>u.id===e.defaultUnitId));
  const votes=sum(Object.values(e.results));assert.deepEqual(votes,a.municipalPartyVotes);
  assert.equal(Object.values(votes).reduce((a,b)=>a+b,0),a.validVotes);
  for(const r of Object.values(e.results))assert.equal(Object.values(r.votes).reduce((a,b)=>a+b,0),r.valid);
  const difference=a.validVotes-a.certifiedNationalValidVotes;
  assert.equal(difference,e.id==='2017'?8797:e.id==='2021'?-1:0);
  if(difference)assert.match(e.coverageNote,/national/);else assert.deepEqual(votes,a.nationalPartyVotes);
  assert.equal(e.parties.find(p=>p.id==='d66').classification,'centre');if(Number(e.id)>=2021)assert.equal(e.parties.find(p=>p.id==='volt').classification,'centre');
  assert.equal(netherlandsMunicipalRoute('world-netherlands-'+e.id),'/municipalities/netherlands?year='+e.id);
 }
 assert.deepEqual([...netherlandsMunicipalYears],mapped.map((_,i)=>Number(data.elections[i].id)));
 assert.equal(netherlandsMunicipalRoute('world-netherlands-2002'),null);
 // The joint list is never substituted into historical separate-party totals.
 assert.ok(election('2017').parties.some(p=>p.id==='pvda'));assert.ok(election('2017').parties.some(p=>p.id==='gl'));
 assert.ok(!election('2017').parties.some(p=>p.id==='gl-pvda'));
});
test('six explicitly sourced pairs select different prior elections and aggregate whole mergers exactly',()=>{
 assert.deepEqual(comparisonElections(data,election('2025')).map(e=>e.id),['2023','2021','2017']);
 assert.equal(geographyView(data,'2025','2017').previous.id,'2017');assert.equal(geographyView(data,'2025','not-loaded').previous,null);
 for(const [after,before,count]of [['2021','2017',327],['2023','2021',334],['2023','2017',310],['2025','2023',338],['2025','2021',330],['2025','2017',308]]){
  const v=geographyView(data,after,before);assert.equal(v.comparedUnits,count);assert.equal(v.comparedUnits,audit.elections[after].comparisons[before]);
  assert.ok(v.maxShift>=1);assert.ok(v.units.filter(u=>u.shift).every(u=>Math.abs(u.shift.change)<=v.maxShift));
 }
 const view=geographyView(data,'2025','2021');const amsterdam=view.units.find(u=>u.id==='2025-GM0363');
 assert.deepEqual(amsterdam.previousResult.votes,sum([election('2021').results['2021-GM0363'],election('2021').results['2021-GM0457']]));
 assert.equal(amsterdam.previousResult.turnout,null);
 const cuijk=view.units.find(u=>u.id==='2025-GM1982');assert.equal(election('2025').comparisons.find(c=>c.electionId==='2021').unitMap[cuijk.id].length,5);
 assert.equal(cuijk.previousResult.valid,[756,786,815,1684,1702].reduce((n,c)=>n+election('2021').results['2021-GM'+String(c).padStart(4,'0')].valid,0));
 const split=geographyView(data,'2021','2017').units.find(u=>u.id==='2021-GM0824');assert.equal(split.previousResult,undefined);assert.equal(split.shift,null);
 assert.equal(geographyView(data,'2021','2017').units.find(u=>u.id==='2021-GM0518').shift,null);
 assert.equal(view.units.find(u=>u.id==='2025-GM0402').shift,null); // Hilversum/Gooise Meren partial correction.
 assert.equal(geographyView(data,'2025','2023').units.find(u=>u.id==='2025-GM0080').shift,null); // 2025 boundary correction.
 assert.equal(combinedResult(election('2021'),['unknown']),undefined);
 for(const id of ['2003','2006','2010','2012','2017'])assert.deepEqual(comparisonElections(data,election(id)),[]);
});
test('mapped comparisons reject missing provenance, reused origins and bad boundary joins',()=>{
 for(const mutate of [d=>d.elections.at(-1).comparisons[0].sources=[],d=>d.elections.at(-1).comparisons[0].unitMap.unknown=['2023-GM0363'],d=>d.elections.at(-1).comparisons[0].unitMap['2025-GM0363']=['unknown'],d=>d.elections.at(-1).comparisons[0].note='',d=>d.elections.at(-1).comparisons[0].sources[0].url='javascript:alert(1)',d=>d.elections.at(-1).defaultUnitId='unknown']){
  const bad=structuredClone(data);mutate(bad);assert.throws(()=>validateGeographyDataset(bad),/Invalid election geography/);
 }
 const duplicate=structuredClone(data),mapping=duplicate.elections.at(-1).comparisons[0].unitMap;const keys=Object.keys(mapping);mapping[keys[1]]=mapping[keys[0]];assert.throws(()=>validateGeographyDataset(duplicate),/reused/);
 const otherCountry=structuredClone(data);otherCountry.elections.find(e=>e.id==='2021').country='Other';assert.ok(!comparisonElections(otherCountry,otherCountry.elections.at(-1)).some(e=>e.id==='2021'));
 const otherOffice=structuredClone(data);otherOffice.elections.find(e=>e.id==='2021').name='Presidency';assert.ok(!comparisonElections(otherOffice,otherOffice.elections.at(-1)).some(e=>e.id==='2021'));
});
test('actual viewer renders earlier maps, the multiple-election picker, missing comparisons and public source notes',async()=>{
 const folder=await fs.mkdtemp(path.resolve('scripts/.geography-history-check-'));
 try{
  const compile=s=>ts.transpileModule(s,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
  await fs.writeFile(path.join(folder,'appearance.mjs'),compile(await fs.readFile('app/appearance.tsx','utf8')));
  await fs.writeFile(path.join(folder,'stubs.mjs'),`import {createElement} from 'react';export const WorldNav=()=>null;export const AppLink=({href,children})=>createElement('a',{href},children);`);
  const source=(await fs.readFile('app/geography/view.tsx','utf8')).replace("'../../src/navigation'","'./stubs.mjs'").replace("'../world/shared'","'./stubs.mjs'").replace("'../appearance'","'./appearance.mjs'").replace("'../../lib/election-geography.mjs'",JSON.stringify(pathToFileURL(path.resolve('lib/election-geography.mjs')).href));
  await fs.writeFile(path.join(folder,'view.mjs'),compile(source));const {default:View}=await import(pathToFileURL(path.join(folder,'view.mjs')));
  const html=renderToStaticMarkup(createElement(View,{data,initialView:{comparison:true,previousElectionId:'2021'}}));
  assert.match(html,/2021 → 2025/);assert.match(html,/Compare with/);assert.match(html,/330 of 342 municipalities/);assert.match(html,/complete municipality mergers/);
  const old=renderToStaticMarkup(createElement(View,{data,initialElectionId:'2003'}));assert.match(old,/Tweede Kamer · 2003/);assert.match(old,/22 January 2003/);assert.match(old,/Amsterdam/);assert.doesNotMatch(old,/vote balance|Left–right shift since/);
  const sourceWarning=renderToStaticMarkup(createElement(View,{data,initialElectionId:'2017'}));assert.match(sourceWarning,/8,797 above/);assert.match(sourceWarning,/Boxmeer and Bergeijk/);
  const split=renderToStaticMarkup(createElement(View,{data,initialElectionId:'2021',initialView:{comparison:true,unitId:'2021-GM0824',previousElectionId:'2017'}}));assert.match(split,/Missing results are shown as unavailable/);
  for(const output of [html,old,sourceWarning,split])assert.doesNotMatch(output,/moderator|admin-only|editor-only|TODO|hidden ideology|private nine|NaN|Infinity/i);
  // Prior mapped municipalities must not be mislabelled as outside-map areas.
  const outside=html.slice(html.indexOf('Results outside the map'));assert.doesNotMatch(outside,/Alkmaar|Eindhoven/);
 }finally{await fs.rm(folder,{recursive:true,force:true});}
});
