import {MapPaletteControl,useMapPalette,accessibleColour,MapPatternDefs,MapSwatch} from '../appearance';
import { useEffect, useId, useMemo, useState } from 'react';
import { AppLink } from '../../src/navigation';
import { WorldNav } from '../world/shared';
import { rankedResults, winningMargin, municipalShift, populationRadius, mixWhite, type MunicipalResult, type Classification } from '../../lib/municipal-comparison.mjs';
type Party = {
    id: string;
    name: string;
    color: string;
    classification: Classification;
    aliases: string[];
};
type Municipality = {
    id: string;
    name: string;
    population: number;
    path: string;
    center: number[];
    results: Record<string, MunicipalResult>;
};
type Dataset = {
    width: number;
    height: number;
    municipalities: Municipality[];
    parties: Party[];
    notes: string[];
    sources: {
        label: string;
        url: string;
    }[];
    checked: string;
    outsideMap: {
        name: string;
        results: Record<string, MunicipalResult>;
    }[];
};
const signed = (n: number) => `${n > 0 ? '+' : ''}${n.toFixed(2)}`;
const number = (n: number) => n.toLocaleString('en-GB');
export default function MunicipalComparison() {
    const [data, setData] = useState<Dataset | null>(null);
    const [error, setError] = useState('');
    const [year, setYear] = useState(() => new URLSearchParams(window.location.search).get('year') === '2023' ? '2023' : '2025');
    const [palette,setPalette]=useMapPalette();
    const [layer, setLayer] = useState('winner');
    const [layout, setLayout] = useState('geographic');
    const [query, setQuery] = useState('');
    const [selected, setSelected] = useState('GM0363');
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState([0, 0]);
    const [arrowScale, setArrowScale] = useState(1);
    const [threshold, setThreshold] = useState(0);
    const [bubbleSize, setBubbleSize] = useState(24);
    const [comparison, setComparison] = useState(false);
    const markerId = useId().replace(/[^a-zA-Z0-9_-]/g, '');
    useEffect(() => { const controller = new AbortController(); fetch(import.meta.env.BASE_URL + 'nl-municipal-2023-2025.json?v=20261005-centre', { signal: controller.signal }).then(r => { if (!r.ok)
        throw Error('Municipal data could not be loaded.'); return r.json(); }).then((d: Dataset) => setData(d)).catch(e => { if (e.name !== 'AbortError')
        setError('Municipal results are temporarily unavailable. Please reload to try again.'); }); return () => controller.abort(); }, []);
    const parties = useMemo(() => new Map(data?.parties.map(p => [p.id, p]) || []), [data]);
    if (!data)
        return <main className="world-main"><WorldNav /><h1>Netherlands municipal results</h1><p role="status">{error || 'Loading official municipal results…'}</p>{error && <button onClick={() => window.location.reload()}>Retry</button>}</main>;
    const classifications: Record<string, Classification> = Object.fromEntries(data.parties.map(p => [p.id, p.classification]));
    const municipalities = data.municipalities;
    const active = municipalities.find(m => m.id === selected) || municipalities[0];
    const maxPopulation = Math.max(...municipalities.map(m => m.population));
    const maxShift = Math.max(1, ...municipalities.map(m => Math.abs(municipalShift(m.results['2023'], m.results['2025'], classifications).change)));
    const matches = municipalities.filter(m => m.name.toLowerCase().includes(query.toLowerCase()));
    const matchingIds = new Set(matches.map(m => m.id));
    const rows = rankedResults(active.results[year]);
    const shift = municipalShift(active.results['2023'], active.results['2025'], classifications);
    const shifted = municipalities.filter(m => municipalShift(m.results['2023'], m.results['2025'], classifications).change > 0.005).length;
    const rightShifted = municipalities.filter(m => municipalShift(m.results['2023'], m.results['2025'], classifications).change < -.005).length;
    const partyName = (id: string) => parties.get(id)?.name || id;
    const partyIndex=(id:string)=>data!.parties.findIndex(p=>p.id===id);
    const partyColor=(id:string)=>palette==='accessible'?accessibleColour(partyIndex(id)):parties.get(id)?.color||'#888888';
    function mapFill(m:Municipality){const r=rankedResults(m.results[year]);return palette==='accessible'&&layer==='winner'&&r[0].votes!==r[1]?.votes?`url(#${markerId}-party-${partyIndex(r[0].party)})`:color(m)}
    function color(m: Municipality) { const r = rankedResults(m.results[year]); if (r.length > 1 && r[0].votes === r[1].votes)
        return '#888888'; const winner = partyColor(r[0]?.party); return layer === 'margin' ? mixWhite(winner, 0.22 + 0.78 * Math.min(1, winningMargin(m.results[year]) / 30)) : winner; }
    function label(m: Municipality) { const r = rankedResults(m.results[year]); const s = municipalShift(m.results['2023'], m.results['2025'], classifications); return `${m.name}: ${partyName(r[0].party)}, ${r[0].share.toFixed(2)}%; lead ${winningMargin(m.results[year]).toFixed(2)} percentage points; population ${number(m.population)}${layer === 'shift' ? `; ${Math.abs(s.change).toFixed(2)} points toward the ${s.change >= 0 ? 'left' : 'right'}` : ''}`; }
    function resetView() { setZoom(1); setPan([0, 0]); }
    function selectMunicipality(id: string) { setSelected(id); }
    const w = data.width / zoom, h = data.height / zoom;
    const vx = (data.width - w) / 2 + pan[0], vy = (data.height - h) / 2 + pan[1];
    return <main className="world-main municipal-comparison"><WorldNav /><div className="kicker">Municipal map · Netherlands</div><h1>Tweede Kamer · {comparison ? '2023 → 2025' : year}</h1><p className="standfirst">Explore election results in all 342 European Netherlands municipalities. View winning parties, winning margins and population-sized circles. Select the 2025 comparison view to explore changes since 2023.</p><div className="municipal-controls"><label>Election year<select value={year} onChange={e => { setYear(e.target.value); setComparison(false); if (layer === 'shift') setLayer('winner'); }}><option value="2023">22 November 2023</option><option value="2025">29 October 2025</option></select></label>{year === '2025' && <label>View<select value={comparison ? 'comparison' : 'results'} onChange={e => { const compare = e.target.value === 'comparison'; setComparison(compare); if (!compare && layer === 'shift') setLayer('winner'); }}><option value="results">Election results</option><option value="comparison">Compare with 2023</option></select></label>}<label>Map layer<select value={layer} onChange={e => setLayer(e.target.value)}><option value="winner">Winning party</option><option value="margin">Winning margin</option>{comparison && <option value="shift">Left–right shift since 2023</option>}</select></label><label>Municipality sizing<select value={layout} onChange={e => setLayout(e.target.value)}><option value="geographic">Geographic boundaries</option><option value="population">Population-sized circles</option></select></label><label>Find a municipality<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Amsterdam, Urk, Groningen…"/></label><label>Select municipality<select value={active.id} onChange={e => selectMunicipality(e.target.value)}>{matches.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}{!matchingIds.has(active.id) && <option value={active.id}>{active.name} (selected)</option>}</select></label></div>
    <p className="meta" role="status">{query ? `${matches.length} matching municipalities. ` : ''}{palette==='accessible'&&layer==='winner'?'Colours and patterns match the party key. Select a municipality for exact results. ':''}{layer === 'margin' ? 'Colour identifies the largest party; deeper colour means a wider lead. The lead is the difference in vote share between the first and second parties.' : layer === 'shift' ? `Arrows point left or right according to the change in vote-share balance. ${shifted} municipalities shifted left; ${rightShifted} shifted right under our fixed classifications.` : 'Colour identifies the party with the most votes, which need not have a majority.'} {layout === 'population' ? 'Circle area is proportional to population on 1 January 2025; centres remain at their geographic locations and circles may overlap.' : ''}</p>
    {layer === 'margin' && <div className="municipal-margin-key"><span>Smaller lead</span><i /><span>30+ percentage points</span></div>}
    <MapPaletteControl value={palette} onChange={setPalette}/><div className="municipal-map-layout"><section className="municipal-map-panel" aria-label="Municipal election map"><div className="municipal-map-tools"><button onClick={() => setZoom(z => Math.min(8, z * 1.4))} aria-label="Zoom in">+</button><button onClick={() => setZoom(z => Math.max(1, z / 1.4))} aria-label="Zoom out">−</button><button onClick={resetView}>Reset view</button>{zoom > 1 && <><button onClick={() => setPan(p => [p[0] - w / 4, p[1]])} aria-label="Pan west">←</button><button onClick={() => setPan(p => [p[0] + w / 4, p[1]])} aria-label="Pan east">→</button><button onClick={() => setPan(p => [p[0], p[1] - h / 4])} aria-label="Pan north">↑</button><button onClick={() => setPan(p => [p[0], p[1] + h / 4])} aria-label="Pan south">↓</button></>}</div>
    {layer === 'shift' && <div className="municipal-sliders"><label>Arrow size<input type="range" min="0.4" max="2" step="0.1" value={arrowScale} onChange={e => setArrowScale(+e.target.value)}/></label><label>Hide shifts below {threshold.toFixed(1)} pp<input type="range" min="0" max="10" step="0.5" value={threshold} onChange={e => setThreshold(+e.target.value)}/></label><span>← Left · Right → · {maxShift.toFixed(2)} pp = longest arrow</span></div>}{layout === 'population' && <label className="municipal-bubble-control">Circle size<input type="range" min="10" max="45" value={bubbleSize} onChange={e => setBubbleSize(+e.target.value)}/></label>}
    <svg className="municipal-map" viewBox={`${vx} ${vy} ${w} ${h}`} role="group" aria-label={`${year} Netherlands municipal results, ${layer} layer`}><MapPatternDefs prefix={markerId+'-party'} count={data.parties.length}/><defs><marker id={markerId + '-left'} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#922c38"/></marker><marker id={markerId + '-right'} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#174c87"/></marker></defs>
    {municipalities.map(m => <path key={m.id} d={m.path} fill={layout === 'population' ? '#e8e5df' : mapFill(m)} fillOpacity={matchingIds.has(m.id) ? layer === 'shift' ? 0.42 : 1 : 0.14} stroke={m.id === active.id ? '#141414' : '#ffffff'} strokeWidth={m.id === active.id ? 1.8 : 0.55} fillRule="evenodd" role="button" tabIndex={layout === 'geographic' ? 0 : -1} aria-label={label(m)} aria-pressed={m.id === active.id} onClick={() => selectMunicipality(m.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectMunicipality(m.id);
    } }}><title>{label(m)}</title></path>)}
    {layout === 'population' && [...municipalities].sort((a, b) => b.population - a.population).map(m => <circle key={m.id} cx={m.center[0]} cy={m.center[1]} r={populationRadius(m.population, maxPopulation, bubbleSize)} fill={mapFill(m)} fillOpacity={matchingIds.has(m.id) ? layer === 'shift' ? 0.5 : 0.85 : 0.15} stroke={m.id === active.id ? '#141414' : '#ffffff'} strokeWidth={m.id === active.id ? 1.8 : 0.7} tabIndex={0} role="button" aria-label={label(m)} aria-pressed={m.id === active.id} onClick={() => selectMunicipality(m.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectMunicipality(m.id);
    } }}><title>{label(m)}</title></circle>)}
    {layer === 'shift' && municipalities.filter(m => matchingIds.has(m.id)).map(m => { const change = municipalShift(m.results['2023'], m.results['2025'], classifications).change; if (Math.abs(change) < Math.max(.005, threshold))
        return null; const length = Math.abs(change) / maxShift * 35 * arrowScale; const dir = change > 0 ? -1 : 1; const x = m.center[0], y = m.center[1]; return <line key={m.id} x1={x - dir * length / 2} y1={y} x2={x + dir * length / 2} y2={y} stroke={change > 0 ? '#922c38' : '#174c87'} strokeWidth={m.id === active.id ? 2.6 : 1.5} markerEnd={`url(#${markerId}-${change > 0 ? 'left' : 'right'})`} pointerEvents="none"><title>{m.name}: {Math.abs(change).toFixed(2)} pp {change > 0 ? 'left' : 'right'}</title></line>; })}</svg><p className="meta">Boundaries and population: CBS / PDOK, 2025. Each municipality retains its geographic location. Use zoom, the search box or the selector for small municipalities.</p>
    <div className="municipal-party-key">{[...new Set(municipalities.flatMap(m => { const r = rankedResults(m.results[year]); return r[0].votes === r[1]?.votes ? [] : [r[0].party]; }))].map(id => <span key={id}><MapSwatch index={partyIndex(id)} original={parties.get(id)?.color||'#888888'} palette={palette} patterns={layer==='winner'}/>{partyName(id)}</span>)}<span><i style={{ background: '#888888' }}/>Tie</span></div></section>
    <aside className="municipal-detail" aria-live="polite"><div className="kicker">Selected municipality · {active.id}</div><h2>{active.name}</h2><p>{number(active.population)} residents · 1 January 2025</p><div className="municipal-winner" style={{ borderColor: color(active) }}><b>{rows[0].votes === rows[1]?.votes ? 'Joint first place' : partyName(rows[0].party)}</b><span>{rows[0].share.toFixed(2)}% · lead {winningMargin(active.results[year]).toFixed(2)} pp</span><small>{year} turnout: {active.results[year].turnout == null ? 'Not recorded' : active.results[year].turnout.toFixed(2) + '%'}</small></div>{active.results[year].turnout!=null&&active.results[year].turnout>100&&<p className="meta">The official local turnout is above 100%. Votes cast using a voter pass from another municipality can exceed the number of locally registered eligible voters.</p>}{comparison && <><h3>2023 → 2025 vote balance</h3><p className="municipal-shift-value" style={{ color: shift.change > 0 ? '#922c38' : shift.change < 0 ? '#174c87' : undefined }}>{Math.abs(shift.change) < .005 ? 'No net shift' : `${Math.abs(shift.change).toFixed(2)} pp ${shift.change > 0 ? '← left' : 'right →'}`}</p><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Bloc</th><th>2023</th><th>2025</th><th>Change</th></tr></thead><tbody>{(['left', 'right', 'centre', 'unclassified'] as const).map(b => <tr key={b}><th>{b === 'unclassified' ? 'Unclassified' : b[0].toUpperCase() + b.slice(1)}</th><td>{shift.before[b].toFixed(2)}%</td><td>{shift.after[b].toFixed(2)}%</td><td>{signed(shift.after[b] - shift.before[b])} pp</td></tr>)}</tbody></table></div><p className="meta">Shift = (left share − right share) in 2025 minus the same balance in 2023. Centre and unclassified parties stay in the valid-vote denominator but contribute to neither bloc. This compares totals; it does not identify how individual people changed their votes.</p></>}<h3>{year} municipal results{comparison ? ' compared with 2023' : ''}</h3><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Party</th>{comparison ? <><th>2023</th><th>2025</th><th>Change</th></> : <><th>Votes</th><th>Vote share</th></>}</tr></thead><tbody>{[...data.parties].filter(p => comparison ? active.results['2023'].votes[p.id] != null || active.results['2025'].votes[p.id] != null : active.results[year].votes[p.id] != null).sort((a, b) => (active.results[year].votes[b.id] || 0) - (active.results[year].votes[a.id] || 0)).map(p => { const a = active.results['2023'].votes[p.id] || 0, b = active.results['2025'].votes[p.id] || 0; const as = 100 * a / active.results['2023'].valid, bs = 100 * b / active.results['2025'].valid; return <tr key={p.id}><th><MapSwatch index={partyIndex(p.id)} original={p.color} palette={palette} patterns={layer==='winner'}/>{p.name}</th>{comparison ? <><td>{as.toFixed(2)}%<small>{number(a)} votes</small></td><td>{bs.toFixed(2)}%<small>{number(b)} votes</small></td><td>{signed(bs - as)} pp</td></> : <><td>{number(active.results[year].votes[p.id] || 0)}</td><td>{(100 * (active.results[year].votes[p.id] || 0) / active.results[year].valid).toFixed(2)}%</td></>}</tr>; })}</tbody></table></div><p className="meta">Valid votes: {comparison ? `${number(active.results['2023'].valid)} (2023) · ${number(active.results['2025'].valid)} (2025). An absent list is treated as zero votes for this comparison.` : `${number(active.results[year].valid)} (${year}).`}</p><p>{(comparison ? ['2023', '2025'] : [year]).map((y, i) => <span key={y}>{i > 0 && ' · '}<a href={active.results[y].source} target="_blank" rel="noreferrer">Official {y} municipal result</a></span>)}</p></aside></div>
    {comparison && <section className="municipal-classifications"><h2>Our left–right classifications</h2><p>Our fixed editorial grouping uses a broad international ideological spectrum and is independent of the hidden ideology ratings. D66 and Volt are classified as centre. Centre and unclassified parties contribute to neither the left nor right bloc.</p><details><summary>View party classifications ({data.parties.length} lists)</summary><div className="municipal-classification-grid">{data.parties.map(p => <div key={p.id}><MapSwatch index={partyIndex(p.id)} original={p.color} palette={palette} patterns={layer==='winner'}/>{p.name} · {p.classification}</div>)}</div></details></section>}
    <section><h2>Coverage and sources</h2><p>All participating lists are included. Shares use valid candidate votes; blank and invalid ballots are excluded. This is a municipal breakdown of a national election, not a municipal council election.</p>{data.notes.filter(note => comparison || !note.startsWith('Left–right shift')).map((note, i) => <p key={i} className="meta">{note}</p>)}<p>Caribbean Netherlands and non-resident voting records are retained separately and are outside this European Netherlands map.</p><details><summary>Results outside the map</summary><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Area</th>{(comparison ? ['2023', '2025'] : [year]).map(y => <th key={y}>{y} largest party</th>)}</tr></thead><tbody>{data.outsideMap.map(m => <tr key={m.name}><th>{m.name}</th>{(comparison ? ['2023', '2025'] : [year]).map(y => { const r = rankedResults(m.results[y]); return <td key={y}>{partyName(r[0].party)} · {r[0].share.toFixed(2)}%<br />{number(m.results[y].valid)} valid votes · <a href={m.results[y].source} target="_blank" rel="noreferrer">Full official result</a></td>; })}</tr>)}</tbody></table></div></details>{data.sources.map(s => <p key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.label}</a></p>)}<p className="meta">Reviewed {data.checked}. <AppLink action href="/world/election/world-netherlands-2023">National 2023 result</AppLink> · <AppLink action href="/world/election/world-netherlands-2025">National 2025 result</AppLink></p></section></main>;
}
