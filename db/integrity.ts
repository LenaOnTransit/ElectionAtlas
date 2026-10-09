import {supabase} from '../lib/supabase';
export type IntegrityFinding={finding_key:string;record_id:string;rule:string;severity:'error'|'warning'|'info';scope:string;subject:string;explanation:string;evidence:Record<string,unknown>;fingerprint:string;active:boolean;review_status:'open'|'fixed'|'accepted-exception';review_note:string;first_seen:string;last_seen:string;resolved_at:string|null;country_id:string;election_title:string;election_type:string};
export type IntegrityDashboard={recordsTotal:number;recordsScanned:number;lastChecked:string|null;lastFullScan:{id:string;status:string;records_scanned:number;records_target:number;started_at:string;finished_at:string|null}|null;pending:number;failures:number;counts:{error:number;warning:number;info:number;open:number};countries:{id:string;name:string}[]};
export type IntegrityFilters={search:string;country:string;election:string;type:string;severity:string;status:string;page:number};
export async function integrityAction(action:string,args:Record<string,unknown>={}){const {data,error}=await supabase.rpc('ea_integrity',{action,args});if(error)throw Error(error.message);return data;}
export async function integrityDashboard():Promise<IntegrityDashboard>{return integrityAction('dashboard');}
export async function integrityFindings(filters:IntegrityFilters):Promise<{rows:IntegrityFinding[];total:number}>{
 let query=supabase.from('ea_integrity_findings').select('*',{count:'exact'}).order('first_seen',{ascending:false}).order('finding_key');
 for(const [key,value] of Object.entries({country_id:filters.country,record_id:filters.election,election_type:filters.type,severity:filters.severity,review_status:filters.status}))if(value)query=query.eq(key,value);
 // Avoid interpolating user input into PostgREST's OR grammar. Search election,
 // rule and explanations through a protected, computed search text column.
 if(filters.search.trim())query=query.ilike('search_text','%'+filters.search.trim().replace(/[\\%_]/g,'\\$&')+'%');
 const {data,error,count}=await query.range(filters.page*50,filters.page*50+49);if(error)throw Error(error.message);return {rows:(data||[]) as IntegrityFinding[],total:count||0};
}
export async function integrityContext(id:string){const {data,error}=await supabase.from('ea_integrity_context').select('settings,note').eq('record_id',id).maybeSingle();if(error)throw Error(error.message);return data;}
