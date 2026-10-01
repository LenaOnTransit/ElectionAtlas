import {readRecords,writeRecord} from './remote';
import {supabase} from '../lib/supabase';
import type {Country,WorldElection,WorldData} from '../lib/world';
export async function getWorld(all=false):Promise<WorldData>{const rows=await readRecords(['world_country','world_election'],all);return {countries:rows.filter(r=>r.kind==='world_country').map(r=>r.data as Country).sort((a,b)=>a.name.localeCompare(b.name)),elections:rows.filter(r=>r.kind==='world_election').map(r=>r.data as WorldElection)};}
export async function saveWorldElection(value:WorldElection,_userId?:string){return {value:await writeRecord('world_election',value)};}
export async function saveWorldCountry(value:Country){return writeRecord('world_country',value);}
export async function worldHistory(id:string){const {data,error}=await supabase.from('ea_revisions').select('created,data').eq('record_id',id).order('created',{ascending:false}).limit(20);if(error)throw error;return (data||[]).map(r=>({date:r.created,election:r.data}));}
