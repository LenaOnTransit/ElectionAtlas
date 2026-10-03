export function siteHref(href,base='/') {
  if (!href.startsWith('/') || href.startsWith('//')) return href;
  const url=new URL(href,'https://routes.local');
  const path=url.pathname==='/'?'':url.pathname.replace(/^\/+|\/+$/g,'')+'/';
  return base.replace(/\/?$/,'/')+path+url.search+url.hash;
}
export function currentRoute(hash,search='',pathname='/',base='/') {
  if(hash.startsWith('#/'))return new URL(hash.slice(1),'https://routes.local');
  if(search.includes('code='))return new URL('/account'+search,'https://routes.local');
  const prefix=base.replace(/\/$/,'');
  const path=prefix&&pathname.startsWith(prefix+'/')?pathname.slice(prefix.length):pathname;
  return new URL((path.replace(/\/+$/,'')||'/')+search,'https://routes.local');
}
