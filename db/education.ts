import {readRecords} from './remote';
import {publicEducation,type Educational} from '../lib/education.mjs';
export async function getEducation(all=false):Promise<Educational[]>{
 const items=(await readRecords(['article'],all)).filter(r=>r.data.articleType==='educational').map(r=>r.data as Educational);
 return all?items:publicEducation(items);
}
