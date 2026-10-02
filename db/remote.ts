import {supabase} from '../lib/supabase';
export type RecordRow={id:string;kind:string;data:any;updated:string;is_public:boolean};
export async function readRecords(kinds:string[],all=false):Promise<RecordRow[]> {
  if(!all){const {data,error}=await supabase.rpc('ea_public_records',{record_kinds:kinds});if(error)throw error;return data||[];}
  let query=supabase.from('ea_records').select('id,kind,data,updated,is_public').in('kind',kinds).order('updated',{ascending:false});
  const {data,error}=await query;if(error)throw error;return data||[];
}
export async function writeRecord(kind:string,value:any) {
  const {data,error}=await supabase.rpc('ea_save_record',{record_kind:kind,payload:value});
  if(error)throw Error(error.code==='40001'?'This record changed in another session. Reload before saving.':error.message);
  return data;
}
