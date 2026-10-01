import type {WorldElection} from '../lib/world';
import {hemicycleLayout,parliamentGroups} from '../lib/parliament';
export function Parliament({election:e,preview=false}:{election:WorldElection;preview?:boolean}){
  const model=parliamentGroups(e);if(!model)return null;
  const {groups,entered,total,knownTotal,missing}=model;
  const dots=hemicycleLayout(total);let offset=0;
  const majority=e.majorityThreshold??(knownTotal?Math.floor(total/2)+1:null);
  const summary=groups.map(g=>`${g.name}: ${g.seats} seats`).join('; ');
  return <section className="parliament-panel"><div className="parliament-heading"><div><div className="kicker">{preview?'EDITOR PREVIEW':'PARLIAMENT COMPOSITION'}</div><h2>{preview?'Parliament preview':'The new parliament'}</h2></div>{majority!=null&&<span className="parliament-majority">{majority} seats for a majority</span>}</div><svg className="parliament-chart" viewBox="0 0 600 330" role="img" aria-label={`Parliament seat diagram. ${summary}`}><title>{summary}</title>{groups.map(g=>{const seats=dots.slice(offset,offset+g.seats);offset+=g.seats;return <g key={g.id} fill={g.color}><title>{g.name}: {g.seats} seats</title>{seats.map((d,i)=><circle key={i} cx={d.x} cy={d.y} r={d.radius}/>)}</g>;})}<text x="300" y="239" textAnchor="middle" className="parliament-total">{total.toLocaleString()}</text><text x="300" y="263" textAnchor="middle" className="parliament-total-label">{knownTotal?'CHAMBER SEATS':'SEATS ENTERED'}</text></svg><div className="parliament-legend">{groups.map(g=><div key={g.id}><i style={{background:g.color}}/><span>{g.name}</span><b>{g.seats.toLocaleString()}</b></div>)}</div><p className="meta">One dot per seat. Parties follow the result-table order. {knownTotal?`${entered.toLocaleString()} of ${total.toLocaleString()} seats entered.`:'Chamber total has not been entered.'}{missing?' Some parties have no seat count yet.':''} {e.resultStatus==='provisional'?'Results are provisional.':''}</p></section>;
}
