import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
function moduleUrl(file,imports={}){let source=fs.readFileSync(file,'utf8');for(const [from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;return 'data:text/javascript;base64,'+Buffer.from(js).toString('base64');}
const houseURL=moduleUrl('lib/house.ts');const worldURL=moduleUrl('lib/world.ts',{'./house':houseURL,'./legitimacy':moduleUrl('lib/legitimacy.ts')});const model=await import(worldURL);const {seedWorldElections}=await import(moduleUrl('lib/world-seeds.ts',{'./world':worldURL}));const {seedCountries}=await import(moduleUrl('lib/world-countries.ts',{'./world':worldURL}));
for(const country of seedCountries)model.validateCountry(country);assert.equal(new Set(seedCountries.map(c=>c.id)).size,seedCountries.length);assert.ok(seedCountries.length>=190);for(const election of seedWorldElections){model.validateWorldElection(election);assert.ok(seedCountries.some(c=>c.id===election.countryId));}assert.equal(new Set(seedWorldElections.map(e=>e.id)).size,seedWorldElections.length);
const draft={...seedWorldElections[0],publication:'draft'};assert.equal(model.publishedWorld({countries:seedCountries,elections:[draft]}).elections.length,0);
const multi={...seedWorldElections[0],startDate:'2026-10-30',endDate:'2026-11-03'};assert.deepEqual(model.calendarDays(multi,'2026-10'),['2026-10-30','2026-10-31']);assert.deepEqual(model.calendarDays(multi,'2026-11'),['2026-11-01','2026-11-02','2026-11-03']);assert.deepEqual(model.calendarDays({...multi,precision:'month'},'2026-10'),[]);assert.deepEqual(model.calendarDays({...multi,status:'postponed'},'2026-10'),[]);
assert.equal(model.validDate('2026-02-30'),false);assert.equal(model.validDate('2024-02-29'),true);assert.equal(model.dateLabel({...multi,startDate:'2027-04-18',endDate:'',precision:'month'}),'April 2027');assert.equal(model.dateLabel({...multi,startDate:'',endDate:'',precision:'unknown'}),'Date not announced');
assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],sources:[]}));assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],startDate:'2026-02-30'}));assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],sources:[{label:'Unsafe',url:'javascript:alert(1)'}]}));assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],sources:[{label:'Unsafe',url:'https://user:secret@example.org'}]}));assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],results:[{id:'x',name:'Bad',party:'',color:'#123456',votes:-1,share:null,seats:null,electoralVotes:null,winner:false}]}));
assert.ok(seedWorldElections.filter(e=>e.status==='held').some(e=>e.results.length));const fr=seedWorldElections.filter(e=>e.seriesId==='france-president-2027');assert.equal(fr.length,2);
const explore=await import(moduleUrl('lib/explore.ts',{'./world':worldURL}));const us=seedWorldElections.filter(e=>e.countryId==='us'&&e.status==='held');assert.equal(explore.comparable(us[0],us[1]),true);assert.equal(explore.comparable(us[0],{...us[1],body:'Senate'}),false);assert.equal(explore.metric(undefined,'seats'),null);const chamber={...seedWorldElections[0],totalSeats:122,majorityThreshold:null};assert.equal(explore.majority(chamber),62);assert.equal(explore.majority({...chamber,majorityThreshold:61}),61);assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],live:{enabled:true,reporting:101,unit:'precincts',bulletin:'',updated:''}}));assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],totalSeats:100,majorityThreshold:101}));model.validateWorldElection({...seedWorldElections[0],live:{enabled:true,reporting:null,unit:'precincts',bulletin:'Waiting for figures',updated:''},coalitionNotes:'Editorial guidance',majorityThreshold:null});const geometry=JSON.parse(fs.readFileSync('lib/atlas-map.json','utf8'));assert.ok(geometry.length>190);for(const code of ['us','gb','nl','br','za','in'])assert.ok(geometry.some(x=>x.id===code&&x.path.startsWith('M')));
console.log(JSON.stringify({validated:true,countries:seedCountries.length,elections:seedWorldElections.length,calendar:seedWorldElections.filter(e=>e.status==='scheduled').length,archive:seedWorldElections.filter(e=>e.status==='held').length,resultTables:seedWorldElections.filter(e=>e.results.length).length,checks:['draft privacy','date precision','month-boundary voting periods','date validation','sources','safe URLs','result validation','linked rounds']}));
const parliament=await import(moduleUrl('lib/parliament.ts'));
for(const n of [0,1,2,150,650,10000]){const dots=parliament.hemicycleLayout(n);assert.equal(dots.length,n);assert.ok(dots.every(d=>Number.isFinite(d.x)&&Number.isFinite(d.y)&&d.x>=0&&d.x<=600&&d.y>=0&&d.y<=330&&d.radius>0));}
for(const n of [150,650]){const dots=parliament.hemicycleLayout(n);for(let i=0;i<dots.length;i++)for(let j=i+1;j<dots.length;j++)assert.ok(Math.hypot(dots[i].x-dots[j].x,dots[i].y-dots[j].y)>=dots[i].radius+dots[j].radius);}
const result={id:'seat-test',name:'Party',party:'',color:'#123456',votes:null,share:null,seats:20,electoralVotes:null,winner:false};
assert.equal(model.seatChange(result),null);assert.equal(model.seatChange({...result,previousSeats:0}),20);assert.equal(model.seatChangeLabel({...result,previousSeats:25}),'−5');assert.equal(model.seatChangeLabel({...result,previousSeats:20}),'0');assert.equal(model.seatChange({...result,seats:null,previousSeats:0}),null);
for(const value of [undefined,null,0,25])model.validateWorldElection({...seedWorldElections[0],totalSeats:30,results:[{...result,previousSeats:value}]});
for(const value of [-1,1.5,'20'])assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],totalSeats:30,results:[{...result,previousSeats:value}]}));
const pe={...seedWorldElections[0],type:'parliamentary',totalSeats:30,results:[result]};const pg=parliament.parliamentGroups(pe);assert.equal(pg.entered,20);assert.equal(pg.groups.reduce((n,g)=>n+g.seats,0),30);assert.equal(pg.groups.at(-1).seats,10);assert.equal(parliament.parliamentGroups({...pe,totalSeats:null}).total,20);assert.equal(parliament.parliamentGroups({...pe,totalSeats:10}),null);assert.equal(parliament.parliamentGroups({...pe,type:'presidential'}),null);
console.log('Parliament: exact seat counts, spacing, missing seats, previous-seat validation and gain/loss passed.');
const house=await import(houseURL),empty=house.emptyHouse();house.validateHouse(empty);assert.deepEqual(house.houseTotals(empty,'results'),{D:0,R:0,O:0,remaining:435,uncategorized:435});
const filled=structuredClone(empty);filled.forecast.ratings.safeD=180;filled.forecast.ratings.leanR=200;filled.forecast.ratings.tossup=40;assert.equal(house.houseTotals(filled,'polling').uncategorized,15);assert.equal(house.houseTotals(filled,'polling').remaining,55);house.validateHouse(filled);
const complete=structuredClone(empty);complete.results={...complete.results,D:218,R:217,called:'D',status:'final'};house.validateHouse(complete);assert.equal(house.houseTotals(complete,'results').remaining,0);
for(const mutate of [h=>h.forecast.ratings.safeD=436,h=>h.results.D=-1,h=>h.results.R=1.5,h=>h.results.called='D',h=>h.results.status='final',h=>h.forecast.probabilityD=101,h=>{h.forecast.genericD=60;h.forecast.genericR=50;},h=>h.forecast.demMin=210,h=>{h.forecast.demMin=230;h.forecast.demMax=200;}]){const h=structuredClone(empty);mutate(h);assert.throws(()=>house.validateHouse(h));}
const watch=structuredClone(empty);watch.races=[{id:'test',district:'NY-19',incumbent:'R',rating:'leanD',call:'D',notes:'',candidates:[{name:'Example',party:'D',poll:51,votes:123}]}];house.validateHouse(watch);assert.equal(house.houseTotals(watch,'results').D,0);assert.throws(()=>house.validateHouse({...watch,races:[...watch.races,{...watch.races[0],id:'duplicate'}]}));model.validateWorldElection({...seedWorldElections[0],house:empty});assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],house:{...empty,results:{...empty.results,D:436}}}));console.log('House: aggregate totals, majority calls, forecast ranges, missing figures and independent watchlist passed.');
const ideologyModel=await import(moduleUrl('lib/ideologies.ts'));const guide=ideologyModel.newIdeology('ideology-test');guide.title='Test tradition';ideologyModel.validateIdeology(guide);assert.throws(()=>ideologyModel.validateIdeology({...guide,status:'published'}));const publishedGuide={...guide,status:'published',summary:'A test introduction.',sections:{...guide.sections,definition:'A test definition.'},sources:[{label:'Source',url:'https://example.org/guide'}]};ideologyModel.validateIdeology(publishedGuide);for(const url of ['javascript:alert(1)','http://example.org','https://user:password@example.org'])assert.throws(()=>ideologyModel.validateIdeology({...publishedGuide,sources:[{label:'Unsafe',url}]}));assert.throws(()=>ideologyModel.validateIdeology({...publishedGuide,archived:true}));assert.throws(()=>ideologyModel.validateIdeology({...guide,date:'2026-02-30'}));model.validateWorldElection({...seedWorldElections[0],totalSeats:30,results:[{...result,ideologyIds:['ideology-test','ideology-other']}]});for(const ids of [['bad'],['ideology-test','ideology-test'],[12],'ideology-test'])assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],totalSeats:30,results:[{...result,ideologyIds:ids}]}));console.log('Ideologies: draft/publish requirements, safe sources, trash privacy and multiple party references passed.');

