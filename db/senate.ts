import {env} from 'cloudflare:workers';import {defaultSenate,Senate} from '../lib/senate';
export async function getSenate():Promise<Senate>{if(!env.DB)throw Error('Storage unavailable');const r=await env.DB.prepare("SELECT data FROM records WHERE id=? AND kind=?").bind('senate-2026','senate').first<{data:string}>();return r?JSON.parse(r.data):defaultSenate();}
