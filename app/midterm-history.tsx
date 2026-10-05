import type {WorldElection} from '../lib/world';
import {AppLink,navigate} from '../src/navigation';
export function MidtermHistory({election,elections}:{election:WorldElection;elections:WorldElection[]}){
 if(election.countryId!=='us'||!/^us-(house|senate|governor)-midterms$/.test(election.seriesId))return null;
 const history=elections.filter(e=>e.countryId==='us'&&e.seriesId===election.seriesId&&e.status==='held').sort((a,b)=>a.startDate.localeCompare(b.startDate));const index=history.findIndex(e=>e.id===election.id);
 return <nav className="midterm-history" aria-label="Historical midterm cycles"><label>Election cycle<select value={election.id} onChange={ev=>navigate('/world/election/'+ev.target.value)}>{history.map(e=><option key={e.id} value={e.id}>{e.startDate.slice(0,4)} · {e.body}</option>)}</select></label><div>{history[index-1]&&<AppLink href={'/world/election/'+history[index-1].id}>← {history[index-1].startDate.slice(0,4)}</AppLink>}{history[index+1]&&<AppLink href={'/world/election/'+history[index+1].id}>{history[index+1].startDate.slice(0,4)} →</AppLink>}</div></nav>;
}
