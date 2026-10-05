import {MapPaletteControl,useMapPalette,accessibleColour,MapPatternDefs,MapSwatch} from './appearance';
import {useEffect, useId, useState} from 'react';
import {AppLink, navigate} from '../src/navigation';
import type {WorldElection} from '../lib/world';
import outlines from '../lib/us-states-map.json';

type ElectoralState = {code:string;name:string;electors:number;votes:Record<string,number>;unallocated:number};
type ElectoralMap = {year:number;electors:number;majority:number;ballotsPerElector:number;states:ElectoralState[];candidates:{id:string;name:string;party:string;color:string}[];note:string;source:string};
const callouts=['VT','NH','MA','RI','CT','NJ','DE','MD'];
const years = [1789,...Array.from({length:59},(_,i)=>1792+i*4)];
export function PresidentialElectoralMap({election,elections}:{election:WorldElection;elections:WorldElection[]}){
 const [palette,setPalette]=useMapPalette();
 const [maps,setMaps]=useState<Record<string,ElectoralMap>|null>(null);
 const [error,setError]=useState(false);
 const [selected,setSelected]=useState('PA');
 const pattern=useId().replace(/[^a-zA-Z0-9_-]/g,'');
 const supported=election.countryId==='us'&&election.type==='presidential'&&years.some(y=>election.id===`world-us-president-${y}`);
 useEffect(()=>{
  if(!supported)return;
  const controller=new AbortController();
  fetch(import.meta.env.BASE_URL+'us-presidential-electoral.json?v=20261005',{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(setMaps).catch(()=>{if(!controller.signal.aborted)setError(true);});
  return()=>controller.abort();
 },[supported]);
 if(!supported)return null;
 const data=maps?.[election.id];
 if(!data)return <section className="presidential-electoral"><h2>Electoral map</h2><p role="status">{error?'The electoral map could not load. The recorded results remain available below.':'Loading the historical electoral map…'}</p></section>;
 const candidates=new Map(data.candidates.map((c,index)=>[c.id,{...c,color:palette==='accessible'?accessibleColour(index):election.results.find(r=>r.id===c.id)?.color||c.color}]));
 const candidateIndex=(id:string)=>data.candidates.findIndex(c=>c.id===id);
 const candidateFill=(id:string)=>palette==='accessible'&&candidateIndex(id)>=0?`url(#${pattern}-party-${candidateIndex(id)})`:candidates.get(id)?.color||'#8054a0';
 const active=data.states.find(s=>s.code===selected)||data.states[0];
 const recipients=(s:ElectoralState)=>Object.entries(s.votes).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
 const description=(s:ElectoralState)=>`${s.name}: ${s.electors} electors; ${recipients(s).map(([id,n])=>`${candidates.get(id)?.name||id} ${n} electoral votes`).join('; ')||'no counted electoral votes'}${s.unallocated?`; ${s.unallocated} uncast or rejected votes`:''}`;
 const choose=(code:string)=>setSelected(code);
 const onKey=(event:React.KeyboardEvent,code:string)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose(code);}};
 const dc=data.states.find(s=>s.code==='DC');
 const available=elections.filter(e=>e.countryId==='us'&&e.type==='presidential'&&maps?.[e.id]).sort((a,b)=>b.startDate.localeCompare(a.startDate));
 return <section className="presidential-electoral"><div className="presidential-map-heading"><h2>Electoral map · {data.year===1789?'1788–89':data.year}</h2><label>Presidential election<select value={election.id} onChange={e=>navigate('/world/election/'+e.target.value)}>{available.map(e=><option key={e.id} value={e.id}>{e.id.endsWith('-1789')?'1788–89':e.startDate.slice(0,4)} · {e.results.find(r=>r.winner)?.name||'Results'}</option>)}</select></label></div>
 <p><b>{data.electors} electors · {data.majority} votes needed for an electoral majority</b>{data.ballotsPerElector===2?' · Each elector cast two undifferentiated votes.':''}</p>
 {data.note&&<p className="world-coverage">{data.note}</p>}
 <p className="meta">Colour shows the leading electoral-vote recipient in each state. Stripes mark multiple recipients or uncast / rejected votes; select a state for the exact allocation. This shows counted electoral votes, which can differ from the popular-vote winner.</p>
 <MapPaletteControl value={palette} onChange={setPalette}/><div className="presidential-map-layout"><div><svg className="presidential-map" viewBox="0 0 1110 630" role="group" aria-label={`${data.year} United States presidential electoral map; select a state`}><MapPatternDefs prefix={pattern+'-party'} count={data.candidates.length}/><defs><pattern id={pattern} width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><rect width="3" height="9" fill="white" fillOpacity=".5"/></pattern></defs>
 {outlines.map(outline=>{
  const state=data.states.find(s=>s.code===outline.code);const rows=state?recipients(state):[];const leader=rows[0];const fill=leader?candidateFill(leader[0]):'#dddcd7';const split=!!state&&(rows.length>1||state.unallocated>0);const index=callouts.indexOf(outline.code);const external=index>=0;const x=external?1045:outline.x;const y=external?160+index*41:outline.y;
  return <g key={outline.code} className={'presidential-map-state'+(active.code===outline.code?' selected':'')} role={state?'button':undefined} tabIndex={state?0:undefined} aria-label={state?description(state):`${outline.name}: not participating in this electoral count; modern outline shown for reference`} aria-pressed={state?active.code===outline.code:undefined} onClick={()=>state&&choose(state.code)} onKeyDown={e=>state&&onKey(e,state.code)}><title>{state?description(state):`${outline.name}: not participating`}</title><path d={outline.path} fill={fill} fillRule="evenodd"/>{split&&<path className="presidential-split" d={outline.path} fill={`url(#${pattern})`} fillRule="evenodd"/>}{external&&<><path className="presidential-callout-line" d={`M${outline.x},${outline.y}L980,${y}L995,${y}`} fill="none"/><rect x="995" y={y-16} width="100" height="33" rx="3" fill={fill}/>{split&&<rect x="995" y={y-16} width="100" height="33" rx="3" fill={`url(#${pattern})`}/>}</>}<text x={x} y={y-3} className="presidential-state-code">{outline.code}</text>{state&&<text x={x} y={y+12} className="presidential-elector-count">{state.electors}</text>}</g>;
 })}
 {dc&&<g role="button" tabIndex={0} aria-label={description(dc)} aria-pressed={active.code==='DC'} className={'presidential-map-state'+(active.code==='DC'?' selected':'')} onClick={()=>choose('DC')} onKeyDown={e=>onKey(e,'DC')}><title>{description(dc)}</title><rect x="995" y="495" width="100" height="33" rx="3" fill={recipients(dc)[0]?candidateFill(recipients(dc)[0][0]):'#dddcd7'}/>{dc.unallocated>0&&<rect x="995" y="495" width="100" height="33" fill={`url(#${pattern})`}/>}<text x="1045" y="509" className="presidential-state-code">DC</text><text x="1045" y="524" className="presidential-elector-count">{dc.electors}</text></g>}
 <text className="map-inset-label" x="170" y="608">Alaska</text><text className="map-inset-label" x="360" y="608">Hawaii</text></svg>
 <p className="meta">Modern state outlines are used for reference, not historical borders. Gray areas did not participate or had no counted votes; they may not yet have been states. Alaska and Hawaii are insets. Numbers show electors in this election, not current allocations. <a href="https://github.com/topojson/us-atlas" target="_blank" rel="noreferrer">Boundaries: U.S. Census / US Atlas</a>.</p>
 <details className="presidential-legend"><summary>Candidate colours ({data.candidates.length})</summary><div className="municipal-party-key">{data.candidates.map(c=><span key={c.id}><MapSwatch index={candidateIndex(c.id)} original={candidates.get(c.id)?.color||c.color} palette={palette}/>{c.name} · {c.party}</span>)}</div></details></div>
 <aside className="presidential-state-detail" aria-live="polite"><label>Select state / district<select value={active.code} onChange={e=>choose(e.target.value)}>{data.states.map(s=><option key={s.code} value={s.code}>{s.name}</option>)}</select></label><h3>{active.name}</h3><p><b>{active.electors} electors</b>{data.ballotsPerElector===2?' · Two votes per elector':''}</p><table className="world-result-table"><thead><tr><th>Recipient</th><th>Electoral votes</th></tr></thead><tbody>{recipients(active).map(([id,n])=><tr key={id}><th><MapSwatch index={candidateIndex(id)} original={candidates.get(id)?.color||'#888'} palette={palette}/>{candidates.get(id)?.name||id}</th><td>{n}</td></tr>)}{active.unallocated>0&&<tr><th>Uncast / rejected</th><td>{active.unallocated}</td></tr>}</tbody></table>{!recipients(active).length&&<p>No electoral votes were counted from this state.</p>}<p><a href={data.source} target="_blank" rel="noreferrer">Official state allocations and historical notes</a></p><p><AppLink action href="/archive/country/us">All U.S. presidential elections</AppLink></p></aside></div></section>;
}