const atlas=await import(moduleUrl('lib/atlas-status.ts'));
const atlasElection={...seedWorldElections[0],countryId:'test',publication:'published',precision:'day',dateStatus:'confirmed',status:'scheduled',startDate:'2026-10-03',endDate:''};
const status=(e,today='2026-10-03')=>atlas.atlasElectionStatuses([e],today).get('test');
assert.equal(status(atlasElection),'today');
assert.equal(status({...atlasElection,startDate:'2026-11-03'}),'upcoming');
assert.equal(status({...atlasElection,startDate:'2026-11-04'}),undefined);
assert.equal(status({...atlasElection,startDate:'2026-10-02'}),undefined);
assert.equal(status({...atlasElection,startDate:'2026-10-01',endDate:'2026-10-04'}),'today');
assert.equal(status({...atlasElection,status:'held'}),'today');
for(const patch of [{publication:'draft'},{status:'postponed'},{status:'cancelled'},{precision:'month'},{precision:'year'},{precision:'unknown'},{dateStatus:'tba'}])assert.equal(status({...atlasElection,...patch}),undefined);
assert.equal(status({...atlasElection,startDate:'2027-02-28'},'2027-01-31'),'upcoming');
assert.equal(status({...atlasElection,startDate:'2027-03-01'},'2027-01-31'),undefined);
assert.equal(status({...atlasElection,startDate:'2028-02-29'},'2028-01-31'),'upcoming');
assert.equal(status({...atlasElection,startDate:'2027-01-31'},'2026-12-31'),'upcoming');
const future={...atlasElection,startDate:'2026-10-20'};
for(const records of [[atlasElection,future],[future,atlasElection]])assert.equal(atlas.atlasElectionStatuses(records,'2026-10-03').get('test'),'today');
assert.equal(atlas.localCalendarDate(new Date(2026,9,3,23,59)),'2026-10-03');
console.log('Atlas: calendar-month boundaries, election days, date ranges, exclusions and red priority passed.');

