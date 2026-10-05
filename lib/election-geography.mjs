// A dataset joins elections and results to stable geographic unit IDs and a named
// boundary set. Importers project/simplify source geometry to SVG paths once.
export function rankedResults(result){
 if(!result||result.valid<=0)return [];
 return Object.entries(result.votes).map(([party,votes])=>({party,votes,share:100*votes/result.valid})).sort((a,b)=>b.votes-a.votes||a.party.localeCompare(b.party));
}
export function winningMargin(result){const rows=rankedResults(result);return rows.length>1?rows[0].share-rows[1].share:rows.length?rows[0].share:0;}
export function blocShares(result,classifications){let left=0,right=0,centre=0,unclassified=0;for(const [id,votes]of Object.entries(result.votes)){const bloc=classifications[id];if(bloc==='left')left+=votes;else if(bloc==='right')right+=votes;else if(bloc==='centre')centre+=votes;else unclassified+=votes;}const share=v=>result.valid?100*v/result.valid:0;return {left:share(left),right:share(right),centre:share(centre),unclassified:share(unclassified),balance:share(left-right)};}
export function voteShift(before,after,beforeClassifications,afterClassifications=beforeClassifications){if(!before?.valid||!after?.valid)return null;const a=blocShares(before,beforeClassifications),b=blocShares(after,afterClassifications);return {before:a,after:b,leftChange:b.left-a.left,rightChange:b.right-a.right,change:b.balance-a.balance};}
export function populationRadius(population,maximum,size=24){return population>0&&maximum>0?size*Math.sqrt(population/maximum):0;}
export function mixWhite(hex,strength){const s=Math.max(0,Math.min(1,strength));return '#'+[1,3,5].map(i=>Math.round(255+(parseInt(hex.slice(i,i+2),16)-255)*s).toString(16).padStart(2,'0')).join('');}
export function classifications(election){return Object.fromEntries(election.parties.map(p=>[p.id,p.classification||'unclassified']));}
export function comparableElection(dataset,election){
 const previous=dataset.elections.find(e=>e.id===election.previousElectionId);
 // No inferred comparisons across changing boundaries or different vote bases.
 return previous&&previous.boundarySetId===election.boundarySetId&&previous.voteBasis===election.voteBasis?previous:null;
}
export function geographyView(dataset,electionId){
 const election=dataset.elections.find(e=>e.id===electionId)||dataset.elections.find(e=>e.id===dataset.defaultElectionId)||dataset.elections[0];
 const previous=comparableElection(dataset,election),boundaries=dataset.boundaries.find(b=>b.id===election.boundarySetId);
 const currentClasses=classifications(election),previousClasses=previous?classifications(previous):{};
 const units=dataset.units.filter(u=>boundaries.features[u.id]).map(unit=>({...unit,...boundaries.features[unit.id],result:election.results[unit.id],previousResult:previous?.results[unit.id],shift:previous?voteShift(previous.results[unit.id],election.results[unit.id],previousClasses,currentClasses):null}));
 const shifts=units.filter(u=>u.shift);
 const hasClassifications=previous&&[election,previous].every(e=>e.parties.some(p=>p.classification==='left'||p.classification==='right'));
 return {election,previous,boundaries,units,hasClassifications:!!hasClassifications,maxPopulation:Math.max(0,...units.map(u=>u.population||0)),maxShift:Math.max(1,...shifts.map(u=>Math.abs(u.shift.change))),leftShifted:shifts.filter(u=>u.shift.change>.005).length,rightShifted:shifts.filter(u=>u.shift.change<-.005).length,comparedUnits:shifts.length};
}
export function validateGeographyDataset(d){
 const fail=message=>{throw Error('Invalid election geography dataset: '+message);};
 const text=value=>typeof value==='string'&&!!value.trim();
 const unique=(items,label)=>{const ids=new Set();for(const item of items){if(!text(item?.id)||ids.has(item.id))fail(label+' IDs must be unique');ids.add(item.id);}return ids;};
 if(d?.version!==1||!Array.isArray(d.units)||!Array.isArray(d.elections)||!d.elections.length||!Array.isArray(d.boundaries))fail('unsupported structure');
 if(!text(d.id)||!text(d.title)||!text(d.unitLabel)||!text(d.unitPlural)||typeof d.description!=='string'||typeof d.coverageNote!=='string'||!Array.isArray(d.notes)||!d.notes.every(n=>typeof n==='string')||!Array.isArray(d.sources))fail('missing presentation metadata');
 const safeSource=s=>{if(!text(s?.label)||typeof s.url!=='string')return false;try{const u=new URL(s.url);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}};
 if(d.comparisonNotes&&(!Array.isArray(d.comparisonNotes)||!d.comparisonNotes.every(n=>typeof n==='string')))fail('invalid comparison notes');
 if(!d.sources.every(safeSource))fail('invalid source URL');
 const units=unique(d.units,'unit'),elections=unique(d.elections,'election'),boundaries=unique(d.boundaries,'boundary');
 if(!elections.has(d.defaultElectionId))fail('default election not found');
 for(const u of d.units)if(!text(u.name)||(u.population!=null&&(!Number.isFinite(u.population)||u.population<0)))fail('invalid unit');
 for(const b of d.boundaries){if(!(Number.isFinite(b.width)&&Number.isFinite(b.height)&&b.width>0&&b.height>0)||!b.features)fail('invalid boundary viewport');for(const [id,f]of Object.entries(b.features)){if(!units.has(id)||typeof f.path!=='string'||!/^M/.test(f.path)||!Array.isArray(f.center)||f.center.length!==2||!f.center.every(Number.isFinite))fail('invalid geometry join');}}
 for(const e of d.elections){
  if(!text(e.label)||!text(e.name)||!text(e.country)||!boundaries.has(e.boundarySetId)||!e.voteBasis||!e.results||!Array.isArray(e.parties))fail('invalid election');
  if(e.previousElectionId&&(!elections.has(e.previousElectionId)||e.previousElectionId===e.id))fail('invalid previous election');
  const parties=unique(e.parties,'party');for(const p of e.parties){if(!text(p.name)||!/^#[0-9a-f]{6}$/i.test(p.color)||p.classification&&!['left','right','centre','unclassified'].includes(p.classification))fail('invalid party metadata');}
  for(const [id,r]of Object.entries(e.results)){
   if(!units.has(id)||!r||!Number.isSafeInteger(r.valid)||r.valid<0||!r.votes||r.turnout!=null&&(!Number.isFinite(r.turnout)||r.turnout<0))fail('invalid result');
   if(r.source&&!safeSource({label:'Result',url:r.source}))fail('invalid result source');
   let sum=0;for(const [party,votes]of Object.entries(r.votes)){if(!parties.has(party)||!Number.isSafeInteger(votes)||votes<0)fail('invalid vote / party join');sum+=votes;}
   if(sum!==r.valid)fail('party votes must reconcile with valid votes');
  }
 }
 return d;
}
