import {useState} from 'react';
import {supabase} from '../../lib/supabase';
import {navigate} from '../../src/navigation';
import type {AccountUser} from '../auth';

export default function DataRights({user}:{user:AccountUser}) {
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState('');
 async function download(){setBusy(true);setError('');try{
  const {data,error}=await supabase.rpc('ea_export_account');if(error)throw error;
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='world-of-elections-account.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  setMessage('Your account data has been downloaded as JSON.');
 }catch(e){setError(e instanceof Error?e.message:'The download failed. Please retry.')}finally{setBusy(false)}}
 async function erase(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');const form=event.currentTarget;const password=String(new FormData(form).get('password'));try{
  const {error:authError}=await supabase.auth.signInWithPassword({email:user.email,password});form.reset();if(authError)throw authError;
  const {error}=await supabase.rpc('ea_delete_account',{confirmation:'DELETE'});if(error)throw error;
  await supabase.auth.signOut({scope:'local'});navigate('/account?deleted=1');window.dispatchEvent(new Event('account-changed'));
 }catch(e){setError(e instanceof Error?e.message:'Deletion failed. Your account has not been deleted.')}finally{form.reset();setBusy(false)}}
 return <section className="account-privacy"><h2>Your data and privacy</h2><p>Download your account details and the election revisions you submitted in a machine-readable JSON file, free of charge.</p><button disabled={busy} onClick={download}>Download my data</button><details><summary>Delete my account and personal account data</summary><p>This permanently removes your sign-in account, email, username, moderator access and your saved revision history, and ends your sessions. Public election records and articles remain. Download your data first if you want a copy.</p><form onSubmit={erase}><label>Confirm with your password<input name="password" type="password" autoComplete="current-password" required maxLength={128}/></label><label className="checklabel"><input type="checkbox" required/>I understand this deletion is permanent.</label><button className="danger" disabled={busy}>Permanently delete my account</button></form></details><p className="meta">These tools support account erasure and data portability under GDPR Articles 17 and 20. Deletion of personal information in editorial coverage, and direct transfers to another controller, require separate review. Erasure rights have legal exceptions; other people’s rights must also be protected.</p><p role="alert">{error}</p><p role="status">{message}</p></section>;
}
