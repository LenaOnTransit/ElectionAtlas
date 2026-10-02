import {readRecords,writeRecord} from './remote';import {validateIdeology,type Ideology} from '../lib/ideologies';
export async function getIdeologies(all=false):Promise<Ideology[]>{return (await readRecords(['article'],all)).filter(r=>r.data.articleType==='ideology'&&(all||!r.data.archived)).map(r=>r.data as Ideology).sort((a,b)=>a.title.localeCompare(b.title));}
export async function saveIdeology(value:Ideology){validateIdeology(value);return await writeRecord('article',value) as Ideology;}
