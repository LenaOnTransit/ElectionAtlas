'use client';
import { useState } from 'react';
import type { User } from '../../lib/auth-core.mjs';
export default function Account({user,returnTo}:{user:User|null;returnTo:string}) {
  const [mode,setMode]=useState<'login'|'register'>('login');
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  async function submit(event:React.FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setError('');
    const values=Object.fromEntries(new FormData(event.currentTarget));
    try {const response=await fetch('/api/auth/'+mode,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});const data=await response.json();if(!response.ok)throw Error(data.error);window.location.assign(returnTo);}catch(e){setError(e instanceof Error?e.message:'Please retry.');setBusy(false);}
  }
  async function logout() {setBusy(true);try{const response=await fetch('/api/auth/logout',{method:'POST'});if(!response.ok)throw Error('Could not sign out.');window.location.assign('/account');}catch(e){setError(e instanceof Error?e.message:'Please retry.');setBusy(false);}}
  if(user)return <><p>Signed in as <b>{user.displayName}</b> · {user.email}</p><p>{user.role==='admin'?'You have access to the private newsroom.':'Your reader account is ready. Browse all public coverage and election tools.'}</p>{user.role==='admin'&&<p><a className="primary" href="/editor">Open private newsroom</a></p>}<button disabled={busy} onClick={logout}>Sign out</button><p role="alert">{error}</p></>;
  return <><p>Read without an account, or create your own. New accounts have reader access.</p><div className="tabs"><button onClick={()=>{setMode('login');setError('')}} className={mode==='login'?'active':''}>Sign in</button><button onClick={()=>{setMode('register');setError('')}} className={mode==='register'?'active':''}>Create account</button></div><form onSubmit={submit}>{mode==='register'&&<label>Username<input name="username" required minLength={3} maxLength={30} pattern="[a-zA-Z0-9_]+" autoComplete="username"/><small>3–30 letters, numbers, or underscores.</small></label>}<label>Email<input name="email" type="email" autoComplete="email" required maxLength={254}/></label><label>Password<input name="password" type="password" autoComplete={mode==='register'?'new-password':'current-password'} required minLength={mode==='register'?12:1} maxLength={128}/>{mode==='register'&&<small>At least 12 characters.</small>}</label><p role="alert">{error}</p><button className="primary" disabled={busy}>{busy?'Please wait…':mode==='register'?'Create account':'Sign in'}</button></form></>;
}
