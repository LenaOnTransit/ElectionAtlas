import {initializeAppearance} from '../app/appearance';
import {useEffect,useState,type ReactNode} from 'react';
import {createRoot} from 'react-dom/client';
import '../app/globals.css';
import {Header,Footer} from '../app/components';
import {RouteRedirect,RouteNotFound,navigate,AppLink} from './navigation';
import {currentRoute,siteHref} from './routing.mjs';
import {supabase} from '../lib/supabase';
import {ModeratorProvider} from './moderation';
initializeAppearance();
if(window.location.hash.startsWith('#/')){const legacy=window.location.hash.slice(1);window.location.replace(siteHref(legacy,import.meta.env.BASE_URL));}
const callbacks=window.location.search.includes('code=')||window.location.hash.includes('access_token=');
const frame=(mode:string)=>async()=>{const {default:Frame}=await import('../app/explore/frame');return Frame({mode});};
const pages:Record<string,()=>Promise<ReactNode>>={
 '/':async()=>(await import('../app/page')).default(),
 '/senate':async()=>(await import('../app/senate/page')).default(),
 '/house':async()=>(await import('../app/house/page')).default(),
 '/editor/house':async()=>(await import('../app/editor/house/page')).default(),
 '/calendar':async()=>(await import('../app/calendar/page')).default(),
 '/education':async()=>(await import('../app/education/page')).default(),
 '/editor/education':async()=>(await import('../app/editor/education/page')).default(),
 '/ideologies':async()=>(await import('../app/ideologies/page')).default(),
 '/editor/ideologies':async()=>(await import('../app/editor/ideologies/page')).default(),
 '/archive':async()=>(await import('../app/archive/page')).default(),
 '/editor':async()=>(await import('../app/editor/page')).default(),
 '/editor/senate':async()=>(await import('../app/editor/senate/page')).default(),
 '/editor/world':async()=>(await import('../app/editor/world/page')).default(),
 '/municipalities/netherlands':async()=>(await import('../app/municipalities/page')).default(),
 '/atlas':frame('atlas'),'/compare':frame('compare'),'/coalitions':frame('coalitions'),
 '/us-election-night':frame('us-night'),'/live-elections':frame('live'),'/election-night':frame('live')
};
function markUnavailable(){
 document.title='Page unavailable · World of Elections';
 let robots=document.querySelector<HTMLMetaElement>('meta[name="robots"]');
 if(!robots){robots=document.createElement('meta');robots.name='robots';document.head.append(robots);}
 robots.content='noindex,follow';document.getElementById('page-schema')?.remove();
}
async function loadPage(url:URL):Promise<ReactNode>{
 if(url.pathname==='/account')return (await import('../app/account/page')).default({searchParams:Promise.resolve(Object.fromEntries(url.searchParams))});
 const loader=pages[url.pathname];if(loader)return loader();
 const params=Promise.resolve({id:decodeURIComponent(url.pathname.split('/').at(-1)||'')});
 if(/^\/education\/category\/[^/]+$/.test(url.pathname))return (await import('../app/education/category/[id]/page')).default({params});
 if(/^\/education\/[^/]+$/.test(url.pathname))return (await import('../app/education/[id]/page')).default({params});
 if(/^\/ideologies\/[^/]+$/.test(url.pathname))return (await import('../app/ideologies/[id]/page')).default({params});
 if(/^\/article\/[^/]+$/.test(url.pathname))return (await import('../app/article/[id]/page')).default({params});
 if(/^\/archive\/country\/[^/]+$/.test(url.pathname))return (await import('../app/archive/country/[id]/page')).default({params});
 if(/^\/world\/election\/[^/]+$/.test(url.pathname))return (await import('../app/world/election/[id]/page')).default({params});
 throw new RouteNotFound();
}
function Application(){const [revision,setRevision]=useState(0);const [content,setContent]=useState<ReactNode>(null);const [pending,setPending]=useState(true);
 useEffect(()=>{const update=()=>setRevision(n=>n+1);window.addEventListener('hashchange',update);window.addEventListener('account-changed',update);return()=>{window.removeEventListener('hashchange',update);window.removeEventListener('account-changed',update);};},[]);
 useEffect(()=>{let active=true;setPending(true);(async()=>{
  await supabase.auth.getSession();
  const url=callbacks&&!window.location.hash.startsWith('#/')?new URL('/account','https://routes.local'):currentRoute(window.location.hash,window.location.search,window.location.pathname,import.meta.env.BASE_URL);
  try{const result=await loadPage(url);if(active){setContent(result);setPending(false);const anchor=url.searchParams.get('scroll')||window.location.hash.slice(1);requestAnimationFrame(()=>anchor?document.getElementById(anchor)?.scrollIntoView():window.scrollTo(0,0));}}
  catch(error){if(!active)return;if(error instanceof RouteRedirect){navigate(error.path);return;}if(error instanceof RouteNotFound)markUnavailable();setContent(<><Header/><main><h1>{error instanceof RouteNotFound?'Page not found':'Could not load this page'}</h1><p>{error instanceof RouteNotFound?'This record is unavailable or private.':'This page is temporarily unavailable. Please try again in a moment.'}</p><AppLink href="/">Back to the publication</AppLink><button onClick={()=>setRevision(n=>n+1)}>Retry</button></main><Footer/></>);setPending(false);}
 })();return()=>{active=false;};},[revision]);
 useEffect(()=>{const main=document.querySelector('main');if(main){main.id='main-content';main.tabIndex=-1}},[pending,content]);
 return pending?<><Header/><main><p role="status">Loading World of Elections…</p></main></>:<div key={revision}>{content}</div>;
}
createRoot(document.getElementById('root')!).render(<ModeratorProvider><Application/></ModeratorProvider>);
