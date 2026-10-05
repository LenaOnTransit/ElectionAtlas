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
const storageKey = 'woe-nl-municipal-classifications-v1';
export default function MunicipalComparison() {
    const [data, setData] = useState<Dataset | null>(null);
    const [error, setError] = useState('');
    const [year, setYear] = useState('2025');
    const [layer, setLayer] = useState('winner');
    const [layout, setLayout] = useState('geographic');
    const [query, setQuery] = useState('');
    const [selected, setSelected] = useState('GM0363');
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState([0, 0]);
    const [arrowScale, setArrowScale] = useState(1);
    const [threshold, setThreshold] = useState(0);
    const [bubbleSize, setBubbleSize] = useState(24);
    const [classifications, setClassifications] = useState<Record<string, Classification>>({});
    const [notice, setNotice] = useState('');
    const markerId = useId().replace(/[^a-zA-Z0-9_-]/g, '');
    useEffect(() => { const controller = new AbortController(); fetch(import.meta.env.BASE_URL + 'nl-municipal-2023-2025.json', { signal: controller.signal }).then(r => { if (!r.ok)
        throw Error('Municipal data could not be loaded.'); return r.json(); }).then((d: Dataset) => { setData(d); let c = Object.fromEntries(d.parties.map(p => [p.id, p.classification])); try {
        const stored = JSON.parse(localStorage.getItem(storageKey) || 'null');
        if (stored && typeof stored === 'object')
            for (const p of d.parties)
                if (['left', 'right', 'centre', 'unclassified'].includes(stored[p.id]))
                    c[p.id] = stored[p.id];
    }
    catch { } setClassifications(c); }).catch(e => { if (e.name !== 'AbortError')
        setError('Municipal results are temporarily unavailable. Please reload to try again.'); }); return () => controller.abort(); }, []);
    const parties = useMemo(() => new Map(data?.parties.map(p => [p.id, p]) || []), [data]);
    if (!data)
        return <main className="world-main"><WorldNav /><h1>Netherlands municipal election comparison</h1><p role="status">{error || 'Loading official municipal results…'}</p>{error && <button onClick={() => window.location.reload()}>Retry</button>}</main>;
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
    function color(m: Municipality) { const r = rankedResults(m.results[year]); if (r.length > 1 && r[0].votes === r[1].votes)
        return '#888888'; const winner = parties.get(r[0]?.party)?.color || '#888888'; return layer === 'margin' ? mixWhite(winner, 0.22 + 0.78 * Math.min(1, winningMargin(m.results[year]) / 30)) : winner; }
    function label(m: Municipality) { const r = rankedResults(m.results[year]); const s = municipalShift(m.results['2023'], m.results['2025'], classifications); return `${m.name}: ${partyName(r[0].party)}, ${r[0].share.toFixed(2)}%; lead ${winningMargin(m.results[year]).toFixed(2)} percentage points; population ${number(m.population)}${layer === 'shift' ? `; ${Math.abs(s.change).toFixed(2)} points toward the ${s.change >= 0 ? 'left' : 'right'}` : ''}`; }
    function resetView() { setZoom(1); setPan([0, 0]); }
    function selectMunicipality(id: string) { setSelected(id); }
    function exportSettings() { const blob = new Blob([JSON.stringify({ comparison: 'Netherlands Tweede Kamer 2023–2025', classifications }, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'netherlands-municipal-classifications.json'; a.click(); URL.revokeObjectURL(url); }
    const w = data.width / zoom, h = data.height / zoom;
    const vx = (data.width - w) / 2 + pan[0], vy = (data.height - h) / 2 + pan[1];
    return <main className="world-main municipal-comparison"><WorldNav /><div className="kicker">Municipal map · Netherlands · experimental comparison</div><h1>Tweede Kamer: 2023 → 2025</h1><p className="standfirst">Explore all 342 European Netherlands municipalities. Compare party winners, the lead over the runner-up, and changes in the left–right vote balance.</p><div className="municipal-controls"><label>Election year<select value={year} onChange={e => { setYear(e.target.value); if (e.target.value === '2023' && layer === 'shift')
        setLayer('winner'); }}><option value="2023">22 November 2023</option><option value="2025">29 October 2025</option></select></label><label>Map layer<select value={layer} onChange={e => setLayer(e.target.value)}><option value="winner">Winning party</option><option value="margin">Winning margin</option>{year === '2025' && <option value="shift">Left–right shift since 2023</option>}</select></label><label>Municipality sizing<select value={layout} onChange={e => setLayout(e.target.value)}><option value="geographic">Geographic boundaries</option><option value="population">Population-sized circles</option></select></label><label>Find a municipality<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Amsterdam, Urk, Groningen…"/></label><label>Select municipality<select value={active.id} onChange={e => selectMunicipality(e.target.value)}>{matches.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}{!matchingIds.has(active.id) && <option value={active.id}>{active.name} (selected)</option>}</select></label></div>
    <p className="meta" role="status">{query ? `${matches.length} matching municipalities. ` : ''}{layer === 'margin' ? 'Colour identifies the largest party; deeper colour means a wider lead. The lead is the difference in vote share between the first and second parties.' : layer === 'shift' ? `Arrows point left or right according to the change in vote-share balance. ${shifted} municipalities shifted left; ${rightShifted} shifted right under the current classifications.` : 'Colour identifies the party with the most votes, which need not have a majority.'} {layout === 'population' ? 'Circle area is proportional to population on 1 January 2025; centres remain at their geographic locations and circles may overlap.' : ''}</p>
    {layer === 'margin' && <div className="municipal-margin-key"><span>Smaller lead</span><i /><span>30+ percentage points</span></div>}
    <div className="municipal-map-layout"><section className="municipal-map-panel" aria-label="Municipal election map"><div className="municipal-map-tools"><button onClick={() => setZoom(z => Math.min(8, z * 1.4))} aria-label="Zoom in">+</button><button onClick={() => setZoom(z => Math.max(1, z / 1.4))} aria-label="Zoom out">−</button><button onClick={resetView}>Reset view</button>{zoom > 1 && <><button onClick={() => setPan(p => [p[0] - w / 4, p[1]])} aria-label="Pan west">←</button><button onClick={() => setPan(p => [p[0] + w / 4, p[1]])} aria-label="Pan east">→</button><button onClick={() => setPan(p => [p[0], p[1] - h / 4])} aria-label="Pan north">↑</button><button onClick={() => setPan(p => [p[0], p[1] + h / 4])} aria-label="Pan south">↓</button></>}</div>
    {layer === 'shift' && <div className="municipal-sliders"><label>Arrow size<input type="range" min="0.4" max="2" step="0.1" value={arrowScale} onChange={e => setArrowScale(+e.target.value)}/></label><label>Hide shifts below {threshold.toFixed(1)} pp<input type="range" min="0" max="10" step="0.5" value={threshold} onChange={e => setThreshold(+e.target.value)}/></label><span>← Left · Right → · {maxShift.toFixed(2)} pp = longest arrow</span></div>}{layout === 'population' && <label className="municipal-bubble-control">Circle size<input type="range" min="10" max="45" value={bubbleSize} onChange={e => setBubbleSize(+e.target.value)}/></label>}
    <svg className="municipal-map" viewBox={`${vx} ${vy} ${w} ${h}`} role="group" aria-label={`${year} Netherlands municipal results, ${layer} layer`}><defs><marker id={markerId + '-left'} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#922c38"/></marker><marker id={markerId + '-right'} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#174c87"/></marker></defs>
    {municipalities.map(m => <path key={m.id} d={m.path} fill={layout === 'population' ? '#e8e5df' : color(m)} fillOpacity={matchingIds.has(m.id) ? layer === 'shift' ? 0.42 : 1 : 0.14} stroke={m.id === active.id ? '#141414' : '#ffffff'} strokeWidth={m.id === active.id ? 1.8 : 0.55} fillRule="evenodd" role="button" tabIndex={layout === 'geographic' ? 0 : -1} aria-label={label(m)} aria-pressed={m.id === active.id} onClick={() => selectMunicipality(m.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectMunicipality(m.id);
    } }}><title>{label(m)}</title></path>)}
    {layout === 'population' && [...municipalities].sort((a, b) => b.population - a.population).map(m => <circle key={m.id} cx={m.center[0]} cy={m.center[1]} r={populationRadius(m.population, maxPopulation, bubbleSize)} fill={color(m)} fillOpacity={matchingIds.has(m.id) ? layer === 'shift' ? 0.5 : 0.85 : 0.15} stroke={m.id === active.id ? '#141414' : '#ffffff'} strokeWidth={m.id === active.id ? 1.8 : 0.7} tabIndex={0} role="button" aria-label={label(m)} aria-pressed={m.id === active.id} onClick={() => selectMunicipality(m.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectMunicipality(m.id);
    } }}><title>{label(m)}</title></circle>)}
    {layer === 'shift' && municipalities.filter(m => matchingIds.has(m.id)).map(m => { const change = municipalShift(m.results['2023'], m.results['2025'], classifications).change; if (Math.abs(change) < Math.max(.005, threshold))
        return null; const length = Math.abs(change) / maxShift * 35 * arrowScale; const dir = change > 0 ? -1 : 1; const x = m.center[0], y = m.center[1]; return <line key={m.id} x1={x - dir * length / 2} y1={y} x2={x + dir * length / 2} y2={y} stroke={change > 0 ? '#922c38' : '#174c87'} strokeWidth={m.id === active.id ? 2.6 : 1.5} markerEnd={`url(#${markerId}-${change > 0 ? 'left' : 'right'})`} pointerEvents="none"><title>{m.name}: {Math.abs(change).toFixed(2)} pp {change > 0 ? 'left' : 'right'}</title></line>; })}</svg><p className="meta">Boundaries and population: CBS / PDOK, 2025. Each municipality retains its geographic location. Use zoom, the search box or the selector for small municipalities.</p>
    <div className="municipal-party-key">{[...new Set(municipalities.flatMap(m => { const r = rankedResults(m.results[year]); return r[0].votes === r[1]?.votes ? [] : [r[0].party]; }))].map(id => <span key={id}><i style={{ background: parties.get(id)?.color }}/>{partyName(id)}</span>)}<span><i style={{ background: '#888888' }}/>Tie</span></div></section>
    <aside className="municipal-detail" aria-live="polite"><div className="kicker">Selected municipality · {active.id}</div><h2>{active.name}</h2><p>{number(active.population)} residents · 1 January 2025</p><div className="municipal-winner" style={{ borderColor: color(active) }}><b>{rows[0].votes === rows[1]?.votes ? 'Joint first place' : partyName(rows[0].party)}</b><span>{rows[0].share.toFixed(2)}% · lead {winningMargin(active.results[year]).toFixed(2)} pp</span><small>{year} turnout: {active.results[year].turnout == null ? 'Not recorded' : active.results[year].turnout.toFixed(2) + '%'}</small></div>{active.results[year].turnout!=null&&active.results[year].turnout>100&&<p className="meta">The official local turnout is above 100%. Votes cast using a voter pass from another municipality can exceed the number of locally registered eligible voters.</p>}<h3>2023 → 2025 vote balance</h3><p className="municipal-shift-value" style={{ color: shift.change > 0 ? '#922c38' : shift.change < 0 ? '#174c87' : undefined }}>{Math.abs(shift.change) < .005 ? 'No net shift' : `${Math.abs(shift.change).toFixed(2)} pp ${shift.change > 0 ? '← left' : 'right →'}`}</p><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Bloc</th><th>2023</th><th>2025</th><th>Change</th></tr></thead><tbody>{(['left', 'right', 'centre', 'unclassified'] as const).map(b => <tr key={b}><th>{b === 'unclassified' ? 'Unclassified' : b[0].toUpperCase() + b.slice(1)}</th><td>{shift.before[b].toFixed(2)}%</td><td>{shift.after[b].toFixed(2)}%</td><td>{signed(shift.after[b] - shift.before[b])} pp</td></tr>)}</tbody></table></div><p className="meta">Shift = (left share − right share) in 2025 minus the same balance in 2023. Centre and unclassified parties stay in the valid-vote denominator but contribute to neither bloc. This compares totals; it does not identify how individual people changed their votes.</p><h3>Full municipal results</h3><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Party</th><th>2023</th><th>2025</th><th>Change</th></tr></thead><tbody>{[...data.parties].filter(p => active.results['2023'].votes[p.id] != null || active.results['2025'].votes[p.id] != null).sort((a, b) => (active.results[year].votes[b.id] || 0) - (active.results[year].votes[a.id] || 0)).map(p => { const a = active.results['2023'].votes[p.id] || 0, b = active.results['2025'].votes[p.id] || 0; const as = 100 * a / active.results['2023'].valid, bs = 100 * b / active.results['2025'].valid; return <tr key={p.id}><th><i className="municipal-swatch" style={{ background: p.color }}/>{p.name}</th><td>{as.toFixed(2)}%<small>{number(a)} votes</small></td><td>{bs.toFixed(2)}%<small>{number(b)} votes</small></td><td>{signed(bs - as)} pp</td></tr>; })}</tbody></table></div><p className="meta">Valid votes: {number(active.results['2023'].valid)} (2023) · {number(active.results['2025'].valid)} (2025). An absent list is treated as zero votes for this comparison.</p><p><a href={active.results['2023'].source} target="_blank" rel="noreferrer">Official 2023 municipal result</a> · <a href={active.results['2025'].source} target="_blank" rel="noreferrer">Official 2025 municipal result</a></p></aside></div>
    <section className="municipal-classifications"><h2>Control the left–right comparison</h2><p>Our starting classifications are an editorial broad left–right grouping, not official Kiesraad labels or the hidden ideology ratings. Parties such as D66, CDA, NSC, ChristenUnie and DENK can reasonably be grouped differently depending on the axis. Change any party below; both years recalculate immediately with the same definition. Small lists without an assessment start unclassified.</p><details><summary>Adjust party classifications ({data.parties.length} lists)</summary><div className="municipal-classification-grid">{data.parties.map(p => <label key={p.id}><span><i className="municipal-swatch" style={{ background: p.color }}/>{p.name}</span><select aria-label={`${p.name} bloc`} value={classifications[p.id] || 'unclassified'} onChange={e => { setClassifications(c => ({ ...c, [p.id]: e.target.value as Classification })); setNotice('Custom classifications apply to this comparison.'); }}><option value="left">Left</option><option value="centre">Centre</option><option value="right">Right</option><option value="unclassified">Unclassified</option></select></label>)}</div></details><div className="municipal-setting-actions"><button onClick={() => { try {
        localStorage.setItem(storageKey, JSON.stringify(classifications));
        setNotice('Saved in this browser. Other visitors keep our default classifications.');
    }
    catch {
        setNotice('Browser storage is unavailable. You can still export these settings.');
    } }}>Save in this browser</button><button onClick={() => { setClassifications(Object.fromEntries(data.parties.map(p => [p.id, p.classification]))); try {
        localStorage.removeItem(storageKey);
    }
    catch { } setNotice('Our default classifications restored.'); }}>Reset classifications</button><button onClick={exportSettings}>Export classifications</button><label>Import classifications<input type="file" accept="application/json,.json" onChange={async (e) => { const file = e.target.files?.[0]; if (!file)
        return; try {
        if (file.size > 100000)
            throw Error();
        const value = JSON.parse(await file.text());
        const c = value.classifications;
        if (!c || typeof c !== 'object' || data.parties.some(p => !['left', 'right', 'centre', 'unclassified'].includes(c[p.id])))
            throw Error();
        setClassifications(Object.fromEntries(data.parties.map(p => [p.id, c[p.id]])));
        setNotice('Imported classifications. Save in this browser to keep them.');
    }
    catch {
        setNotice('Could not import: choose an exported comparison settings file.');
    } e.target.value = ''; }}/></label></div><p role="status" className="meta">{notice || 'Your changes affect this browser’s comparison and do not alter our published party or ideology records.'}</p></section>
    <section><h2>Coverage and sources</h2><p>All participating lists are included. Shares use valid candidate votes; blank and invalid ballots are excluded. This is a municipal breakdown of a national election, not a municipal council election.</p>{data.notes.map((note, i) => <p key={i} className="meta">{note}</p>)}<p>Caribbean Netherlands and non-resident voting records are retained separately and are outside this European Netherlands map.</p><details><summary>Results outside the map</summary><div className="world-table-scroll"><table className="world-result-table"><thead><tr><th>Area</th><th>2023 largest party</th><th>2025 largest party</th></tr></thead><tbody>{data.outsideMap.map(m => <tr key={m.name}><th>{m.name}</th>{['2023', '2025'].map(y => { const r = rankedResults(m.results[y]); return <td key={y}>{partyName(r[0].party)} · {r[0].share.toFixed(2)}%<br />{number(m.results[y].valid)} valid votes · <a href={m.results[y].source} target="_blank" rel="noreferrer">Full official result</a></td>; })}</tr>)}</tbody></table></div></details>{data.sources.map(s => <p key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.label}</a></p>)}<p className="meta">Reviewed {data.checked}. <AppLink href="/world/election/world-netherlands-2023">National 2023 result</AppLink> · <AppLink href="/world/election/world-netherlands-2025">National 2025 result</AppLink></p></section></main>;
}
