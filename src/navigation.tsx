import type { AnchorHTMLAttributes } from 'react';
import { siteHref } from './routing.mjs';
import {useModerator} from './moderation';
export function AppLink({href='',action=false,className='',...props}:AnchorHTMLAttributes<HTMLAnchorElement>&{action?:boolean}) {
  const moderator=useModerator();
  if((href==='/editor'||href.startsWith('/editor/')||href.startsWith('/editor?')||href.startsWith('/editor#'))&&!moderator)return null;
  return <a {...props} className={[className,action?'action-link':''].filter(Boolean).join(' ')||undefined} aria-current={props['aria-current']??(typeof window!=='undefined'&&href.startsWith('/')&&window.location.pathname.replace(/\/$/,'')===href.split(/[?#]/)[0].replace(/\/$/,'')?'page':undefined)} href={siteHref(href,import.meta.env.BASE_URL)}/>;
}
export class RouteRedirect extends Error {constructor(public path:string){super('Redirect');}}
export class RouteNotFound extends Error {}
export function redirect(path:string):never {throw new RouteRedirect(path);}
export function notFound():never {throw new RouteNotFound();}
export function navigate(path:string){window.location.assign(siteHref(path,import.meta.env.BASE_URL));}
export function routeSearch(){return window.location.hash.includes('?')?window.location.hash.slice(window.location.hash.indexOf('?')):window.location.search;}
