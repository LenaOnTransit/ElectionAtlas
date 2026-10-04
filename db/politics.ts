import {supabase} from '../lib/supabase';
import {validateParty,type CountryParty} from '../lib/country-parties';
import {validateScores,type Axis,type AxisScores,type IdeologyScores,type ParliamentPosition} from '../lib/political-axes';
export async function getCountryParties(all=false):Promise<CountryParty[]>{let q=supabase.from('ea_country_parties').select('*').order('name');if(!all)q=q.eq('archived',false);const {data,error}=await q;if(error)throw error;return data||[];}
export async function saveCountryParty(p:CountryParty){validateParty(p);const {data,error}=await supabase.from('ea_country_parties').upsert(p).select().single();if(error)throw error;return data as CountryParty;}
export async function getIdeologyScores():Promise<IdeologyScores[]>{const {data,error}=await supabase.from('ea_ideology_axes').select('ideology_id,scores');if(error)throw error;return data||[];}
export async function saveIdeologyScores(ideology_id:string,scores:AxisScores){validateScores(scores);const {error}=await supabase.from('ea_ideology_axes').upsert({ideology_id,scores});if(error)throw error;}
export async function getParliamentOrder(election_id:string,axes:Axis[],reverse=false):Promise<string[]>{const {data,error}=await supabase.rpc('ea_parliament_order',{election_id,axes,reverse_order:reverse});if(error)throw error;return (data||[]).map((r:{result_id:string})=>r.result_id);}
export async function getParliamentSpectrum(election_id:string,axes:Axis[],reverse=false):Promise<ParliamentPosition[]>{const {data,error}=await supabase.rpc('ea_parliament_spectrum',{election_id,axes,reverse_order:reverse});if(error)throw error;return data||[];}
