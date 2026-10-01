import {save} from '../db/content';
import {getSenate} from '../db/senate';
import {validateSenate} from './senate';
import {validateCountry,validateWorldElection} from './world';
import {saveWorldCountry,saveWorldElection,worldHistory,getWorld} from '../db/world';
export async function saveContent(kind:string,value:any) {
  if(kind==='senate')validateSenate(value);
  if(kind==='article'&&(!value.title?.trim()||!['draft','published'].includes(value.status)))throw Error('Title and status required.');
  if(!['senate','article','election'].includes(kind))throw Error('Invalid record type.');
  await save(kind,value);return {ok:true};
}
export async function saveWorld(kind:string,value:any) {
  if(kind==='country'){validateCountry(value);await saveWorldCountry(value);return {value};}
  if(kind!=='election')throw Error('Invalid record type.');
  validateWorldElection(value);
  const {countries}=await getWorld(true);if(!countries.some(c=>c.id===value.countryId))throw Error('Choose an existing country.');
  return saveWorldElection(value);
}
export {worldHistory};
export async function liveResults(){const [data,senate]=await Promise.all([getWorld(),getSenate()]);return {data,senate};}
