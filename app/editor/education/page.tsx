import {requireUser} from '../../auth';
import {isEditor} from '../../../db/content';
import {getEducation} from '../../../db/education';
import {Header} from '../../components';
import Workspace from './workspace';
export default async function Page(){const user=await requireUser('/editor/education');if(!await isEditor(user.userId))return <><Header/><main><h1>Editorial access required</h1><p>This account does not have access to the education newsroom.</p></main></>;return <><Header/><Workspace initial={await getEducation(true)}/></>;}
