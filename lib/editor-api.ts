import {validateEducational} from './education.mjs';
import {getIdeologies} from '../db/ideologies';
import {validateIdeology} from './ideologies';
import {validatePublication} from './publication';
import {save} from '../db/content';
import {getSenate} from '../db/senate';
import {validateSenate} from './senate';
import {validateCountry,validateWorldElection} from './world';
import {saveWorldCountry,saveWorldElection,worldHistory,getWorld} from '../db/world';
export async function saveContent(kind:string,value:any) {
  if(kind==='article')validatePublication(value);
  if(kind==='article'&&value.articleType==='ideology')validateIdeology(value);
  if(kind==='article'&&value.articleType==='educational')validateEducational(value);
  if(kind==='senate')validateSenate(value);
  if(kind==='article'&&(!value.title?.trim()||!['draft','published'].includes(value.status)))throw Error('Title and status required.');
  if(kind==='article'&&(value.archived!==undefined&&typeof value.archived!=='boolean'||value.archived===true&&value.status!=='draft'))throw Error('Removed articles must be private drafts.');
  if(!['senate','article','election'].includes(kind))throw Error('Invalid record type.');
  await save(kind,value);return {ok:true};
}
export async function saveWorld(kind:string,value:any) {
  if(kind==='country'){validateCountry(value);await saveWorldCountry(value);return {value};}
  if(kind!=='election')throw Error('Invalid record type.');
  validateWorldElection(value);
  const ids=new Set(value.results.flatMap((r:any)=>r.ideologyIds||[]));if(ids.size){const known=new Set((await getIdeologies(true)).map(i=>i.id));if([...ids].some(id=>!known.has(id as string)))throw Error('An assigned ideology no longer exists. Remove its label or choose an existing guide.');}

  const {countries}=await getWorld(true);if(!countries.some(c=>c.id===value.countryId))throw Error('Choose an existing country.');
  return saveWorldElection(value);
}
export {worldHistory};
export async function liveResults(includeSenate=true){const [data,senate]=await Promise.all([getWorld(),includeSenate?getSenate():Promise.resolve(null)]);return {data,senate};}