const politics=await import(moduleUrl('lib/political-axes.ts'));
assert.equal(politics.politicalAxes.length,9);
for(const scores of [{socialistCapitalist:-10},{socialistCapitalist:10},{socialistCapitalist:0},{}])politics.validateScores(scores);
for(const scores of [{socialistCapitalist:11},{socialistCapitalist:-11},{unknown:0},{socialistCapitalist:'1'},{socialistCapitalist:NaN},[]])assert.throws(()=>politics.validateScores(scores));
const rows=[{...result,id:'unknown',ideologyIds:[]},{...result,id:'right',ideologyIds:['ideology-r']},{...result,id:'left',ideologyIds:['ideology-l']},{...result,id:'center',ideologyIds:['ideology-r','ideology-l']}];
const positions=[{ideology_id:'ideology-r',scores:{socialistCapitalist:8,progressiveConservative:-2}},{ideology_id:'ideology-l',scores:{socialistCapitalist:-8,progressiveConservative:2}}];
assert.deepEqual(politics.orderByAxes(rows,['socialistCapitalist'],positions),['left','center','right','unknown']);
assert.deepEqual(politics.orderByAxes(rows,['socialistCapitalist'],positions,true),['right','center','left','unknown']);
assert.deepEqual(politics.orderByAxes(rows,['socialistCapitalist','progressiveConservative'],positions),['left','center','right','unknown']);
assert.deepEqual(politics.orderByAxes(rows,['democracyAutocracy'],positions),rows.map(r=>r.id));
assert.deepEqual(politics.classifyByAxes(rows,['socialistCapitalist'],positions).map(r=>r.side),['negative','neutral','positive','unassessed']);
assert.deepEqual(politics.classifyByAxes(rows,['socialistCapitalist'],positions,true).map(r=>r.side),['positive','neutral','negative','unassessed']);
for(const [axis] of politics.politicalAxes){
 const scores=[{ideology_id:'ideology-r',scores:{[axis]:8}},{ideology_id:'ideology-l',scores:{[axis]:-8}}];
 assert.deepEqual(politics.classifyByAxes(rows,[axis],scores).map(r=>r.side),['negative','neutral','positive','unassessed']);
}
assert.equal(politics.classifyByAxes([rows[1]],['socialistCapitalist','democracyAutocracy'],positions)[0].side,'unassessed');
assert.equal(politics.classifyByAxes([rows[1]],['socialistCapitalist','progressiveConservative'],[{ideology_id:'ideology-r',scores:{socialistCapitalist:2,progressiveConservative:-2}}])[0].side,'neutral');
for(const total of [1,2,100,150,650,10000]){
 const dots=parliament.hemicycleLayout(total);
 for(const counts of [[0,0,total,0],[total,0,0,0],[0,0,0,total],[Math.floor(total*.1),Math.floor(total*.05),Math.floor(total*.75),total-Math.floor(total*.1)-Math.floor(total*.05)-Math.floor(total*.75)]]){
  for(const reverse of [false,true]){
   const categories=reverse?['positive','neutral','negative','unassessed']:['negative','neutral','positive','unassessed'];
   const bySide=Object.fromEntries(['negative','neutral','positive','unassessed'].map((s,i)=>[s,counts[i]]));
   const sides=categories.flatMap(s=>Array(bySide[s]).fill(s));
   const geo=parliament.spectrumGeometry(dots,sides,reverse);
   assert.ok(geo.bands.every(b=>!b.path.includes('NaN')));
   // SVG endpoint arcs have two possible centres. Check the actual arc flags
   // select the chamber's centre, not a reflected arc below the seat row.
   for(const band of geo.bands){
    const n=band.path.match(/-?\d+(?:\.\d+)?/g).map(Number);
    const [x1,y1,r,,rotation,large,sweep,x2,y2]=n.slice(2,11);
    assert.equal(rotation,0);assert.equal(sweep,1);assert.equal(n[17],0);const dx=(x1-x2)/2,dy=(y1-y2)/2;
    const coefficient=(large===sweep?-1:1)*Math.sqrt(Math.max(0,(r*r-dx*dx-dy*dy)/(dx*dx+dy*dy)));
    assert.ok(Math.abs((x1+x2)/2+coefficient*dy-300)<1);
    assert.ok(Math.abs((y1+y2)/2-coefficient*dx-305)<1);
   }
   dots.forEach((dot,i)=>{const band=geo.bands.filter(b=>b.row===dot.row&&dot.angle>b.start&&dot.angle<b.end);assert.equal(band.length,1);assert.equal(band[0].side,sides[i]);});
   if(counts[0]||counts[2])assert.ok(geo.borders.some(b=>b.zero));
  }
 }
}
assert.deepEqual(parliament.spectrumGeometry([],[]),{bands:[],borders:[]});
assert.throws(()=>parliament.spectrumGeometry(parliament.hemicycleLayout(2),['negative']));
console.log('Parliament spectrum: all nine axes, averaging, reversed poles, neutral/unassessed seats, one-sided chambers and exact seat bands passed.');
const parties=await import(moduleUrl('lib/country-parties.ts'));const party={...parties.newParty('nl'),name:'Example',ideology_ids:['ideology-test']};parties.validateParty(party);const copied=parties.partyResult(party);assert.equal(copied.name,party.name);assert.equal(copied.color,party.color);assert.equal(copied.partyId,party.id);copied.ideologyIds.push('ideology-other');assert.equal(party.ideology_ids.length,1);party.color='#112233';assert.notEqual(copied.color,party.color);assert.throws(()=>parties.validateParty({...party,name:''}));
const legitimacy=await import(moduleUrl('lib/legitimacy.ts'));legitimacy.validateLegitimacy(legitimacy.emptyLegitimacy());assert.equal(legitimacy.legitimacyInfo(undefined)[0],'unassessed');const assessment={level:'concerns',summary:'Source-based context',reviewed:'2026-10-03',sources:[{label:'Report',url:'https://example.org/report'}]};legitimacy.validateLegitimacy(assessment);model.validateCountry({...seedCountries[0],legitimacy:assessment});for(const patch of [{summary:''},{sources:[]},{reviewed:'2026-02-30'},{level:'made-up'},{sources:[{label:'Unsafe',url:'javascript:alert(1)'}]}])assert.throws(()=>legitimacy.validateLegitimacy({...assessment,...patch}));
const observer={id:'test',organization:'Example mission',status:'report-published',assessment:'Findings',url:'https://example.org/report',date:'2026-10-03'};legitimacy.validateObservers([observer]);assert.throws(()=>legitimacy.validateObservers([{...observer,url:''}]));model.validateWorldElection({...seedWorldElections[0],legitimacy:assessment,observers:[observer]});
console.log('Political context: nine-axis limits, combined ordering, missing values, party snapshots and sourced assessments passed.');

