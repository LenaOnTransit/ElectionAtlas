import type { AnchorHTMLAttributes } from 'react';
import { siteHref } from './routing.mjs';
export function AppLink({href='',...props}:AnchorHTMLAttributes<HTMLAnchorElement>) {
  return <a {...props} href={siteHref(href,import.meta.env.BASE_URL)}/>;
}
export class RouteRedirect extends Error {constructor(public path:string){super('Redirect');}}
export class RouteNotFound extends Error {}
export function redirect(path:string):never {throw new RouteRedirect(path);}
export function notFound():never {throw new RouteNotFound();}
export function navigate(path:string){window.location.assign(siteHref(path,import.meta.env.BASE_URL));}
export function routeSearch(){return window.location.hash.includes('?')?window.location.hash.slice(window.location.hash.indexOf('?')):window.location.search;}
