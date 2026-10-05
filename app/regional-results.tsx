import {AppLink} from '../src/navigation';
import type {WorldElection} from '../lib/world';
import map from '../lib/netherlands-provinces.json';

export function RegionalResults({overview,elections,selectedId}:{overview:WorldElection;elections:WorldElection[];selectedId:string}){
 const children=elections.filter(e=>e.overviewId===overview.id).sort((a,b)=>(a.geography?.name||a.title).localeCompare(b.geography?.name||b.title));
 const province=overview.regionalOverview==='provincial';
 const leader=(e:WorldElection)=>[...e.results].filter(r=>r.votes!=null).sort((a,b)=>(b.votes||0)-(a.votes||0))[0];
 return <section className="regional-results"><h2>{province?'Results by province':'Results by electoral college'}</h2>
 <p>{province?'Each province elects its own chamber. The overview combines popular votes; provincial seats are shown on each province’s page.':'Each college has its own electorate and elected membership. Its members subsequently take part in the indirect Eerste Kamer election.'}</p>
 {selectedId!==overview.id&&<p><AppLink action href={'/world/election/'+overview.id}>View the full election overview</AppLink></p>}
 <div className={province?'regional-layout':'regional-layout colleges'}>
 {province&&overview.countryId==='nl'&&<div><svg className="province-map" viewBox={`0 0 ${map.width} ${map.height}`} role="group" aria-label="Netherlands provincial election results; select a province">
 {map.provinces.map(p=>{const e=children.find(e=>e.geography?.id===p.id);const first=e&&leader(e);return e?<AppLink key={p.id} href={'/world/election/'+e.id} aria-label={`${p.name}: ${first?.name||'results'}`} className={selectedId===e.id?'selected-province':''}><path d={p.path} fill={first?.color||'#cbd5e1'}><title>{p.name}{first?' · '+first.name+' '+first.share+'%':''}</title></path></AppLink>:<path key={p.id} d={p.path} fill="#e5e7eb"><title>{p.name}: no results entered</title></path>})}
 </svg><p className="meta">Color: party with most votes. <AppLink href={map.source} target="_blank" rel="noreferrer">Boundaries: CBS / PDOK (2023)</AppLink>. Province boundaries are used for navigation across all years.</p></div>}
 <div className="regional-links">{children.map(e=>{const first=leader(e);return <AppLink key={e.id} className={'regional-link'+(selectedId===e.id?' selected':'')} href={'/world/election/'+e.id} style={{borderLeftColor:first?.color||'#183e60'}} aria-current={selectedId===e.id?'page':undefined}><b>{e.geography?.name||e.title}</b><span>{first?`${first.name} · ${first.share?.toFixed(2)}%`: 'View results'}</span><small>{e.totalSeats!=null?`${e.totalSeats} seats · `:''}{e.turnout!=null?`${e.turnout.toFixed(2)}% turnout`:''}</small></AppLink>})}</div>
 </div></section>;
}
