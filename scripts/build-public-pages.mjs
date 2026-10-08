import fs from 'node:fs/promises';
import path from 'node:path';
import {educationCategories,educationCategory,publicEducation,readingMinutes} from '../lib/education.mjs';
import {siteHref} from '../src/routing.mjs';
import {staticPages,pageMetadata,latestTimestamp,electionMetadata} from '../lib/seo.mjs';

const origin='https://worldofelections.com';
const base=process.env.VITE_BASE_PATH||'/';
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=(route,label)=>`<a href="${escape(siteHref(route,base))}">${escape(label)}</a>`;
const sources=items=>items?.length?`<section><h2>Sources & further reading</h2>${items.filter(s=>{try{const u=new URL(s.url);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}}).map(s=>`<p><a href="${escape(s.url)}" rel="noreferrer">${escape(s.label)}</a></p>`).join('')}</section>`:'';
const paragraphs=text=>String(text||'').split(/\n\n/).filter(Boolean).map(p=>`<p>${escape(p)}</p>`).join('');
const legitimacyLabels={unassessed:'Unassessed',credible:'Credible / competitive',concerns:'Significant concerns',disputed:'Seriously disputed',uncompetitive:'Uncompetitive / restricted'};
const assessment=l=>l?`<section><h2>Election legitimacy</h2><strong>${escape(legitimacyLabels[l.level]||'Unassessed')}</strong>${paragraphs(l.summary)}<p>Our editorial assessment · reviewed ${escape(l.reviewed||'Not recorded')}</p>${(l.sources||[]).map(s=>`<p><a href="${escape(s.url)}" rel="noreferrer">${escape(s.label)}</a></p>`).join('')}</section>`:'';
const observers=items=>items?.length?`<section><h2>Election observers & reports</h2>${items.map(o=>`<h3>${escape(o.organization)}</h3><p>${escape(o.status)} · ${escape(o.date)}</p>${paragraphs(o.assessment)}${o.url?`<a href="${escape(o.url)}" rel="noreferrer">Observer report / source</a>`:''}`).join('')}</section>`:'';
// Anonymous public RPC only: no editor credentials, drafts or future scheduled posts.
const source=await fs.readFile('lib/supabase.ts','utf8');
const api=process.env.VITE_SUPABASE_URL||source.match(/const url.*?'(https:[^']+)'/)[1];
const key=process.env.VITE_SUPABASE_PUBLISHABLE_KEY||source.match(/const key.*?'(sb_publishable_[^']+)'/)[1];
const rows=[];
const pageSize=500;
for(let from=0;;from+=pageSize){
  const response=await fetch(api+`/rest/v1/rpc/ea_public_records?limit=${pageSize}&offset=${from}`,{method:'POST',headers:{apikey:key,'Content-Type':'application/json'},body:JSON.stringify({record_kinds:['article','world_country','world_election','senate']}),signal:AbortSignal.timeout(60000)});
  if(!response.ok)throw Error(`Public page generation failed (${response.status}); previous deployment stays live.`);
  const batch=await response.json();
  rows.push(...batch);
  if(batch.length<pageSize)break;
}
const now=Date.now();
const articles=rows.filter(r=>r.kind==='article'&&r.data.status==='published'&&!r.data.archived&&(!r.data.publishAt||Date.parse(r.data.publishAt)<=now)).map(r=>r.data).filter(a=>a.articleType!=='educational'||educationCategory(a.educationCategory));
const elections=rows.filter(r=>r.kind==='world_election'&&r.data.publication==='published').map(r=>r.data);
const countries=rows.filter(r=>r.kind==='world_country').map(r=>r.data);
const senate=rows.find(r=>r.kind==='senate'&&r.id==='senate-2026')?.data;
const updatedFor=items=>latestTimestamp(rows.filter(r=>items.some(x=>x.id===r.id)).map(r=>r.updated));
const dateLabel=e=>!e.startDate||e.precision==='unknown'?'Date not announced':e.precision==='year'?e.startDate.slice(0,4):e.precision==='month'?e.startDate.slice(0,7):e.startDate+(e.endDate&&e.endDate!==e.startDate?' – '+e.endDate:'');
const countryName=id=>countries.find(c=>c.id===id)?.name||id;
const electionLink=e=>link('/world/election/'+e.id,e.title);
const articleRoute=a=>(a.articleType==='ideology'?'/ideologies/':a.articleType==='educational'?'/education/':'/article/')+a.id;
const articleLink=a=>link(articleRoute(a),a.title);
const nav=`<div class="utility">Independent election coverage</div><header><a class="masthead" href="${base}">World of Elections</a></header><nav aria-label="Main navigation">${link('/','Home')}${link('/live-elections','Live Elections')}${link('/senate','U.S. Senate')}${link('/house','U.S. House')}${link('/calendar','Election calendar')}${link('/archive','Election archive')}${link('/education','Education')}${link('/ideologies','Ideologies')}</nav>`;
const template=await fs.readFile('dist/index.html','utf8');
const entries=[];
const cleanTemplate=template.replace(/<title>[^<]*<\/title>/,'').replace(/<meta name="description"[^>]*\/?\s*>/,'');
async function page(route,title,description,body,index=true,updated='',details={}){
  if(!/^\/(?:[a-zA-Z0-9_-]+\/?)*$/.test(route))throw Error('Invalid public page route.');
  const {seo,...metadataDetails}=details;
  const meta=pageMetadata({route,title,description,index,updated,base,...metadataDetails,...seo});
  const html=cleanTemplate.replace('</head>',meta.head+'</head>')
    .replace('<div id="root"></div>',`<div id="root">${nav}<main class="articlepage"><h1>${escape(title)}</h1>${body}</main></div>`);
  const dir=route==='/'?'dist':path.join('dist',route.slice(1));
  await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'index.html'),html);
  if(index)entries.push({url:meta.url,updated});
}
const news=articles.filter(a=>a.articleType!=='ideology'&&a.articleType!=='educational');
const educationals=publicEducation(articles);
const educationList=items=>items.length?`<ul>${items.map(a=>`<li>${articleLink(a)}${paragraphs(a.summary)}<p>${readingMinutes(a)} min read</p></li>`).join('')}</ul>`:'<p>Educationals will appear here as they are published.</p>';
const educationDirectory=()=>`<section><h2>Educational topics</h2>${educationCategories.map(c=>`<h3>${link('/education/category/'+c.id,c.name)}</h3>${paragraphs(c.description)}`).join('')}</section>`;
const guides=articles.filter(a=>a.articleType==='ideology');
const directory=()=>`<section><h2>Country election directory</h2><ul>${[...countries].sort((a,b)=>a.name.localeCompare(b.name)).map(c=>`<li>${link('/archive/country/'+c.id,c.name+' elections')}</li>`).join('')}</ul></section>`;
const electionList=items=>`<ul>${[...items].filter(e=>!e.overviewId).sort((a,b)=>(a.startDate||'9999').localeCompare(b.startDate||'9999')).map(e=>`<li>${escape(countryName(e.countryId))} · ${electionLink(e)}<p>${escape(dateLabel(e))} · ${escape(e.status)} · ${escape(e.dateStatus)}</p></li>`).join('')}</ul>`;
for(const [route,{title,description}]of Object.entries(staticPages)){
  let items=[],body=paragraphs(description);
  if(route==='/'){
    items=[...news,...elections];body+=`<h2>Latest coverage</h2><ul>${news.map(a=>`<li>${articleLink(a)}${paragraphs(a.summary)}</li>`).join('')}</ul><h2>Explore our coverage</h2><ul>${Object.entries(staticPages).filter(([r])=>r!=='/').map(([r,m])=>`<li>${link(r,m.title)}</li>`).join('')}</ul>`;
  }else if(route==='/education'){
    items=educationals;body+=educationDirectory()+`<h2>Our educationals</h2>${educationList(educationals)}<h2>Our ideology library</h2>${link('/ideologies','Explore political ideologies')}`;
  }else if(route==='/ideologies'){
    items=guides;body+=`<ul>${guides.map(a=>`<li>${articleLink(a)}${paragraphs(a.summary)}</li>`).join('')}</ul>`;
  }else if(['/archive','/calendar','/live-elections'].includes(route)){
    items=elections.filter(e=>route==='/archive'?e.status==='held':route==='/calendar'?e.status!=='held':e.live?.enabled);
    body+=electionList(items)+(route==='/archive'?directory():'');
    if(route==='/archive')items=[...items,...countries];
  }else if(route==='/municipalities/netherlands'){
    const municipal=JSON.parse(await fs.readFile('public/nl-municipal-2023-2025.json','utf8'));
    body+=`<p>Full official municipal results for 22 November 2023 and 29 October 2025. Interactive layers show party winners, first-versus-second margins, population circles and changes in the left–right vote balance. Each year has a standalone results view; 2025 also offers comparison with 2023. Our fixed international classifications place D66 and Volt in the centre.</p><h2>Municipalities</h2><ul>${municipal.municipalities.map(m=>`<li>${escape(m.name)} · ${escape(m.population)} residents (1 January 2025)</li>`).join('')}</ul>${sources(municipal.sources)}`;
  }else if(route==='/atlas'){
    items=[...countries,...elections];body+=directory();
  }else if(['/compare','/coalitions'].includes(route)){
    items=elections.filter(e=>route==='/compare'?e.status==='held':e.type==='parliamentary'&&e.results?.some(r=>r.seats!=null));
    body+=`<h2>Recorded elections</h2>${electionList(items)}`;
  }else if(route==='/senate'&&senate){
    items=[senate];body+=`<h2>Senate races</h2><ul>${senate.races.map(r=>`<li><h3>${escape(r.state)}${r.special?' · Special election':''}</h3><p>Incumbent: ${escape(r.incumbentName||r.incumbent)}</p><ul>${r.candidates.map(c=>`<li>${escape(c.name)} · ${escape(c.party)}</li>`).join('')}</ul>${paragraphs(r.notes)}</li>`).join('')}</ul>`;
  }else if(route==='/house'){
    items=elections.filter(e=>e.id==='world-us-house-2026');body+=electionList(items);
    const house=items[0]?.house;if(house)body+=paragraphs(house.notes)+`<h2>Reported House seats</h2><p>Democratic: ${escape(house.results.D)} · Republican: ${escape(house.results.R)} · Other: ${escape(house.results.O)} · ${escape(house.results.status)}</p><h2>District coverage</h2><ul>${house.races.map(r=>`<li>${escape(r.district)}: ${r.candidates.map(c=>escape(c.name)+' ('+escape(c.party)+')').join(', ')}</li>`).join('')}</ul>`;
  }else if(route==='/us-election-night'){
    items=[...(senate?[senate]:[]),...elections.filter(e=>e.id==='world-us-house-2026')];body+=`<p>${link('/senate','U.S. Senate polling and results')} · ${link('/house','U.S. House polling and results')}</p>`;
  }
  await page(route,title,description,body,true,updatedFor(items));
}
for(const a of articles){
  const related=elections.find(e=>e.id===a.electionId);
  const body=a.articleType==='ideology'?Object.entries({definition:'At a glance',principles:'Core principles',history:'Origins & development',economics:'Economic outlook',society:'Society & government',variants:'Variations & related traditions',criticisms:'Debates & criticisms'}).filter(([name])=>a.sections?.[name]).map(([name,label])=>`<section id="${name}"><h2>${label}</h2>${name==='principles'?`<ul>${a.sections[name].split('\n').filter(Boolean).map(p=>`<li>${escape(p)}</li>`).join('')}</ul>`:paragraphs(a.sections[name])}</section>`).join(''):paragraphs(a.body)+(a.articleType==='educational'?(a.sections||[]).map((section,i)=>`<section id="lesson-section-${i}"><h2>${escape(section.title)}</h2>${paragraphs(section.body)}</section>`).join(''):'');
  const educationCategoryInfo=a.articleType==='educational'?educationCategory(a.educationCategory):null;
  const educationIntro=educationCategoryInfo?`<p>${link('/education','Education')} · ${link('/education/category/'+educationCategoryInfo.id,educationCategoryInfo.name)} · ${readingMinutes(a)} min read</p>`:'';
  await page(articleRoute(a),a.title,a.summary,educationIntro+`<p class="standfirst">${escape(a.summary)}</p><p class="meta">By ${escape(a.author)} · ${escape(a.date)}</p><div class="articlebody">${body}</div>${sources(a.sources)}${related?`<aside class="article-election-link"><h2>Related election</h2>${electionLink(related)}</aside>`:''}`,true,updatedFor([a]),{article:a,breadcrumbs:[...(a.articleType==='ideology'?[{name:'Ideologies',route:'/ideologies'}]:educationCategoryInfo?[{name:'Education',route:'/education'},{name:educationCategoryInfo.name,route:'/education/category/'+educationCategoryInfo.id}]:[]),{name:a.title,route:articleRoute(a)}]});
}
for(const category of educationCategories){
 const items=educationals.filter(a=>a.educationCategory===category.id);
 await page('/education/category/'+category.id,category.name+' — Education',category.description,`<p>${link('/education','All educationals')}</p>${paragraphs(category.description)}${educationList(items)}${category.id==='parties-ideology'?link('/ideologies','Explore our ideology library'):''}`,items.length>0,updatedFor(items),{breadcrumbs:[{name:'Education',route:'/education'},{name:category.name,route:'/education/category/'+category.id}]});
}
const presidentialMaps=JSON.parse(await fs.readFile('public/us-presidential-electoral.json','utf8').catch(()=> '{}'));
for(const e of elections){
  const electoral=e.countryId==='us'&&e.type==='presidential'?presidentialMaps[e.id]:null;
  const electoralHtml=electoral?`<section><h2>Electoral map — ${electoral.year===1789?'1788–89':electoral.year}</h2><p>${electoral.electors} electors; ${electoral.majority} votes required for an electoral majority. Modern state outlines are a geographic reference, not historical borders. The interactive map shows actual counted electoral votes, including split and faithless votes.</p><table><caption>Historical electoral allocations by state</caption><thead><tr><th>State</th><th>Electors</th><th>Electoral vote recipients</th></tr></thead><tbody>${electoral.states.map(state=>`<tr><th>${escape(state.name)}</th><td>${state.electors}</td><td>${Object.entries(state.votes).map(([id,n])=>escape(electoral.candidates.find(c=>c.id===id)?.name||id)+' '+n).join('; ')}${state.unallocated?'; '+state.unallocated+' uncast / rejected':''}</td></tr>`).join('')}</tbody></table></section>`:'';
  const contestsHtml=e.contests?.length?`<section><h2>State races and results map</h2><p>Each race has its own denominator. Missing counts are blank. The interactive map uses modern state outlines as navigation references.</p>${e.contests.map(c=>`<section><h3>${escape(c.stateName)} — ${escape(c.title)} — ${escape(c.round)}</h3><p>${c.method==='indirect'?'Legislative / indirect selection':'Popular election'}. ${escape(c.voteBasis)}</p><table><thead><tr><th>Candidate</th><th>Party</th><th>Votes</th><th>Share</th><th>Result</th></tr></thead><tbody>${c.results.map(r=>`<tr><th>${escape(r.name)}</th><td>${escape(r.party)}</td><td>${escape(r.votes??'—')}</td><td>${r.share==null?'—':escape(r.share.toFixed(2))+'%'}</td><td>${r.winner?'Elected':r.advanced?'Advancing to runoff':'—'}</td></tr>`).join('')}</tbody></table>${paragraphs(c.notes)}${sources(c.sources)}</section>`).join('')}</section>`:'';
  const body=`<p>${link('/archive/country/'+e.countryId,countryName(e.countryId)+' elections')} · ${escape(dateLabel(e))} · ${escape(e.status)}</p>${paragraphs(e.summary)}${electoralHtml}${contestsHtml}${e.electionMethod==='indirect'?'<p><strong>Indirect election</strong> — selection through an electoral body rather than a direct national popular vote. The record notes explain the selection process.</p>':''}${e.overviewId?`<p>${link('/world/election/'+e.overviewId,'View election overview')}</p>`:''}${e.regionalOverview?`<h2>Regional results</h2><ul>${elections.filter(x=>x.overviewId===e.id).map(x=>`<li>${link('/world/election/'+x.id,x.geography?.name||x.title)}</li>`).join('')}</ul>`:''}${e.linkedElectionIds?.length?`<h2>Related elections</h2><ul>${elections.filter(x=>e.linkedElectionIds.includes(x.id)).map(x=>`<li>${electionLink(x)}</li>`).join('')}</ul>`:''}<p>Results: ${escape(e.resultStatus)} · ${escape(e.resultCoverage)} coverage · ${escape(e.voteBasis||'')}</p>${e.turnout!=null?`<p>${e.electionMethod==='indirect'?'Elector participation':'Turnout'}: ${escape(e.turnout)}%</p>`:''}${e.results?.length?`<table><caption>${escape(e.title)} — recorded results</caption><thead><tr><th scope="col">Party / candidate</th><th scope="col">${e.weightedVotes?'Weighted votes':e.electionMethod==='indirect'?'Elector ballots':'Votes'}</th><th scope="col">${e.weightedVotes?'Weighted vote share':e.electionMethod==='indirect'?'Elector ballot share':'Vote share'}</th><th scope="col">Seats</th><th scope="col">Electoral votes</th></tr></thead><tbody>${e.results.map(r=>`<tr><th scope="row">${escape(r.name)}</th><td>${escape(r.votes??'—')}</td><td>${escape(r.share!=null?r.share+'%':'—')}</td><td>${escape(r.seats??'—')}</td><td>${escape(r.electoralVotes??'—')}</td></tr>`).join('')}</tbody></table>`:''}${paragraphs(e.government)}${paragraphs(e.notes)}${assessment(e.legitimacy)}${observers(e.observers)}${sources(e.sources)}`;
  await page('/world/election/'+e.id,electoral?`United States presidential election ${electoral.year===1789?'1788–89':electoral.year} — Results & electoral map`:e.title,[countryName(e.countryId),dateLabel(e),e.status==='held'?e.resultStatus+' election results':e.dateStatus+' election timing',e.summary].filter(Boolean).join(' · '),body,true,updatedFor([e]),{seo:electionMetadata(e,countryName(e.countryId)),breadcrumbs:[{name:'Election archive',route:'/archive'},{name:countryName(e.countryId),route:'/archive/country/'+e.countryId},{name:e.title,route:'/world/election/'+e.id}]});
}
for(const c of countries){
  const items=elections.filter(e=>e.countryId===c.id);
  const index=items.length>0||!!(c.legitimacy?.level&&c.legitimacy.level!=='unassessed'&&c.legitimacy.summary?.trim());
  await page('/archive/country/'+c.id,c.name+' elections — Results & timeline',`Browse ${c.name}'s recorded elections, historical results, upcoming election dates and our country election coverage.`,`${paragraphs(c.coverageNote)}${assessment(c.legitimacy)}<h2>Election timeline</h2>${items.length?electionList(items):'<p>Historical elections have not been entered for this country yet.</p>'}`,index,updatedFor([c,...items]),{breadcrumbs:[{name:'Election archive',route:'/archive'},{name:c.name,route:'/archive/country/'+c.id}]});
}
for(const route of ['/account','/editor','/editor/world','/editor/senate','/editor/house','/editor/ideologies','/editor/education','/election-night'])await page(route,route==='/account'?'Your account':'World of Elections','World of Elections.', '<p>Loading…</p>',false);
await fs.writeFile('dist/404.html',cleanTemplate.replace('</head>',pageMetadata({route:'/404',title:'Page not found',description:'This page is unavailable. Browse our election coverage, calendar and archive.',index:false,base}).head+'</head>').replace('<div id="root"></div>','<div id="root"><main><h1>Page not found</h1><p>Loading election coverage…</p></main></div>'));
const sitemap=`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries.map(({url,updated})=>`<url><loc>${escape(url)}</loc>${updated&&Number.isFinite(Date.parse(updated))?`<lastmod>${new Date(updated).toISOString()}</lastmod>`:''}</url>`).join('\n')}</urlset>\n`;
await fs.writeFile('dist/sitemap.xml',sitemap);
await fs.writeFile('dist/robots.txt',`User-agent: *\nAllow: /\nSitemap: ${origin+base}sitemap.xml\n`);
await fs.writeFile('dist/CNAME','worldofelections.com\n');
console.log(`Generated ${entries.length} indexable public pages and sitemap; ${news.length} public articles, ${elections.length} public elections. Private content excluded.`);
