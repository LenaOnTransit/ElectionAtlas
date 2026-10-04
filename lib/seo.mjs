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
 '/ideologies':{title:'Political ideologies — Definitions, history & principles',description:'Explore political ideology guides covering core principles, origins, economic outlooks, government, related traditions and debates, with sources.'},
 '/atlas':{title:'World election atlas — Elections & legitimacy',description:'Explore our interactive world atlas for election coverage, upcoming national elections and country election legitimacy assessments.'},
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
   const story={'@type':'NewsArticle','@id':url+'#article',headline:article.title,description:summary,mainEntityOfPage:{'@id':webpage['@id']},publisher:{'@id':organization['@id']},author:article.author===siteName?{'@id':organization['@id']}:{'@type':'Person',name:article.author||siteName},articleSection:article.category,inLanguage:'en',isAccessibleForFree:true,...(datePublished?{datePublished}:{}),...(validTimestamp(updated)?{dateModified:validTimestamp(updated)}:{})};
   graph.push(story);webpage.mainEntity={'@id':story['@id']};
  }
 }
 const meta=(name,value,property=false)=>`<meta ${property?'property':'name'}="${name}" content="${escapeHtml(value)}"/>`;
 const head=`<title>${escapeHtml(fullTitle)}</title>${meta('description',summary)}${meta('robots',index?'index,follow,max-image-preview:large':'noindex,follow')}<link rel="canonical" href="${escapeHtml(url)}"/>${meta('og:site_name',siteName,true)}${meta('og:type',article&&article.articleType!=='ideology'?'article':'website',true)}${meta('og:title',fullTitle,true)}${meta('og:description',summary,true)}${meta('og:url',url,true)}${meta('og:locale','en_GB',true)}${meta('og:image',image,true)}${meta('og:image:width','1200',true)}${meta('og:image:height','630',true)}${meta('og:image:alt','World of Elections — Independent election coverage',true)}${meta('twitter:card','summary_large_image')}${meta('twitter:title',fullTitle)}${meta('twitter:description',summary)}${meta('twitter:image',image)}${index?`<script id="page-schema" type="application/ld+json">${jsonLd({'@context':'https://schema.org','@graph':graph})}</script>`:''}`;
 return {head,url,title:fullTitle,description:summary};
}
