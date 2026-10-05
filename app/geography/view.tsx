import {useId,useMemo,useState} from 'react';
import {AppLink} from '../../src/navigation';
import {WorldNav} from '../world/shared';
import {MapPaletteControl,useMapPalette,accessibleColour,MapPatternDefs,MapSwatch} from '../appearance';
import {geographyView,rankedResults,winningMargin,populationRadius,mixWhite,type GeographyDataset,type ViewUnit} from '../../lib/election-geography.mjs';
const signed=(n:number)=>`${n>0?'+':''}${n.toFixed(2)}`;
const number=(n:number)=>n.toLocaleString('en-GB');
const share=(votes:number,valid:number)=>valid?100*votes/valid:0;

export default function ElectionGeography({data,initialElectionId,initialView={}}:{data:GeographyDataset;initialElectionId?:string;initialView?:{comparison?:boolean;layer?:'winner'|'margin'|'shift';layout?:'geographic'|'population';unitId?:string}}){
 const [electionId,setElectionId]=useState(initialElectionId||data.defaultElectionId);
 const [palette,setPalette]=useMapPalette();
 const [layer,setLayer]=useState(initialView.layer||'winner');
 const [layout,setLayout]=useState(initialView.layout||'geographic');
 const [query,setQuery]=useState('');
 const [selected,setSelected]=useState(initialView.unitId||data.defaultUnitId||'');
 const [zoom,setZoom]=useState(1),[pan,setPan]=useState([0,0]);
 const [arrowScale,setArrowScale]=useState(1),[threshold,setThreshold]=useState(0),[bubbleSize,setBubbleSize]=useState(24);
 const [comparisonRequested,setComparison]=useState(initialView.comparison||false);
 const markerId=useId().replace(/[^a-zA-Z0-9_-]/g,'');
 const view=useMemo(()=>geographyView(data,electionId),[data,electionId]);
 const {election,previous,boundaries,units,maxPopulation,maxShift}=view;
 const comparison=comparisonRequested&&!!previous;
 const shiftLayer=layer==='shift'&&comparison&&view.hasClassifications;
 const effectiveLayer=layer==='shift'&&!shiftLayer?'winner':layer;
 const effectiveLayout=layout==='population'&&maxPopulation>0?'population':'geographic';
 const active=units.find(u=>u.id===selected)||units[0];
 const matches=units.filter(u=>u.name.toLowerCase().includes(query.toLowerCase()));
 const matchingIds=new Set(matches.map(u=>u.id));
 const currentParties=new Map(election.parties.map(p=>[p.id,p]));
 const allParties=[...election.parties,...(previous?.parties.filter(p=>!currentParties.has(p.id))||[])];
 const parties=new Map(allParties.map(p=>[p.id,p]));
 const partyIndex=(id:string)=>allParties.findIndex(p=>p.id===id);
 const partyName=(id:string)=>parties.get(id)?.name||id;
 const partyColor=(id:string)=>palette==='accessible'?accessibleColour(partyIndex(id)):parties.get(id)?.color||'#888888';
 const partySwatch=(id:string)=><MapSwatch index={partyIndex(id)} original={parties.get(id)?.color||'#888888'} palette={palette} patterns={effectiveLayer==='winner'}/>;
 function color(u:ViewUnit){const rows=rankedResults(u.result);if(!rows.length||rows[0].votes===rows[1]?.votes)return '#888888';const winner=partyColor(rows[0].party);return effectiveLayer==='margin'?mixWhite(winner,.22+.78*Math.min(1,winningMargin(u.result)/30)):winner;}
 function mapFill(u:ViewUnit){const r=rankedResults(u.result);return palette==='accessible'&&effectiveLayer==='winner'&&r.length&&r[0].votes!==r[1]?.votes?`url(#${markerId}-party-${partyIndex(r[0].party)})`:color(u);}
 function label(u:ViewUnit){const r=rankedResults(u.result);return `${u.name}: ${r.length?`${partyName(r[0].party)}, ${r[0].share.toFixed(2)}%; lead ${winningMargin(u.result).toFixed(2)} percentage points`:'Results not available'}${u.population!=null?`; population ${number(u.population)}`:''}${shiftLayer?(u.shift?`; ${Math.abs(u.shift.change).toFixed(2)} points toward the ${u.shift.change>=0?'left':'right'}`:'; comparison not available'):''}`;}
 function selectUnit(id:string){setSelected(id);}
 const keys=(id:string)=>(event:React.KeyboardEvent<SVGElement>)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectUnit(id);}};
 function resetView(){setZoom(1);setPan([0,0]);}
 const w=boundaries.width/zoom,h=boundaries.height/zoom,vx=(boundaries.width-w)/2+pan[0],vy=(boundaries.height-h)/2+pan[1];
 const rows=rankedResults(active?.result),shift=active?.shift;
 const resultsAvailable=!!rows.length,comparisonAvailable=!!active?.result?.valid&&!!active?.previousResult?.valid;
 const shownElections=comparison&&previous?[previous,election]:[election];
 const outside=data.units.filter(u=>!boundaries.features[u.id]&&shownElections.some(e=>e.results[u.id]));
 const winners=[...new Set(units.flatMap(u=>{const r=rankedResults(u.result);return !r.length||r[0].votes===r[1]?.votes?[]:[r[0].party];}))];
 if(!active)return <main className="world-main"><h1>{data.title}</h1><p>No mapped areas are available for this election.</p></main>;
 return <main className="world-main municipal-comparison"><WorldNav/>
  <div className="kicker">{data.unitLabel} map · {election.country}</div><h1>{election.name} · {comparison&&previous?`${previous.label} → ${election.label}`:election.label}</h1><p className="standfirst">{data.description}</p>
  <div className="municipal-controls">
   <label>Election<select value={election.id} onChange={e=>{setElectionId(e.target.value);setComparison(false);setLayer('winner');resetView();}}>{data.elections.map(e=><option key={e.id} value={e.id}>{e.dateLabel||e.label} · {e.name}</option>)}</select></label>
   {previous&&<label>View<select value={comparison?'comparison':'results'} onChange={e=>{setComparison(e.target.value==='comparison');if(e.target.value!=='comparison')setLayer('winner');}}><option value="results">Election results</option><option value="comparison">Compare with {previous.label}</option></select></label>}
   <label>Map layer<select value={effectiveLayer} onChange={e=>setLayer(e.target.value as typeof layer)}><option value="winner">Winning party</option><option value="margin">Winning margin</option>{comparison&&view.hasClassifications&&<option value="shift">Left–right shift since {previous?.label}</option>}</select></label>
   <label>Area sizing<select value={effectiveLayout} onChange={e=>setLayout(e.target.value as typeof layout)}><option value="geographic">Geographic boundaries</option>{maxPopulation>0&&<option value="population">Population-sized circles</option>}</select></label>
   <label>Find a {data.unitLabel}<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by area name…"/></label>
   <label>Select {data.unitLabel}<select value={active.id} onChange={e=>selectUnit(e.target.value)}>{matches.map(u=><option key={u.id} value={u.id}>{u.name}</option>)}{!matchingIds.has(active.id)&&<option value={active.id}>{active.name} (selected)</option>}</select></label>
  </div>
  <p className="meta" role="status">{query?`${matches.length} matching ${data.unitPlural}. `:''}{palette==='accessible'&&effectiveLayer==='winner'?'Colours and patterns match the party key. ':''}{effectiveLayer==='margin'?'Colour identifies the largest party; deeper colour means a wider lead. The lead is the difference in vote share between the first and second parties.':shiftLayer?`Arrows show the change in vote-share balance. ${view.leftShifted} areas shifted left; ${view.rightShifted} shifted right. ${view.comparedUnits} of ${units.length} areas have comparable results.`:'Colour identifies the party with the most votes, which need not have a majority.'} Grey means a tie or results not available. {effectiveLayout==='population'?`Circle area is proportional to population${data.populationLabel?' on '+data.populationLabel:''}; centres remain at their geographic locations and circles may overlap. Areas without population figures retain their boundaries.`:''}</p>
  {effectiveLayer==='margin'&&<div className="municipal-margin-key"><span>Smaller lead</span><i/><span>30+ percentage points</span></div>}
  <MapPaletteControl value={palette} onChange={setPalette}/>
  <div className="municipal-map-layout"><section className="municipal-map-panel" aria-label="Election geography map">
   <div className="municipal-map-tools"><button onClick={()=>setZoom(z=>Math.min(8,z*1.4))} aria-label="Zoom in">+</button><button onClick={()=>setZoom(z=>Math.max(1,z/1.4))} aria-label="Zoom out">−</button><button onClick={resetView}>Reset view</button>{zoom>1&&<><button onClick={()=>setPan(p=>[p[0]-w/4,p[1]])} aria-label="Pan west">←</button><button onClick={()=>setPan(p=>[p[0]+w/4,p[1]])} aria-label="Pan east">→</button><button onClick={()=>setPan(p=>[p[0],p[1]-h/4])} aria-label="Pan north">↑</button><button onClick={()=>setPan(p=>[p[0],p[1]+h/4])} aria-label="Pan south">↓</button></>}</div>
   {shiftLayer&&<div className="municipal-sliders"><label>Arrow size<input type="range" min=".4" max="2" step=".1" value={arrowScale} onChange={e=>setArrowScale(+e.target.value)}/></label><label>Hide shifts below {threshold.toFixed(1)} pp<input type="range" min="0" max="10" step=".5" value={threshold} onChange={e=>setThreshold(+e.target.value)}/></label><span>← Left · Right → · {maxShift.toFixed(2)} pp = longest arrow</span></div>}
   {effectiveLayout==='population'&&<label className="municipal-bubble-control">Circle size<input type="range" min="10" max="45" value={bubbleSize} onChange={e=>setBubbleSize(+e.target.value)}/></label>}
   <svg className="municipal-map" viewBox={`${vx} ${vy} ${w} ${h}`} role="group" aria-label={`${election.label} ${election.country} ${data.unitPlural} results, ${effectiveLayer} layer`}><MapPatternDefs prefix={markerId+'-party'} count={allParties.length}/><defs>{(['left','right'] as const).map(side=><marker key={side} id={markerId+'-'+side} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill={side==='left'?'#922c38':'#174c87'}/></marker>)}</defs>
    {units.map(u=><path key={u.id} d={u.path} fill={effectiveLayout==='population'&&u.population?'#e8e5df':mapFill(u)} fillOpacity={matchingIds.has(u.id)?shiftLayer ? .42 : 1:.14} stroke={u.id===active.id?'#141414':'#ffffff'} strokeWidth={u.id===active.id?1.8:.55} fillRule="evenodd" role="button" tabIndex={effectiveLayout==='geographic'||!u.population?0:-1} aria-label={label(u)} aria-pressed={u.id===active.id} onClick={()=>selectUnit(u.id)} onKeyDown={keys(u.id)}><title>{label(u)}</title></path>)}
    {effectiveLayout==='population'&&[...units].filter(u=>u.population&&u.population>0).sort((a,b)=>(b.population||0)-(a.population||0)).map(u=><circle key={u.id} cx={u.center[0]} cy={u.center[1]} r={populationRadius(u.population||0,maxPopulation,bubbleSize)} fill={mapFill(u)} fillOpacity={matchingIds.has(u.id)?shiftLayer ? .5 : .85:.15} stroke={u.id===active.id?'#141414':'#ffffff'} strokeWidth={u.id===active.id?1.8:.7} role="button" tabIndex={0} aria-label={label(u)} aria-pressed={u.id===active.id} onClick={()=>selectUnit(u.id)} onKeyDown={keys(u.id)}><title>{label(u)}</title></circle>)}
    {shiftLayer&&units.filter(u=>matchingIds.has(u.id)&&u.shift).map(u=>{const change=u.shift!.change;if(Math.abs(change)<Math.max(.005,threshold))return null;const length=Math.abs(change)/maxShift*35*arrowScale,dir=change>0?-1:1,[x,y]=u.center;return <line key={u.id} x1={x-dir*length/2} y1={y} x2={x+dir*length/2} y2={y} stroke={change>0?'#922c38':'#174c87'} strokeWidth={u.id===active.id?2.6:1.5} markerEnd={`url(#${markerId}-${change>0?'left':'right'})`} pointerEvents="none"><title>{`${u.name}: ${Math.abs(change).toFixed(2)} pp ${change>0?'left':'right'}`}</title></line>;})}
   </svg><p className="meta">Boundaries: {boundaries.label}. Each area retains its geographic location. Use zoom, search or the selector for small areas.</p>
   <div className="municipal-party-key">{winners.map(id=><span key={id}>{partySwatch(id)}{partyName(id)}</span>)}<span><i style={{background:'#888888'}}/>Tie / results not available</span></div>
  </section>
  <aside className="municipal-detail" aria-live="polite"><div className="kicker">Selected {data.unitLabel} · {active.id}</div><h2>{active.name}</h2>{active.population!=null&&<p>{number(active.population)} residents{data.populationLabel?' · '+data.populationLabel:''}</p>}
   {resultsAvailable?<div className="municipal-winner" style={{borderColor:color(active)}}><b>{rows[0].votes===rows[1]?.votes?'Joint first place':partyName(rows[0].party)}</b><span>{rows[0].share.toFixed(2)}% · lead {winningMargin(active.result).toFixed(2)} pp</span><small>{election.label} turnout: {active.result?.turnout==null?'Not recorded':active.result.turnout.toFixed(2)+'%'}</small></div>:<p>Results are not available for this area.</p>}
   {active.result?.turnout!=null&&active.result.turnout>100&&data.turnoutNote&&<p className="meta">{data.turnoutNote}</p>}
   {comparison&&view.hasClassifications&&(shift?<><h3>{previous?.label} → {election.label} vote balance</h3><p className="municipal-shift-value" style={{color:shift.change>0?'#922c38':shift.change<0?'#174c87':undefined}}>{Math.abs(shift.change)<.005?'No net shift':`${Math.abs(shift.change).toFixed(2)} pp ${shift.change>0?'← left':'right →'}`}</p><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Bloc</th><th>{previous?.label}</th><th>{election.label}</th><th>Change</th></tr></thead><tbody>{(['left','right','centre','unclassified'] as const).map(b=><tr key={b}><th>{b[0].toUpperCase()+b.slice(1)}</th><td>{shift.before[b].toFixed(2)}%</td><td>{shift.after[b].toFixed(2)}%</td><td>{signed(shift.after[b]-shift.before[b])} pp</td></tr>)}</tbody></table></div><p className="meta">Shift = (left share − right share) in {election.label} minus the same balance in {previous?.label}. Centre and unclassified votes remain in the denominator and contribute to neither bloc. Aggregate changes do not identify individual voter movements.</p></>:<p>Vote-balance comparison is not available for this area.</p>)}
   <h3>{election.label} area results{comparison?' compared with '+previous?.label:''}</h3>
   {comparison&&!comparisonAvailable&&<p>Comparable results are not available for both elections in this area. Missing results are shown as unavailable.</p>}
   <div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Party</th>{comparison?<><th>{previous?.label}</th><th>{election.label}</th><th>Change</th></>:<><th>Votes</th><th>Vote share</th></>}</tr></thead><tbody>{allParties.filter(p=>active.result?.votes[p.id]!=null||comparison&&active.previousResult?.votes[p.id]!=null).sort((a,b)=>(active.result?.votes[b.id]||0)-(active.result?.votes[a.id]||0)).map(p=>{const a=active.previousResult?.votes[p.id]||0,b=active.result?.votes[p.id]||0,as=share(a,active.previousResult?.valid||0),bs=share(b,active.result?.valid||0);return <tr key={p.id}><th>{partySwatch(p.id)}{p.name}</th>{comparison?<><td>{active.previousResult?.valid?<>{as.toFixed(2)}%<small>{number(a)} votes</small></>:'Not available'}</td><td>{active.result?.valid?<>{bs.toFixed(2)}%<small>{number(b)} votes</small></>:'Not available'}</td><td>{comparisonAvailable?signed(bs-as)+' pp':'Not available'}</td></>:<><td>{number(b)}</td><td>{active.result?.valid?bs.toFixed(2)+'%':'Not available'}</td></>}</tr>;})}</tbody></table></div>
   <p className="meta">Valid votes: {shownElections.map(e=>`${e.results[active.id]?number(e.results[active.id].valid):'Not available'} (${e.label})`).join(' · ')}.{comparisonAvailable&&comparison?' An absent party in a recorded result is treated as zero votes for comparison.':''}</p>
   <p>{shownElections.filter(e=>e.results[active.id]?.source).map((e,i)=><span key={e.id}>{i>0&&' · '}<a href={e.results[active.id].source} target="_blank" rel="noreferrer">Official {e.label} area result</a></span>)}</p>
  </aside></div>
  {comparison&&view.hasClassifications&&<section className="municipal-classifications"><h2>Our left–right classifications</h2><p>{data.classificationNote} Centre and unclassified parties contribute to neither bloc.</p><details><summary>View party classifications</summary>{shownElections.map(e=><div key={e.id}><h3>{e.label}</h3><div className="municipal-classification-grid">{e.parties.map(p=><div key={p.id}>{partySwatch(p.id)}{p.name} · {p.classification||'unclassified'}</div>)}</div></div>)}</details></section>}
  <section><h2>Coverage and sources</h2><p>{data.coverageNote}</p>{[...data.notes,...(comparison?data.comparisonNotes||[]:[])].map((n,i)=><p key={i} className="meta">{n}</p>)}{data.outsideMapNote&&<p>{data.outsideMapNote}</p>}
   {!!outside.length&&<details><summary>Results outside the map</summary><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Area</th>{shownElections.map(e=><th key={e.id}>{e.label} largest party</th>)}</tr></thead><tbody>{outside.map(u=><tr key={u.id}><th>{u.name}</th>{shownElections.map(e=>{const result=e.results[u.id],r=rankedResults(result);return <td key={e.id}>{r.length?<>{r[0].votes===r[1]?.votes?'Joint first place':partyName(r[0].party)} · {r[0].share.toFixed(2)}%<br/>{number(result.valid)} valid votes{result.source&&<> · <a href={result.source} target="_blank" rel="noreferrer">Full official result</a></>}</>:'Not available'}</td>;})}</tr>)}</tbody></table></div></details>}
   {data.sources.map(s=><p key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.label}</a></p>)}<p className="meta">Reviewed {data.checked}. {data.elections.filter(e=>e.nationalRoute).map(e=><span key={e.id}> <AppLink action href={e.nationalRoute!}>National {e.label} result</AppLink></span>)}</p>
  </section>
 </main>;
}
