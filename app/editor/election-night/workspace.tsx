import {useCallback,useState} from 'react';
import {useModerator} from '../../../src/moderation';
import {AppLink} from '../../../src/navigation';
import type {Senate} from '../../../lib/senate';
import {emptyHouse,type HouseOverview} from '../../../lib/house';
import {addSimulatedHouseCall,setSimulatedSenateCall} from '../../../lib/election-night';
import NightIntro from '../../explore/night-intro';
import PollCountdown from '../../explore/poll-countdown';
import USNightBoard from '../../explore/us-night';
type Snapshot={senate:Senate;house:HouseOverview};
export default function TestRoom({initialSenate,initialHouse}:{initialSenate:Senate;initialHouse:HouseOverview|null}){
 const moderator=useModerator();
 const original=()=>({senate:structuredClone(initialSenate),house:structuredClone(initialHouse??emptyHouse())});
 const [draft,setDraft]=useState<Snapshot>(original),[history,setHistory]=useState<Snapshot[]>([]),[selected,setSelected]=useState('GA'),[intro,setIntro]=useState(false);const dismissIntro=useCallback(()=>setIntro(false),[]);
 if(!moderator)return <main><h1>Moderator access required</h1><p>Verifying editorial access. Sign in with a moderator account to use the test room.</p></main>;
 function change(next:Snapshot){setHistory(h=>[...h.slice(-39),draft]);setDraft(next);}
 function callNext(party:'D'|'R'){
  const r=draft.senate.races.find(r=>!r.results.called&&r.candidates.some(c=>c.party===party));if(!r)return;
  change({...draft,senate:setSimulatedSenateCall(draft.senate,r.id,r.candidates.find(c=>c.party===party)!.id)});setSelected(r.code);
 }
 function reset(){const next=original();next.senate.races.forEach(r=>{r.results.called='';r.results.reporting=0});next.house.results={...next.house.results,D:0,R:0,O:0,called:'',status:'provisional'};next.house.races=next.house.races.map(r=>({...r,call:''}));return next;}
 function scenario(senateParty:'D'|'R',houseParty:'D'|'R'){
  const next=reset();for(const r of next.senate.races){const c=r.candidates.find(c=>c.party===senateParty);if(c)r.results.called=c.id;}
  next.house.results={...next.house.results,D:houseParty==='D'?218:217,R:houseParty==='R'?218:217,O:0,called:houseParty};change(next);
 }
 const race=draft.senate.races.find(r=>r.code===selected),full=draft.house.results.D+draft.house.results.R+draft.house.results.O>=435;
 return <main className="world-main night-test-room">{intro&&<NightIntro onDone={dismissIntro}/>}<div className="formhead"><div><p className="kicker">PRIVATE NEWSROOM</p><h1>Election night test room</h1></div><AppLink action href="/editor">Back to newsroom</AppLink></div><p className="night-test-warning"><b>Simulation only.</b> Changes stay in this tab’s memory. They cannot update public results, save to the database, or publish. Reloading discards the test.</p>
 <section className="night-test-controls" aria-label="Simulation controls"><h2>Test chamber control</h2><div className="night-test-buttons"><button onClick={()=>change(reset())}>Starting tally / clear calls</button><button onClick={()=>scenario('D','D')}>Both blue</button><button onClick={()=>scenario('D','R')}>Blue Senate / red House</button><button onClick={()=>scenario('R','D')}>Red Senate / blue House</button><button onClick={()=>scenario('R','R')}>Both red</button><button onClick={()=>change(original())}>Restore loaded public snapshot</button><button disabled={!history.length} onClick={()=>{setDraft(history[history.length-1]);setHistory(h=>h.slice(0,-1))}}>Undo last change</button></div>
 <div className="night-test-grid"><fieldset><legend>Senate calls</legend><p>Call a seat and watch the starting tally grow.</p><div className="night-test-buttons"><button onClick={()=>callNext('D')} disabled={!draft.senate.races.some(r=>!r.results.called&&r.candidates.some(c=>c.party==='D'))}>Call next Senate seat for D</button><button onClick={()=>callNext('R')} disabled={!draft.senate.races.some(r=>!r.results.called&&r.candidates.some(c=>c.party==='R'))}>Call next Senate seat for R</button></div>{race?<><label>{race.state} winner<select value={race.results.called} onChange={e=>change({...draft,senate:setSimulatedSenateCall(draft.senate,race.id,e.target.value)})}><option value="">Uncalled</option>{race.candidates.map(c=><option key={c.id} value={c.id}>{c.name||c.party+' candidate'} ({c.party})</option>)}</select></label><label>Reporting %<input type="number" min="0" max="100" value={race.results.reporting} onChange={e=>{const n=Number(e.target.value);if(!Number.isFinite(n)||n<0||n>100)return;change({...draft,senate:{...draft.senate,races:draft.senate.races.map(r=>r.id===race.id?{...r,results:{...r.results,reporting:n}}:r)}})}}/></label></>:<p>Select a state with a Senate race to change its call.</p>}<label>Senate tie-breaker<select value={draft.senate.tieBreaker} onChange={e=>change({...draft,senate:{...draft.senate,tieBreaker:e.target.value as 'D'|'R'|'I'}})}><option value="D">Democratic</option><option value="R">Republican</option><option value="I">Neither caucus</option></select></label></fieldset>
 <fieldset><legend>House calls</legend><p>Add a clearly labelled test district in the selected state. Each call adds exactly one national seat.</p><div className="night-test-buttons"><button disabled={full} onClick={()=>change({...draft,house:addSimulatedHouseCall(draft.house,'D',selected)})}>Call test House district for D</button><button disabled={full} onClick={()=>change({...draft,house:addSimulatedHouseCall(draft.house,'R',selected)})}>Call test House district for R</button></div>{(['D','R','O'] as const).map(p=><label key={p}>{p==='D'?'Democratic':p==='R'?'Republican':'Other'} House seats<input type="number" min="0" max="435" step="1" value={draft.house.results[p]} onChange={e=>{const n=Number(e.target.value),other=(['D','R','O'] as const).filter(x=>x!==p).reduce((s,x)=>s+draft.house.results[x],0);if(!Number.isInteger(n)||n<0||n+other>435)return;change({...draft,house:{...draft.house,results:{...draft.house.results,[p]:n,called:'',status:'provisional'}}})}}/></label>)}</fieldset></div></section>
 <PollCountdown/><USNightBoard tools={<button onClick={()=>setIntro(true)}>Preview intro</button>} senate={draft.senate} house={draft.house} selected={selected} onSelect={setSelected}/></main>;
}
