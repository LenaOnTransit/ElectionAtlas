import {requireUser} from '../../auth';
import {isEditor} from '../../../db/content';
import {getSenate} from '../../../db/senate';
import {getWorldElection} from '../../../db/world';
import {Header} from '../../components';
import TestRoom from './workspace';
export default async function Page(){
 const user=await requireUser('/editor/election-night');
 if(!await isEditor(user.userId))return <><Header/><main><h1>Editorial access required</h1></main></>;
 const [senate,house]=await Promise.all([getSenate(),getWorldElection('world-us-house-2026')]);
 return <><Header/><TestRoom initialSenate={senate} initialHouse={house?.house??null}/></>;
}
