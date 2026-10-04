import type {WorldData,WorldElection} from '../../../lib/world';

export function ElectionBrowser({data,selectedId,query,setQuery,countryId,setCountryId,choose}:{
 data:WorldData;selectedId:string;query:string;setQuery:(value:string)=>void;
 countryId:string;setCountryId:(value:string)=>void;choose:(election:WorldElection)=>void;
}) {
 const normalize=(value:string)=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const terms=normalize(query).trim().split(/\s+/).filter(Boolean);
 const countries=[...data.countries].sort((a,b)=>a.name.localeCompare(b.name));
 const groups=countries.map(country=>({country,elections:data.elections.filter(e=>{
  if(countryId&&country.id!==countryId||e.countryId!==country.id)return false;
  const text=normalize([country.name,country.aliases,country.id,e.title,e.startDate,e.round,e.type,e.status,e.publication].join(' '));
  return terms.every(term=>text.includes(term));
 }).sort((a,b)=>b.startDate.localeCompare(a.startDate)||a.title.localeCompare(b.title))})).filter(group=>group.elections.length);
 const count=groups.reduce((sum,group)=>sum+group.elections.length,0);
 return <div className="election-browser"><label>Search elections<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Country, election or year"/></label><label>Country<select value={countryId} onChange={e=>setCountryId(e.target.value)}><option value="">All countries</option>{countries.map(country=><option key={country.id} value={country.id}>{country.name} ({data.elections.filter(e=>e.countryId===country.id).length})</option>)}</select></label><p className="meta" role="status">{count} {count===1?'election':'elections'} in {groups.length} {groups.length===1?'country':'countries'}</p>{(query||countryId)&&<button type="button" className="clear-election-filters" onClick={()=>{setQuery('');setCountryId('')}}>Clear filters</button>}<div className="election-country-groups">{groups.map(({country,elections})=><details className="election-country-group" key={country.id} open={Boolean(terms.length||countryId||elections.some(e=>e.id===selectedId))}><summary>{country.name}<span>{elections.length}</span></summary><div>{elections.map(e=><button type="button" className={'record '+(selectedId===e.id?'chosen':'')} key={e.id} aria-pressed={selectedId===e.id} onClick={()=>choose(e)}><b>{e.title}{e.round?' · '+e.round:''}</b><span>{e.startDate||'Date unknown'} · {e.type}</span><span>{e.publication} · {e.status}</span></button>)}</div></details>)}</div>{!count&&<p className="empty-state">No elections match these filters. Try another country or search term.</p>}</div>;
}
