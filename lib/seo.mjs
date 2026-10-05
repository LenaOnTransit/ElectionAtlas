import {siteHref} from '../src/routing.mjs';

export const siteOrigin='https://worldofelections.com';
export const siteName='World of Elections';
export const staticPages={
 '/':{title:'World of Elections — Election results, calendars & analysis',description:'Follow national elections with our election calendar, historical results, interactive world atlas, political ideology guides and U.S. election coverage.'},
 '/live-elections':{title:'Live election results & counting updates',description:'Follow elections featured by our desk, with reported vote shares, seats, counting updates and links to full election records and sources.'},
 '/senate':{title:'2026 U.S. Senate elections — Our polling & results',description:'Explore our coverage of the 2026 U.S. Senate elections: candidates, race ratings, our polling, reported results and the balance of Senate control.'},
 '/house':{title:'2026 U.S. House elections — Our polling & results',description:'Track the 2026 U.S. House elections with our race ratings, district coverage, polling and reported results for control of the House.'},
 '/calendar':{title:'World election calendar — Upcoming national elections',description:'Browse upcoming parliamentary and presidential elections by country, month and region, with confirmed dates, expected timing and source links.'},
 '/archive':{title:'Historical election results — World election archive',description:'Explore archived parliamentary and presidential election results by country and year, including vote shares, seats, sources and election timelines.'},
 '/education':{title:'Education — Elections, voting & government explained',description:'Learn how elections, voting systems, districts, parties, polling and government work through our educational explainers and political ideology guides.'},
 '/ideologies':{title:'Political ideologies — Definitions, history & principles',description:'Explore political ideology guides covering core principles, origins, economic outlooks, government, related traditions and debates, with sources.'},
 '/atlas':{title:'World election atlas — Elections & legitimacy',description:'Explore our interactive world atlas for election coverage, upcoming national elections and country election legitimacy assessments.'},
 '/municipalities/netherlands':{title:'Dutch municipal election map — Tweede Kamer 2023 and 2025',description:'Compare Dutch parliamentary election results in all 342 municipalities: party winners, winning margins, population-sized circles and optional 2025 comparisons with 2023.'},
 '/compare':{title:'Compare election results — Then versus now',description:'Compare recorded elections in the same country and see how parties, vote shares and parliamentary seats changed between elections.'},
 '/coalitions':{title:'Parliamentary coalition builder',description:'Explore possible parliamentary coalitions using recorded election seat totals, party selections and majority thresholds.'},
 '/us-election-night':{title:'U.S. election night — Senate & House results',description:'Follow our U.S. election night coverage with Senate and House results, race calls, reported counts and the balance of congressional control.'}
};
export const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function descriptionText(value,max=180){
 const text=String(value||'').replace(/\s+/g,' ').trim();
 if(text.length<=max)return text;
 const prefix=text.slice(0,max-1),space=prefix.lastIndexOf(' ');
 return prefix.slice(0,space>max*0.65?space:prefix.length)+'…';
}
// Metadata only: never rewrite the stored election name or visible heading.
export function electionMetadata(e,country){
 const clean=value=>String(value||'').replace(/\s+/g,' ').trim();
 const escapeRegex=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const start=/^\d{4}-\d{2}-\d{2}$/.test(e.startDate||'')?e.startDate.slice(0,4):'';
 const end=/^\d{4}-\d{2}-\d{2}$/.test(e.endDate||'')?e.endDate.slice(0,4):'';
 const year=start+(start&&end&&end!==start?'–'+end:'');
 const type=clean(e.type)||'national';
 country=clean(country)||clean(e.countryId);
 let name=clean(e.title)||clean(e.body)||`${type} election`;
 // Whole terms only, so a year never removes a district number or part of a word.
 const remove=term=>{if(term)name=name.replace(new RegExp('(?<![\\p{L}\\p{N}])'+escapeRegex(term)+'(?![\\p{L}\\p{N}])','giu'),' ');};
 remove(country);
 if(year){remove(year.replace('–','-'));remove(year);remove(start);if(end!==start)remove(end);}
 name=clean(name.replace(/^[\s·|,:;–—-]+|[\s·|,:;–—-]+$/g,''));
 const title=[year,country,name||`${type} election`].filter(Boolean).join(' ')+' | '+siteName;
 const parts=[`${[year,country,type+' election'].filter(Boolean).join(' ')}${name&&name.toLowerCase()!==type+' election'?' — '+name:''}.`];
 if(e.startDate&&e.precision!=='unknown'){
  const date=e.precision==='year'?year:e.precision==='month'?e.startDate.slice(0,7):e.startDate+(e.endDate&&e.endDate!==e.startDate?' to '+e.endDate:'');
  parts.push(`${e.dateStatus==='expected'?'Expected date':'Date'}: ${date}.`);
 }else parts.push('Date not announced.');
 if(e.status==='cancelled'||e.status==='postponed')parts.push(`Election ${e.status}.`);
 const rows=e.results||[];
 const hasResults=rows.some(r=>['votes','share','seats','electoralVotes'].some(k=>Number.isFinite(r[k])))||(e.contests||[]).some(c=>c.results?.some(r=>['votes','share','seats','electoralVotes'].some(k=>Number.isFinite(r[k]))));
 if(hasResults)parts.push(`${e.resultStatus==='final'?'Final':e.resultStatus==='provisional'?'Provisional':'Recorded'} results${e.resultCoverage==='partial'?' (partial coverage)':''}.`);
 if(Number.isFinite(e.totalSeats))parts.push(`${e.totalSeats} seats.`);
 if(rows.length)parts.push(`${rows.length} ${type==='parliamentary'?'parties / lists':'candidates'} ${hasResults?'with recorded results':'listed'}.`);
 if(e.electionMethod==='indirect')parts.push('Indirect election.');
 return {title,description:descriptionText(parts.join(' '))};
}
export function canonicalUrl(route,base='/'){return siteOrigin+siteHref(route.split(/[?#]/)[0],base);}
export function validTimestamp(value){return typeof value==='string'&&/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(value)&&Number.isFinite(Date.parse(value))?new Date(value).toISOString():undefined;}
export function latestTimestamp(values){return values.map(validTimestamp).filter(Boolean).sort().at(-1);}
export function isPrivateRoute(route){return route==='/account'||route==='/editor'||route.startsWith('/editor/')||route==='/election-night';}
export function jsonLd(value){return JSON.stringify(value).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');}
export function pageMetadata({route,title,description,index=true,updated,article,breadcrumbs=[],base='/'}){
 const url=canonicalUrl(route,base),image=siteOrigin+base.replace(/\/?$/,'/')+'social-card.png';
 const fullTitle=title.includes(siteName)?title:title+' · '+siteName;
 const summary=descriptionText(description||title);
 const organization={'@type':'Organization','@id':siteOrigin+'/#organization',name:siteName,url:siteOrigin+'/'};
 const website={'@type':'WebSite','@id':siteOrigin+'/#website',name:siteName,url:siteOrigin+'/',publisher:{'@id':organization['@id']},inLanguage:'en'};
 const webpage={'@type':article?'WebPage':Object.hasOwn(staticPages,route)&&route!=='/'?'CollectionPage':'WebPage','@id':url+'#webpage',url,name:fullTitle,description:summary,isPartOf:{'@id':website['@id']},inLanguage:'en',...(validTimestamp(updated)?{dateModified:validTimestamp(updated)}:{})};
 const graph=[organization,website,webpage];
 if(breadcrumbs.length){webpage.breadcrumb={'@id':url+'#breadcrumb'};graph.push({'@type':'BreadcrumbList','@id':url+'#breadcrumb',itemListElement:[{name:'Home',route:'/'},...breadcrumbs].map((b,n)=>({'@type':'ListItem',position:n+1,name:b.name,item:canonicalUrl(b.route,base)}))});}
 if(article){
  if(article.articleType==='ideology'){
   const term={'@type':'DefinedTerm','@id':url+'#ideology',name:article.title,description:summary,url};graph.push(term);webpage.mainEntity={'@id':term['@id']};
  }else{
   const datePublished=validTimestamp(article.publishAt||article.date);
   const story={'@type':article.articleType==='educational'?'Article':'NewsArticle','@id':url+'#article',headline:article.title,description:summary,mainEntityOfPage:{'@id':webpage['@id']},publisher:{'@id':organization['@id']},author:article.author===siteName?{'@id':organization['@id']}:{'@type':'Person',name:article.author||siteName},articleSection:article.category,inLanguage:'en',isAccessibleForFree:true,...(datePublished?{datePublished}:{}),...(validTimestamp(updated)?{dateModified:validTimestamp(updated)}:{})};
   graph.push(story);webpage.mainEntity={'@id':story['@id']};
  }
 }
 const meta=(name,value,property=false)=>`<meta ${property?'property':'name'}="${name}" content="${escapeHtml(value)}"/>`;
 const head=`<title>${escapeHtml(fullTitle)}</title>${meta('description',summary)}${meta('robots',index?'index,follow,max-image-preview:large':'noindex,follow')}<link rel="canonical" href="${escapeHtml(url)}"/>${meta('og:site_name',siteName,true)}${meta('og:type',article&&article.articleType!=='ideology'?'article':'website',true)}${meta('og:title',fullTitle,true)}${meta('og:description',summary,true)}${meta('og:url',url,true)}${meta('og:locale','en_GB',true)}${meta('og:image',image,true)}${meta('og:image:width','1200',true)}${meta('og:image:height','630',true)}${meta('og:image:alt','World of Elections — Independent election coverage',true)}${meta('twitter:card','summary_large_image')}${meta('twitter:title',fullTitle)}${meta('twitter:description',summary)}${meta('twitter:image',image)}${index?`<script id="page-schema" type="application/ld+json">${jsonLd({'@context':'https://schema.org','@graph':graph})}</script>`:''}`;
 return {head,url,title:fullTitle,description:summary};
}
