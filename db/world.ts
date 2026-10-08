import {readRecords,writeRecord} from './remote';
import {supabase} from '../lib/supabase';
import type {Country,WorldElection,WorldData} from '../lib/world';
export async function getWorld(all=false):Promise<WorldData>{const rows=all?await readRecords(['world_country','world_election'],true):await publicSummaries();return {countries:rows.filter(r=>r.kind==='world_country').map(r=>r.data as Country).sort((a,b)=>a.name.localeCompare(b.name)),elections:rows.filter(r=>r.kind==='world_election').map(r=>r.data as WorldElection)};}
export async function saveWorldElection(value:WorldElection,_userId?:string){return {value:await writeRecord('world_election',value)};}
export async function saveWorldCountry(value:Country){return writeRecord('world_country',value);}
export async function worldHistory(id:string){const {data,error}=await supabase.from('ea_revisions').select('created,data').eq('record_id',id).order('created',{ascending:false}).limit(20);if(error)throw error;return (data||[]).map(r=>({date:r.created,election:r.data}));}

async function publicSummaries(){
  const pageSize=500;
  const rows:{id:string;kind:string;data:any;updated:string}[]=[];
  for(let from=0;;from+=pageSize){
    const {data,error}=await supabase.rpc('ea_world_summaries').range(from,from+pageSize-1);
    if(error)throw error;
    rows.push(...(data||[]));
    if(!data||data.length<pageSize)break;
  }
  return rows;
}
export async function getWorldElection(id:string):Promise<WorldElection|null>{const {data,error}=await supabase.rpc('ea_public_election',{record_id:id});if(error)throw error;return data as WorldElection|null;}
