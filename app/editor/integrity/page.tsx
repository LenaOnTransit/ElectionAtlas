import {requireUser} from '../../auth';
import {isEditor} from '../../../db/content';
import {ModeratorOnly} from '../../../src/moderation';
import {Header} from '../../components';
import {integrityDashboard} from '../../../db/integrity';
import IntegrityWorkspace from './workspace';
export default async function Page(){
 const user=await requireUser('/editor/integrity');
 if(!await isEditor(user.userId))return <><Header/><main><h1>Moderator access required</h1></main></>;
 return <><Header/><ModeratorOnly><IntegrityWorkspace initial={await integrityDashboard()}/></ModeratorOnly></>;
}
