import Ideologies from '../app/ideologies/page';import Ideology from '../app/ideologies/[id]/page';import IdeologyEditor from '../app/editor/ideologies/page';
import House from '../app/house/page';import HouseEditor from '../app/editor/house/page';
import {useEffect,useState,type ReactNode} from 'react';
import {createRoot} from 'react-dom/client';
import '../app/globals.css';
import {Header,Footer} from '../app/components';
import Home from '../app/page';import Senate from '../app/senate/page';import Calendar from '../app/calendar/page';import Archive from '../app/archive/page';import Article from '../app/article/[id]/page';import Country from '../app/archive/country/[id]/page';import Election from '../app/world/election/[id]/page';import Account from '../app/account/page';import Editor from '../app/editor/page';import SenateEditor from '../app/editor/senate/page';import WorldEditor from '../app/editor/world/page';import Frame from '../app/explore/frame';
import {RouteRedirect,RouteNotFound,navigate,AppLink} from './navigation';
import {currentRoute,siteHref} from './routing.mjs';
import {supabase} from '../lib/supabase';
if(window.location.hash.startsWith('#/')){const legacy=window.location.hash.slice(1);window.location.replace(siteHref(legacy,import.meta.env.BASE_URL));}
const callbacks=window.location.search.includes('code=')||window.location.hash.includes('access_token=');
const pages:Record<string,()=>Promise<ReactNode>>={'/':Home,'/senate':Senate,'/house':House,'/editor/house':HouseEditor,'/calendar':Calendar,'/ideologies':Ideologies,'/editor/ideologies':IdeologyEditor,'/archive':Archive,'/editor':Editor,'/editor/senate':SenateEditor,'/editor/world':WorldEditor,'/atlas':()=>Frame({mode:'atlas'}),'/compare':()=>Frame({mode:'compare'}),'/coalitions':()=>Frame({mode:'coalitions'}),'/us-election-night':()=>Frame({mode:'us-night'}),'/live-elections':()=>Frame({mode:'live'}),'/election-night':()=>Frame({mode:'live'})};
async function loadPage(url:URL):Promise<ReactNode>{
 if(url.pathname==='/account')return Account({searchParams:Promise.resolve(Object.fromEntries(url.searchParams))});
 const loader=pages[url.pathname];if(loader)return loader();
 const params=Promise.resolve({id:decodeURIComponent(url.pathname.split('/').at(-1)||'')});
 if(/^\/ideologies\/[^/]+$/.test(url.pathname))return Ideology({params});
 if(/^\/article\/[^/]+$/.test(url.pathname))return Article({params});
 if(/^\/archive\/country\/[^/]+$/.test(url.pathname))return Country({params});
 if(/^\/world\/election\/[^/]+$/.test(url.pathname))return Election({params});
 throw new RouteNotFound();
}
function Application(){const [revision,setRevision]=useState(0);const [content,setContent]=useState<ReactNode>(null);const [pending,setPending]=useState(true);
 useEffect(()=>{const update=()=>setRevision(n=>n+1);window.addEventListener('hashchange',update);window.addEventListener('account-changed',update);return()=>{window.removeEventListener('hashchange',update);window.removeEventListener('account-changed',update);};},[]);
 useEffect(()=>{let active=true;setPending(true);(async()=>{
  await supabase.auth.getSession();
  const url=callbacks&&!window.location.hash.startsWith('#/')?new URL('/account','https://routes.local'):currentRoute(window.location.hash,window.location.search,window.location.pathname,import.meta.env.BASE_URL);
  try{const result=await loadPage(url);if(active){setContent(result);setPending(false);const anchor=url.searchParams.get('scroll')||window.location.hash.slice(1);requestAnimationFrame(()=>anchor?document.getElementById(anchor)?.scrollIntoView():window.scrollTo(0,0));}}
  catch(error){if(!active)return;if(error instanceof RouteRedirect){navigate(error.path);return;}setContent(<><Header/><main><h1>{error instanceof RouteNotFound?'Page not found':'Could not load this page'}</h1><p>{error instanceof RouteNotFound?'This record is unavailable or private.':'Please try again. If the database has paused, its owner can resume it in Supabase.'}</p><AppLink href="/">Back to the publication</AppLink><button onClick={()=>setRevision(n=>n+1)}>Retry</button></main><Footer/></>);setPending(false);}
 })();return()=>{active=false;};},[revision]);
 return pending?<><Header/><main><p role="status">Loading World of Elections…</p></main></>:<div key={revision}>{content}</div>;
}
createRoot(document.getElementById('root')!).render(<Application/>);
