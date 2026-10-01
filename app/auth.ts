import { supabase } from '../lib/supabase';
import { redirect } from '../src/navigation';
export type AccountUser={userId:string;displayName:string;email:string;role:'reader'|'admin'};
export async function getUser():Promise<AccountUser|null> {
  const {data:{user},error}=await supabase.auth.getUser();
  if(!user) return null;
  if(error) throw error;
  const [{data:profile,error:profileError},{data:editor,error:editorError}]=await Promise.all([
    supabase.from('ea_profiles').select('username').eq('user_id',user.id).maybeSingle(),
    supabase.from('ea_editors').select('user_id').eq('user_id',user.id).maybeSingle(),
  ]);
  if(profileError||editorError)throw profileError||editorError;
  return {userId:user.id,displayName:profile?.username||user.user_metadata.username||'Reader',email:user.email||'',role:editor?'admin':'reader'};
}
export async function requireUser(returnTo:string) {
  const user=await getUser();if(!user)redirect('/account?returnTo='+encodeURIComponent(returnTo));return user;
}
