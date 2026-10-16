import {useCallback,useEffect,useRef,useState} from 'react';
import {getSenate} from '../../db/senate';
import {getWorldElection} from '../../db/world';
import type {Senate} from '../../lib/senate';
import type {HouseOverview} from '../../lib/house';
import {ModeratorOnly} from '../../src/moderation';
import {AppLink} from '../../src/navigation';
import USNightBoard from './us-night';
import NightIntro from './night-intro';
import PollCountdown from './poll-countdown';
import './night-desk.css';
export default function NightDesk(){
 const [data,setData]=useState<{senate:Senate;house:HouseOverview|null}|null>(null),[intro,setIntro]=useState(true),[auto,setAuto]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState(false),[last,setLast]=useState('');const active=useRef(true),main=useRef<HTMLElement>(null);
 const dismissIntro=useCallback(()=>{setIntro(false);requestAnimationFrame(()=>main.current?.focus())},[]);
 const refresh=useCallback(async()=>{setBusy(true);try{const [senate,election]=await Promise.all([getSenate(),getWorldElection('world-us-house-2026')]);if(active.current){setData({senate,house:election?.house??null});setError('');setLast(new Date().toLocaleTimeString());}}catch{if(active.current)setError('Updates unavailable. Last loaded figures remain on screen.')}finally{if(active.current)setBusy(false)}},[]);
 useEffect(()=>{active.current=true;document.body.dataset.electionNightDesk='true';void refresh();return()=>{active.current=false;delete document.body.dataset.electionNightDesk}},[refresh]);
 useEffect(()=>{if(!auto)return;const timer=setInterval(()=>void refresh(),30000);return()=>clearInterval(timer)},[auto,refresh]);
 return <>{intro&&<NightIntro onDone={dismissIntro}/>}<main ref={main} tabIndex={-1} className="election-night-desk" inert={intro?true:undefined} aria-label="Election Night Desk"><div className="desk-topline"><div><AppLink href="/" className="desk-wordmark">World of Elections</AppLink><h1>Election Night Desk</h1><span className="desk-live-tag">2026 MIDTERMS</span></div><PollCountdown/></div>
 {data?<USNightBoard senate={data.senate} house={data.house} heading={false} tools={<><button onClick={()=>setIntro(true)}>Replay intro</button><ModeratorOnly><AppLink href="/editor/election-night">Test room</AppLink></ModeratorOnly></>}/>:<section className="desk-loading-data" aria-live="polite"><h2>Opening the desk</h2><p>{error||'Loading the latest published calls…'}</p>{error&&<button onClick={()=>void refresh()}>Try again</button>}</section>}
 <div className="desk-update-strip"><div><button disabled={busy} onClick={()=>void refresh()}>{busy?'Refreshing…':'Refresh results'}</button><button role="switch" aria-checked={auto} onClick={()=>setAuto(!auto)}>Auto-refresh {auto?'on':'off'}</button><span role="status">{error||(last?'Updated '+last:'Updates every 30 seconds')}</span></div><ModeratorOnly><div><AppLink href="/editor/senate">Senate editor</AppLink> · <AppLink href="/editor/house">House editor</AppLink></div></ModeratorOnly></div></main></>;
}
