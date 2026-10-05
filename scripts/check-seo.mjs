import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {pageMetadata,staticPages,canonicalUrl,descriptionText,electionMetadata} from '../lib/seo.mjs';

const schema=html=>JSON.parse(html.match(/<script id="page-schema" type="application\/ld\+json">(.*?)<\/script>/s)[1]);
test('Search metadata has stable canonical URLs, distinct descriptions and safe JSON-LD',()=>{
 assert.equal(canonicalUrl('/calendar?month=2026-10#results'), 'https://worldofelections.com/calendar/');
 assert.equal(canonicalUrl('/calendar','/ElectionAtlas/'),'https://worldofelections.com/ElectionAtlas/calendar/');
 assert.equal(new Set(Object.values(staticPages).map(p=>p.description)).size,Object.keys(staticPages).length);
 assert.ok(descriptionText('word '.repeat(100)).length<=180);
 const title='A </script><script>alert(1)</script> & B';
 const {head}=pageMetadata({route:'/article/test',title,description:'A story',updated:'2026-10-01T12:00:00Z',article:{title,author:'World of Elections',category:'Election coverage',date:'2026-10-01'}});
 assert.equal((head.match(/<script /g)||[]).length,1);
 const graph=schema(head)['@graph'];
 const story=graph.find(x=>x['@type']==='NewsArticle');
 assert.equal(story.headline,title);assert.equal(story.datePublished,'2026-10-01T00:00:00.000Z');
 assert.equal(story.dateModified,'2026-10-01T12:00:00.000Z');
 assert.match(head,/og:image" content="https:\/\/worldofelections.com\/social-card.png"/);
 assert.ok(!head.includes('SearchAction')); // There is no standalone site-search URL.
});

test('Election metadata uses structured country, dates and results without changing records',()=>{
 const election={title:'Federal Senate',type:'parliamentary',startDate:'2026-10-04',precision:'day',resultStatus:'provisional',resultCoverage:'partial',totalSeats:81,results:[{name:'Party',share:0,seats:0}]};
 const before=JSON.stringify(election);
 const meta=electionMetadata(election,'Brazil');
 assert.equal(meta.title,'2026 Brazil Federal Senate | World of Elections');
 for(const detail of ['Brazil','2026','parliamentary','2026-10-04','Provisional results (partial coverage)','81 seats','1 parties / lists'])assert.ok(meta.description.includes(detail),detail);
 assert.equal(JSON.stringify(election),before);
 for(const title of ['Brazil Federal Senate 2026','2026 BRAZIL Federal Senate','Federal Senate · 2026'])assert.equal(electionMetadata({...election,title},'Brazil').title,meta.title);
 assert.equal(electionMetadata({...election,title:'2026 Netherlands Tweede Kamer'},'Netherlands').title,'2026 Netherlands Tweede Kamer | World of Elections');
 assert.equal(electionMetadata({...election,title:'Côte d’Ivoire National Assembly'},'Côte d’Ivoire').title,'2026 Côte d’Ivoire National Assembly | World of Elections');
 assert.equal(electionMetadata({...election,title:'2026–2027 National Assembly',endDate:'2027-01-02'},'Example').title,'2026–2027 Example National Assembly | World of Elections');
 assert.match(electionMetadata({...election,title:'District 20260'},'Example').title,/District 20260/);
 const unknown=electionMetadata({title:'President',type:'presidential',precision:'unknown',results:[]},'Example');
 assert.equal(unknown.title,'Example President | World of Elections');assert.match(unknown.description,/Date not announced/);assert.ok(!unknown.description.includes('results'));
 const yearly=electionMetadata({...election,precision:'year'},'Example');assert.ok(!yearly.description.includes('2026-10-04'));
 const head=pageMetadata({route:'/world/election/example',...meta}).head;
 assert.match(head,/<title>2026 Brazil Federal Senate \| World of Elections<\/title>/);
 assert.match(head,/og:title" content="2026 Brazil Federal Senate \| World of Elections"/);
 assert.ok(electionMetadata({...election,title:'Very long chamber name '.repeat(20)},'Example').description.length<=180);
});

test('Generated HTML protects unpublished content and indexes only substantive country profiles',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'electionatlas-seo-'));
 try{
  await fs.mkdir(path.join(dir,'dist'));await fs.mkdir(path.join(dir,'lib'));await fs.mkdir(path.join(dir,'public'));
  await fs.writeFile(path.join(dir,'public/nl-municipal-2023-2025.json'),JSON.stringify({municipalities:[{name:'Amsterdam',population:934526}],sources:[{label:'Kiesraad municipal results',url:'https://www.verkiezingsuitslagen.nl/'}]}));
  await fs.writeFile(path.join(dir,'lib/supabase.ts'),"const url='https://example.invalid';const key='sb_publishable_test';");
  await fs.writeFile(path.join(dir,'dist/index.html'),'<!doctype html><html lang="en"><head><title>Old title</title><meta name="description" content="Old"/><link rel="stylesheet" href="/assets/style.css"/></head><body><div id="root"></div><script type="module" src="/assets/main.js"></script></body></html>');
  const row=(kind,data,updated='2026-10-02T12:00:00Z')=>({kind,id:data.id,data,updated});
  const article={id:'public-story',title:'Public coverage',status:'published',summary:'A public summary',body:'A public report',author:'World of Elections',date:'2026-10-01'};
  const election={id:'world-test',countryId:'test',title:'Test election',publication:'published',type:'parliamentary',status:'held',startDate:'2026-01-01',precision:'year',resultStatus:'provisional',resultCoverage:'partial',voteBasis:'National vote share',results:[{name:'Party',votes:0,share:0,seats:0,electoralVotes:null}],sources:[{label:'Election commission',url:'https://example.org/results'}]};
  const history={...election,id:'world-us-president-2024',countryId:'us',title:'President',type:'presidential',startDate:'2024-11-05',precision:'day'};
  await fs.writeFile(path.join(dir,'public/us-presidential-electoral.json'),JSON.stringify({[history.id]:{year:2024,electors:538,majority:270,states:[{name:'Maine',electors:4,votes:{harris:3,trump:1},unallocated:0}],candidates:[{id:'harris',name:'Kamala Harris'},{id:'trump',name:'Donald Trump'}]}}));
  const rows=[row('world_election',history),row('world_country',{id:'us',name:'United States',coverageNote:'Presidential history.'}),row('article',article),row('article',{...article,id:'draft-secret',title:'DRAFT_SECRET',status:'draft'}),row('article',{...article,id:'future-secret',title:'FUTURE_SECRET',publishAt:'2099-01-01T00:00:00Z'}),row('article',{...article,id:'archived-secret',title:'ARCHIVED_SECRET',archived:true}),row('world_election',election),row('world_election',{...election,id:'world-draft',title:'ELECTION_SECRET',publication:'draft'}),row('world_country',{id:'test',name:'Testland',coverageNote:'Our coverage.'},'2026-10-03T12:00:00Z'),row('world_country',{id:'empty',name:'Emptyland',coverageNote:'Coverage is expanding.'}),row('world_country',{id:'assessed',name:'Assessedland',coverageNote:'',legitimacy:{level:'concerns',summary:'A sourced assessment.',sources:[]}}),row('article',{...article,id:'ideology-test',articleType:'ideology',title:'Example ideology',sections:{definition:'Definition',principles:'First\nSecond'},sources:[{label:'Source',url:'https://example.org/ideology'}],scores:{socialistCapitalist:'PRIVATE_SCORE_SECRET'}})];
  const entry=pathToFileURL(path.resolve('scripts/build-public-pages.mjs')).href;
  const code=`globalThis.fetch=async(url,options)=>{const kinds=JSON.parse(options.body).record_kinds;if(kinds.includes('ideology_axes'))throw Error('Private data requested');return {ok:true,json:async()=>${JSON.stringify(rows)}}};await import(${JSON.stringify(entry)});`;
  const result=spawnSync(process.execPath,['--input-type=module','-e',code],{cwd:dir,env:{...process.env,VITE_BASE_PATH:'/',VITE_SUPABASE_URL:'https://example.invalid',VITE_SUPABASE_PUBLISHABLE_KEY:'sb_publishable_test'},encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const sitemap=await fs.readFile(path.join(dir,'dist/sitemap.xml'),'utf8');
  for(const secret of ['draft-secret','future-secret','archived-secret','world-draft','/account/','/editor/','/country/empty/'])assert.ok(!sitemap.includes(secret),secret);
  assert.ok(sitemap.includes('/municipalities/netherlands/'));
  const municipal=await fs.readFile(path.join(dir,'dist/municipalities/netherlands/index.html'),'utf8');assert.match(municipal,/Amsterdam/);assert.match(municipal,/934526/);
  assert.ok(sitemap.includes('/archive/country/test/'));assert.ok(sitemap.includes('/archive/country/assessed/'));
  const country=await fs.readFile(path.join(dir,'dist/archive/country/test/index.html'),'utf8');
  assert.match(country,/2026-10-03T12:00:00.000Z/);assert.match(country,/world\/election\/world-test\//);
  const empty=await fs.readFile(path.join(dir,'dist/archive/country/empty/index.html'),'utf8');assert.match(empty,/noindex,follow/);
  const page=await fs.readFile(path.join(dir,'dist/world/election/world-test/index.html'),'utf8');
  assert.match(page,/<title>2026 Testland Test election \| World of Elections<\/title>/);assert.match(page,/<h1>Test election<\/h1>/);assert.match(page,/name="description" content="2026 Testland parliamentary election/);
  assert.ok(page.includes('https://example.org/results'));assert.match(page,/>0%<\/td>/);assert.match(page,/Testland elections<\/a> · 2026 · held/);assert.ok(!page.includes('2026-01-01'));
  const presidential=await fs.readFile(path.join(dir,'dist/world/election/world-us-president-2024/index.html'),'utf8');assert.match(presidential,/United States presidential election 2024/);assert.match(presidential,/Historical electoral allocations by state/);assert.match(presidential,/Kamala Harris 3; Donald Trump 1/);
  const guide=await fs.readFile(path.join(dir,'dist/ideologies/ideology-test/index.html'),'utf8');
  assert.ok(!guide.includes('PRIVATE_SCORE_SECRET'));assert.match(guide,/<li>First<\/li><li>Second<\/li>/);assert.ok(schema(guide)['@graph'].some(x=>x['@type']==='DefinedTerm'));
  const home=await fs.readFile(path.join(dir,'dist/index.html'),'utf8');
  for(const secret of ['DRAFT_SECRET','FUTURE_SECRET','ARCHIVED_SECRET','ELECTION_SECRET','PRIVATE_SCORE_SECRET'])assert.ok(!home.includes(secret));
  assert.equal((home.match(/<title>/g)||[]).length,1);assert.equal((home.match(/name="description"/g)||[]).length,1);
  assert.ok(home.includes('/assets/style.css'));assert.ok(home.includes('/assets/main.js'));
  for(const route of ['account/index.html','editor/index.html','404.html'])assert.match(await fs.readFile(path.join(dir,'dist',route),'utf8'),/noindex,follow/);
 }finally{await fs.rm(dir,{recursive:true,force:true});}
});
