export function siteHref(href,base='/ElectionAtlas/') {
  if (!href.startsWith('/') || href.startsWith('//')) return href;
  const [route,anchor]=href.split('#');
  return base+'#'+route+(anchor?(route.includes('?')?'&':'?')+'scroll='+encodeURIComponent(anchor):'');
}
export function currentRoute(hash,search='') {
  if (hash.startsWith('#/')) return new URL(hash.slice(1),'https://routes.local');
  return new URL((search.includes('code=')?'/account':'/')+search,'https://routes.local');
}
