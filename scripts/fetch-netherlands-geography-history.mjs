// Download public source snapshots for the Dutch municipal history importer.
// This script writes only a local cache and never publishes or accesses Supabase.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../.cache/dutch-geography');fs.mkdirSync(root,{recursive:true});
const codes=['TK20030122','TK20061122','TK20100609','TK20120912','TK20170315','TK20210317'];
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#39;|&apos;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
async function snapshot(code,id){
 const destination=path.join(root,`${code}${id?'-'+id:''}.json`);
 if(fs.existsSync(destination))return JSON.parse(fs.readFileSync(destination));
 let error;for(let attempt=0;attempt<3;attempt++)try{
  const response=await fetch(`https://www.verkiezingsuitslagen.nl/verkiezingen/detail/${code}${id?'/'+id:''}`,{signal:AbortSignal.timeout(30000)});
  if(!response.ok)throw Error('HTTP '+response.status);
  const text=await response.text(),match=text.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/);if(!match)throw Error('Missing official result snapshot');
  const result=JSON.parse(decode(match[1]));fs.writeFileSync(destination,JSON.stringify(result));return result;
 }catch(e){error=e;}throw error;
}
const jobs=[];for(const code of codes){const result=await snapshot(code);for(const op of result.Regios.Regios.find(r=>r.Name==='Gemeente').Options.filter(o=>o.Value!=='-')){if(!Number.isSafeInteger(op.Id)||op.Id<=0)throw Error('Invalid area reference');jobs.push({code,id:op.Id});}}
let next=0,done=0;await Promise.all(Array.from({length:8},async()=>{while(next<jobs.length){const job=jobs[next++];await snapshot(job.code,job.id);if(++done%100===0)console.log(`${done}/${jobs.length} official municipal snapshots cached`);}}));
const downloads=[
 ['https://www.cbs.nl/-/media/imported/documents/2008/01/2003-buurt-kaart.zip?sc_lang=nl-nl','boundaries-2003.zip'],
 ['https://www.cbs.nl/-/media/imported/documents/2010/13/buurt_2006_gn2.zip?sc_lang=nl-nl','boundaries-2006.zip'],
 ['https://download.cbs.nl/regionale-kaarten/2010-buurtkaart-shape-versie-3.zip','boundaries-2010.zip'],
 ['https://download.cbs.nl/regionale-kaarten/2012-buurtkaart-shape-versie-1.zip','boundaries-2012.zip'],
 ...[2017,2021,2023].map(year=>[`https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1/collections/gemeente_gegeneraliseerd/items?jaarcode=${year}&limit=1000&f=json`,`geometry-${year}-generalized.json`])
];
for(const [url,name]of downloads){const destination=path.join(root,name);if(fs.existsSync(destination))continue;const response=await fetch(url,{signal:AbortSignal.timeout(180000)});if(!response.ok)throw Error(name+': HTTP '+response.status);fs.writeFileSync(destination,new Uint8Array(await response.arrayBuffer()));console.log('Cached',name);}
console.log('Dutch geography source download complete. Run the Python importer to validate and build the public asset.');
