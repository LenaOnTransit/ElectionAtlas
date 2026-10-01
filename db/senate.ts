import {storage} from './storage.mjs';import {defaultSenate,Senate} from '../lib/senate';
export async function getSenate():Promise<Senate>{const r=await storage().prepare("SELECT data FROM records WHERE id=? AND kind=?").bind('senate-2026','senate').first<{data:string}>();return r?JSON.parse(r.data):defaultSenate();}
