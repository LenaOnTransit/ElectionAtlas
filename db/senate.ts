import {readRecords} from './remote';import {defaultSenate,Senate} from '../lib/senate';
export async function getSenate():Promise<Senate>{const rows=await readRecords(['senate']);return rows.find(r=>r.id==='senate-2026')?.data||defaultSenate();}
