import {AppLink,navigate,routeSearch} from '../../src/navigation';
import {useState} from 'react';
import {supabase} from '../../lib/supabase';
import type {AccountUser} from '../auth';
import DataRights from './data-rights';
export default function Account({user,returnTo}:{user:AccountUser|null;returnTo:string}) {
 const [mode,setMode]=useState<'login'|'register'>('login');const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [message,setMessage]=useState('');
 async function submit(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');setMessage('');const form=new FormData(event.currentTarget);const email=String(form.get('email')).trim().toLowerCase();const password=String(form.get('password'));const username=String(form.get('username')||'').trim().toLowerCase();
  try{if(mode==='register'){
    if(!/^[a-z0-9_]{3,30}$/.test(username))throw Error('Username must be 3–30 letters, numbers, or underscores.');
    const {data,error}=await supabase.auth.signUp({email,password,options:{data:{username},emailRedirectTo:window.location.origin+import.meta.env.BASE_URL}});
    if(error)throw error;if(!data.session){setMessage('Check your email to confirm your account, then sign in.');setBusy(false);return;}
  }else{const {error}=await supabase.auth.signInWithPassword({email,password});if(error)throw error;}
  navigate(returnTo);window.dispatchEvent(new Event('account-changed'));
  }catch(e){setError(e instanceof Error?e.message:'Please retry.');setBusy(false);}}
 async function logout(){setBusy(true);const {error}=await supabase.auth.signOut();if(error){setError(error.message);setBusy(false);return;}navigate('/account');window.dispatchEvent(new Event('account-changed'));}
 if(user)return <><p>Signed in as <b>{user.displayName}</b> · {user.email}</p><p>{user.role==='admin'?'You have access to the private newsroom.':'Your reader account is ready. Browse all public coverage and election tools.'}</p>{user.role==='admin'&&<p><AppLink action className="primary" href="/editor">Open private newsroom</AppLink></p>}<button disabled={busy} onClick={logout}>Sign out</button><p role="alert">{error}</p><DataRights user={user}/></>;
 return <>{new URLSearchParams(routeSearch()).get('deleted')==='1'&&<p role="status">Your account and personal account data have been deleted.</p>}<p>Read without an account, or create your own. New accounts have reader access.</p><div className="tabs"><button onClick={()=>{setMode('login');setError('');setMessage('')}} className={mode==='login'?'active':''}>Sign in</button><button onClick={()=>{setMode('register');setError('');setMessage('')}} className={mode==='register'?'active':''}>Create account</button></div><form onSubmit={submit}>{mode==='register'&&<label>Username<input name="username" required minLength={3} maxLength={30} pattern="[a-zA-Z0-9_]+" autoComplete="username"/><small>3–30 letters, numbers, or underscores.</small></label>}<label>Email<input name="email" type="email" autoComplete="email" required maxLength={254}/></label><label>Password<input name="password" type="password" autoComplete={mode==='register'?'new-password':'current-password'} required minLength={mode==='register'?12:1} maxLength={128}/>{mode==='register'&&<small>At least 12 characters.</small>}</label><p role="alert">{error}</p><p role="status">{message}</p><button className="primary" disabled={busy}>{busy?'Please wait…':mode==='register'?'Create account':'Sign in'}</button></form></>;
}
