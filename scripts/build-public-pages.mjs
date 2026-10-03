import fs from 'node:fs/promises';
import path from 'node:path';
import {siteHref} from '../src/routing.mjs';

const origin='https://worldofelections.com';
const base=process.env.VITE_BASE_PATH||'/';
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=(route,label)=>`<a href="${escape(siteHref(route,base))}">${escape(label)}</a>`;
const paragraphs=text=>String(text||'').split(/\n\n/).filter(Boolean).map(p=>`<p>${escape(p)}</p>`).join('');
const legitimacyLabels={unassessed:'Unassessed',credible:'Credible / competitive',concerns:'Significant concerns',disputed:'Seriously disputed',uncompetitive:'Uncompetitive / restricted'};
const assessment=l=>l?`<section><h2>Election legitimacy</h2><strong>${escape(legitimacyLabels[l.level]||'Unassessed')}</strong>${paragraphs(l.summary)}<p>Our editorial assessment · reviewed ${escape(l.reviewed||'Not recorded')}</p>${(l.sources||[]).map(s=>`<p><a href="${escape(s.url)}" rel="noreferrer">${escape(s.label)}</a></p>`).join('')}</section>`:'';
const observers=items=>items?.length?`<section><h2>Election observers & reports</h2>${items.map(o=>`<h3>${escape(o.organization)}</h3><p>${escape(o.status)} · ${escape(o.date)}</p>${paragraphs(o.assessment)}${o.url?`<a href="${escape(o.url)}" rel="noreferrer">Observer report / source</a>`:''}`).join('')}</section>`:'';
// Anonymous public RPC only: no editor credentials, drafts or future scheduled posts.
const source=await fs.readFile('lib/supabase.ts','utf8');
const api=process.env.VITE_SUPABASE_URL||source.match(/const url.*?'(https:[^']+)'/)[1];
const key=process.env.VITE_SUPABASE_PUBLISHABLE_KEY||source.match(/const key.*?'(sb_publishable_[^']+)'/)[1];
const response=await fetch(api+'/rest/v1/rpc/ea_public_records',{method:'POST',headers:{apikey:key,'Content-Type':'application/json'},body:JSON.stringify({record_kinds:['article','world_country','world_election']})});
if(!response.ok)throw Error(`Public page generation failed (${response.status}); previous deployment stays live.`);
const rows=await response.json();
const now=Date.now();
const articles=rows.filter(r=>r.kind==='article'&&r.data.status==='published'&&!r.data.archived&&(!r.data.publishAt||Date.parse(r.data.publishAt)<=now)).map(r=>r.data);
const elections=rows.filter(r=>r.kind==='world_election'&&r.data.publication==='published').map(r=>r.data);
const countries=rows.filter(r=>r.kind==='world_country').map(r=>r.data);
const countryName=id=>countries.find(c=>c.id===id)?.name||id;
const electionLink=e=>link('/world/election/'+e.id,e.title);
const articleLink=a=>link((a.articleType==='ideology'?'/ideologies/':'/article/')+a.id,a.title);
const nav=`<div class="utility">Independent election coverage</div><header><a class="masthead" href="${base}">World of Elections</a></header><nav aria-label="Main navigation">${link('/','Home')}${link('/live-elections','Live Elections')}${link('/senate','U.S. Senate')}${link('/house','U.S. House')}${link('/calendar','Election calendar')}${link('/archive','Election archive')}${link('/ideologies','Ideologies')}</nav>`;
const template=await fs.readFile('dist/index.html','utf8');
const entries=[];
async function page(route,title,description,body,index=true,updated=''){
  if(!/^\/(?:[a-zA-Z0-9_-]+\/?)*$/.test(route))throw Error('Invalid public page route.');
  const url=origin+siteHref(route,base);
  let html=template.replace(/<title>[^<]*<\/title>/,`<title>${escape(title)}${route==='/'?'':' · World of Elections'}</title>`)
    .replace(/<meta name="description"[^>]*\/>/,`<meta name="description" content="${escape(description)}"/>`)
    .replace('</head>',`${index?`<link rel="canonical" href="${escape(url)}"/>`:'<meta name="robots" content="noindex,follow"/>'}<meta property="og:title" content="${escape(title)}"/><meta property="og:description" content="${escape(description)}"/><meta property="og:url" content="${escape(url)}"/></head>`)
    .replace('<div id="root"></div>',`<div id="root">${nav}<main class="articlepage"><h1>${escape(title)}</h1>${body}</main></div>`);
  const dir=route==='/'?'dist':path.join('dist',route.slice(1));
  await fs.mkdir(dir,{recursive:true});await fs.writeFile(path.join(dir,'index.html'),html);
  if(index)entries.push({url,updated});
}
const titles={'/':'World of Elections','/live-elections':'Live Elections','/senate':'U.S. Senate elections 2026','/house':'U.S. House elections 2026','/calendar':'Election calendar','/archive':'Election archive','/ideologies':'Ideologies','/atlas':'World election atlas','/compare':'Then versus now','/coalitions':'Coalition builder','/us-election-night':'U.S. Election Night'};
const news=articles.filter(a=>a.articleType!=='ideology');
for(const [route,title]of Object.entries(titles)){
  const body=route==='/'?`<p>Independent election coverage, analysis, and results.</p><h2>Latest coverage</h2><ul>${news.map(a=>`<li>${articleLink(a)}${paragraphs(a.summary)}</li>`).join('')}</ul>`:
    route==='/ideologies'?`<ul>${articles.filter(a=>a.articleType==='ideology').map(a=>`<li>${articleLink(a)}</li>`).join('')}</ul>`:
    route==='/archive'||route==='/calendar'||route==='/live-elections'?`<ul>${elections.filter(e=>route==='/archive'?e.status==='held':route==='/calendar'?e.status==='scheduled':e.live?.enabled).map(e=>`<li>${escape(countryName(e.countryId))} · ${electionLink(e)}</li>`).join('')}</ul>`:
    '<p>Explore our election coverage, polling and results.</p>';
  await page(route,title,'Election coverage, polling, analysis and results from World of Elections.',body);
}
for(const a of articles){
  const related=elections.find(e=>e.id===a.electionId);
  const body=a.articleType==='ideology'?Object.entries(a.sections||{}).map(([name,text])=>`<h2>${escape(name)}</h2>${paragraphs(text)}`).join(''):paragraphs(a.body);
  await page((a.articleType==='ideology'?'/ideologies/':'/article/')+a.id,a.title,a.summary,`<p class="standfirst">${escape(a.summary)}</p><p class="meta">By ${escape(a.author)} · ${escape(a.date)}</p><div class="articlebody">${body}</div>${related?`<aside class="article-election-link"><h2>Related election</h2>${electionLink(related)}</aside>`:''}`,true,rows.find(r=>r.data.id===a.id)?.updated);
}
for(const e of elections){
  const body=`<p>${escape(countryName(e.countryId))} · ${escape(e.startDate||'Date not announced')} · ${escape(e.status)}</p>${paragraphs(e.summary)}${e.results?.length?`<table><thead><tr><th>Party / candidate</th><th>Votes</th><th>Vote share</th><th>Seats</th></tr></thead><tbody>${e.results.map(r=>`<tr><td>${escape(r.name)}</td><td>${escape(r.votes??'—')}</td><td>${escape(r.share??'—')}</td><td>${escape(r.seats??'—')}</td></tr>`).join('')}</tbody></table>`:''}${paragraphs(e.government)}${paragraphs(e.notes)}${assessment(e.legitimacy)}${observers(e.observers)}`;
  await page('/world/election/'+e.id,e.title,e.summary||e.title,body,true,rows.find(r=>r.data.id===e.id)?.updated);
}
for(const c of countries)await page('/archive/country/'+c.id,c.name+' elections',c.coverageNote||'Election history and upcoming elections.',`${paragraphs(c.coverageNote)}${assessment(c.legitimacy)}<ul>${elections.filter(e=>e.countryId===c.id).map(e=>`<li>${electionLink(e)}</li>`).join('')}</ul>`);
for(const route of ['/account','/editor','/editor/world','/editor/senate','/editor/house','/editor/ideologies','/election-night'])await page(route,route==='/account'?'Your account':'World of Elections','World of Elections.', '<p>Loading…</p>',false);
await fs.writeFile('dist/404.html',template.replace('</head>','<meta name="robots" content="noindex,follow"/></head>').replace('<div id="root"></div>','<div id="root"><main><h1>Page not found</h1><p>Loading election coverage…</p></main></div>'));
const sitemap=`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries.map(({url,updated})=>`<url><loc>${escape(url)}</loc>${updated&&Number.isFinite(Date.parse(updated))?`<lastmod>${new Date(updated).toISOString()}</lastmod>`:''}</url>`).join('\n')}</urlset>\n`;
await fs.writeFile('dist/sitemap.xml',sitemap);
await fs.writeFile('dist/robots.txt',`User-agent: *\nAllow: /\nSitemap: ${origin+base}sitemap.xml\n`);
await fs.writeFile('dist/CNAME','worldofelections.com\n');
console.log(`Generated ${entries.length} public pages and sitemap; ${news.length} public articles, ${elections.length} public elections. Private content excluded.`);
