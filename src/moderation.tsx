import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {getUser} from '../app/auth';
import {supabase} from '../lib/supabase';
import {createModeratorAccess} from '../lib/moderator-access';

const ModeratorContext=createContext(false);
export function ModeratorProvider({children}:{children:ReactNode}){
 const [allowed,setAllowed]=useState(false);
 useEffect(()=>{
  const access=createModeratorAccess(getUser,setAllowed);
  let timer:ReturnType<typeof setTimeout>|undefined;
  const refresh=()=>{access.invalidate();clearTimeout(timer);timer=setTimeout(()=>{void access.refresh();},0);};
  // Do not await other Supabase calls inside the auth event callback.
  const {data:{subscription}}=supabase.auth.onAuthStateChange((_event,session)=>{
   access.invalidate();clearTimeout(timer);if(session)refresh();
  });
  const visible=()=>{if(document.visibilityState==='visible')refresh();};
  window.addEventListener('account-changed',refresh);
  window.addEventListener('focus',refresh);
  document.addEventListener('visibilitychange',visible);
  return()=>{clearTimeout(timer);subscription.unsubscribe();access.dispose();window.removeEventListener('account-changed',refresh);window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',visible);};
 },[]);
 return <ModeratorContext.Provider value={allowed}>{children}</ModeratorContext.Provider>;
}
export function ModeratorOnly({children}:{children:ReactNode}){return useContext(ModeratorContext)?<>{children}</>:null;}
export function useModerator(){return useContext(ModeratorContext);}
