import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {validateGeographyDataset,geographyView,comparableElection,rankedResults,winningMargin,voteShift} from '../lib/election-geography.mjs';
import {netherlandsGeography} from '../lib/netherlands-geography.mjs';
const result=votes=>({votes,valid:Object.values(votes).reduce((a,b)=>a+b,0),turnout:null});
function fixture(){const parties=[{id:'alpha',name:'Alpha',color:'#112233',classification:'left'},{id:'beta',name:'Beta',color:'#445566',classification:'right'}];return {version:1,id:'test-regions',title:'Example regional results',unitLabel:'region',unitPlural:'regions',defaultElectionId:'second',description:'Regional results.',coverageNote:'Valid votes.',checked:'2026-01-01',notes:[],sources:[],units:[{id:'north',name:'North',population:100},{id:'south',name:'South'},{id:'postal',name:'Postal'}],boundaries:[{id:'stable',label:'Example boundaries',width:100,height:100,features:{north:{path:'M0,0L50,0L50,50Z',center:[25,25]},south:{path:'M50,50L100,50L100,100Z',center:[75,75]}}}],elections:[{id:'first',label:'2010',dateLabel:'1 January 2010',name:'Assembly',country:'Example',boundarySetId:'stable',voteBasis:'Valid votes',parties,results:{north:result({alpha:30,beta:70}),south:result({alpha:40,beta:60}),postal:result({alpha:5,beta:5})}},{id:'second',label:'2014',dateLabel:'1 January 2014',name:'Assembly',country:'Example',boundarySetId:'stable',voteBasis:'Valid votes',previousElectionId:'first',parties,results:{north:result({alpha:60,beta:40})}}]};}
test('arbitrary election IDs and units use explicit comparisons, retaining missing results',()=>{
 const d=validateGeographyDataset(fixture()),v=geographyView(d,'second');assert.equal(v.previous.id,'first');assert.equal(v.units.length,2);assert.equal(v.units[0].shift.change,60);assert.equal(v.units[1].result,undefined);assert.equal(v.units[1].shift,null);assert.equal(v.maxShift,60);assert.equal(v.comparedUnits,1);assert.equal(v.leftShifted,1);assert.equal(v.maxPopulation,100);
 const standalone=geographyView(d,'first');assert.equal(standalone.previous,null);assert.equal(standalone.units[0].shift,null);assert.equal(geographyView(d,'not-found').election.id,'second');
 const noLink=structuredClone(d);delete noLink.elections[1].previousElectionId;assert.equal(comparableElection(noLink,noLink.elections[1]),null);
 const differentBasis=structuredClone(d);differentBasis.elections[1].voteBasis='Electoral votes';assert.equal(geographyView(differentBasis,'second').previous,null);
 const differentBoundaries=structuredClone(d);differentBoundaries.boundaries.push({...d.boundaries[0],id:'changed'});differentBoundaries.elections[1].boundarySetId='changed';assert.equal(geographyView(differentBoundaries,'second').previous,null);
});
test('party metadata is election-specific and absent classifications do not enable arrows',()=>{
 const d=fixture();d.elections[1].parties=structuredClone(d.elections[1].parties);d.elections[1].parties[0].classification='right';assert.equal(geographyView(validateGeographyDataset(d),'second').units[0].shift.change,-60);
 for(const e of d.elections)for(const p of e.parties)delete p.classification;assert.equal(geographyView(d,'second').hasClassifications,false);
 assert.equal(voteShift(undefined,result({alpha:1}),{}),null);assert.equal(voteShift(result({}),result({alpha:1}),{}),null);
 assert.deepEqual(rankedResults(result({})),[]);assert.equal(winningMargin(result({alpha:10})),100);assert.equal(winningMargin(result({alpha:10,beta:10})),0);
});
test('invalid joins, duplicate IDs, unreconciled votes and malformed geometry fail validation',()=>{
 for(const mutate of [d=>d.units.push(d.units[0]),d=>d.elections[1].results.unknown=result({alpha:1}),d=>d.elections[1].results.north=result({unknown:1}),d=>d.elections[1].results.north.valid++,d=>d.elections[1].results.north.votes.alpha=-1,d=>d.boundaries[0].features.north.center=[NaN,0],d=>d.elections[1].previousElectionId='unknown',d=>d.elections[1].boundarySetId='unknown',d=>d.elections[1].parties[0].color='red',d=>d.units[0].name=42,d=>d.sources.push({label:'Unsafe',url:'javascript:alert(1)'}),d=>d.elections[1].results.north.source='javascript:alert(1)',d=>d.boundaries[0].width=Infinity]){const d=structuredClone(fixture());mutate(d);assert.throws(()=>validateGeographyDataset(d),/Invalid election geography dataset/);}
});
test('Dutch adapter preserves all certified votes, boundaries, population and fixed centre classifications',async()=>{
 const source=JSON.parse(await fs.readFile('public/nl-municipal-2023-2025.json','utf8')),before=JSON.stringify(source),d=netherlandsGeography(source);
 assert.equal(d.units.length,346);assert.equal(geographyView(d,'2025').units.length,342);assert.equal(geographyView(d,'2025').comparedUnits,342);
 for(const e of d.elections){for(const id of ['d66','volt'])assert.equal(e.parties.find(p=>p.id===id).classification,'centre');for(const u of source.municipalities){assert.deepEqual(e.results[u.id],u.results[e.id]);assert.equal(d.boundaries[0].features[u.id].path,u.path);assert.equal(d.units.find(x=>x.id===u.id).population,u.population);}const totals={};let valid=0;for(const r of Object.values(e.results)){valid+=r.valid;for(const [id,n]of Object.entries(r.votes))totals[id]=(totals[id]||0)+n;}assert.equal(valid,source.national[e.id].valid);assert.deepEqual(totals,source.national[e.id].votes);}
 assert.equal(JSON.stringify(source),before);
});
test('the actual shared renderer renders a non-Dutch standalone election, missing results and accessible maps',async()=>{
 const folder=await fs.mkdtemp(path.resolve('scripts/.geography-check-'));
 try{
  const compile=source=>ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
  await fs.writeFile(path.join(folder,'appearance.mjs'),compile(await fs.readFile('app/appearance.tsx','utf8')));
  await fs.writeFile(path.join(folder,'stubs.mjs'),`import {createElement} from 'react';export const WorldNav=()=>null;export const AppLink=({href,children})=>createElement('a',{href},children);`);
  const source=(await fs.readFile('app/geography/view.tsx','utf8')).replace("'../../src/navigation'","'./stubs.mjs'").replace("'../world/shared'","'./stubs.mjs'").replace("'../appearance'","'./appearance.mjs'").replace("'../../lib/election-geography.mjs'",JSON.stringify(pathToFileURL(path.resolve('lib/election-geography.mjs')).href));
  await fs.writeFile(path.join(folder,'view.mjs'),compile(source));const {default:View}=await import(pathToFileURL(path.join(folder,'view.mjs')));
  const data=validateGeographyDataset(fixture());const html=renderToStaticMarkup(createElement(View,{data}));assert.match(html,/Assembly · 2014/);assert.match(html,/Compare with 2010/);assert.doesNotMatch(html,/vote balance|Left–right shift since|Netherlands|2023|2025/);assert.match(html,/South: Results not available/);assert.match(html,/Population-sized circles/);
  const old=renderToStaticMarkup(createElement(View,{data,initialElectionId:'first'}));assert.doesNotMatch(old,/Compare with/);assert.match(old,/Assembly · 2010/);assert.match(old,/Postal/);
  const compared=renderToStaticMarkup(createElement(View,{data,initialView:{comparison:true,layer:'shift'}}));assert.match(compared,/2010 → 2014/);assert.match(compared,/60.00 pp ← left/);assert.match(compared,/marker-end=/);assert.match(compared,/1 of 2 areas have comparable results/);
  const missing=renderToStaticMarkup(createElement(View,{data,initialView:{comparison:true,unitId:'south'}}));assert.match(missing,/Missing results are shown as unavailable/);assert.match(missing,/Vote-balance comparison is not available/);assert.doesNotMatch(missing,/NaN|Infinity/);
  const added=structuredClone(data);added.elections[1].parties.push({id:'gamma',name:'New party',color:'#778899'});added.elections[1].results.north=result({alpha:50,gamma:50});const partyComparison=renderToStaticMarkup(createElement(View,{data:validateGeographyDataset(added),initialView:{comparison:true}}));assert.match(partyComparison,/New party/);assert.match(partyComparison,/Beta/);assert.match(partyComparison,/50.00 pp/);
  const population=renderToStaticMarkup(createElement(View,{data,initialView:{layout:'population'}}));assert.match(population,/<circle/);assert.match(population,/South: Results not available/);
  const single=structuredClone(data);single.elections=[single.elections[1]];delete single.elections[0].previousElectionId;for(const p of single.elections[0].parties)delete p.classification;const standalone=renderToStaticMarkup(createElement(View,{data:validateGeographyDataset(single),initialView:{comparison:true,layer:'shift'}}));assert.doesNotMatch(standalone,/Compare with|vote balance|Left–right shift since/);
  globalThis.localStorage={getItem:()=> 'accessible'};const accessible=renderToStaticMarkup(createElement(View,{data}));assert.match(accessible,/url\(#.*-party-/);assert.match(accessible,/Colours and patterns match/);delete globalThis.localStorage;
 }finally{await fs.rm(folder,{recursive:true,force:true});}
});