// Existing winner flags remain valid; runoff calls are distinct and mutually exclusive.
for(const advanced of [undefined,false,true])model.validateWorldElection({...seedWorldElections[0],results:[{...result,advanced}]});
assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],results:[{...result,advanced:'yes'}]}));
assert.throws(()=>model.validateWorldElection({...seedWorldElections[0],results:[{...result,winner:true,advanced:true}]}));

// Indirect and regional election metadata must remain optional for older records.
const regional={...seedWorldElections[0],electionMethod:'indirect',weightedVotes:true,geography:{id:'utrecht',name:'Utrecht',type:'province'},overviewId:'world-nl-provincial-2023',linkedElectionIds:['world-nl-eerste-kamer-2023'],results:[{...result,ballotVotes:10}]};
model.validateWorldElection(regional);
for(const patch of [{electionMethod:'unknown'},{weightedVotes:'yes'},{overviewId:regional.id},{linkedElectionIds:[regional.id]},{geography:{id:'',name:'Utrecht',type:'province'}},{results:[{...result,ballotVotes:-1}]}])assert.throws(()=>model.validateWorldElection({...regional,...patch}));

assert.equal(explore.coalitionEligible({...chamber,type:'parliamentary',countryId:'us',body:'U.S. Senate',results:[{seats:35}]}),false);assert.equal(explore.coalitionEligible({...chamber,type:'parliamentary',countryId:'us',body:'House of Representatives',results:[{seats:435}]}),true);assert.equal(explore.coalitionEligible({...chamber,type:'parliamentary',countryId:'nl',body:'Tweede Kamer',results:[{seats:150}]}),true);assert.equal(explore.coalitionEligible({...chamber,type:'parliamentary',countryId:'nl',totalSeats:null,results:[{seats:150}]}),false);
