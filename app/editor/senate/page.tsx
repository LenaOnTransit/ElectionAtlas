import {requireUser} from '../../auth';import {isEditor} from '../../../db/content';import {getSenate} from '../../../db/senate';import {Header} from '../../components';import SenateEditor from './workspace';

export default async function Page(){const u=await requireUser('/editor/senate');if(!await isEditor(u.userId))return <><Header/><main><h1>Editorial access required</h1></main></>;try{return <><Header/><SenateEditor initial={await getSenate()} name={u.displayName}/></>}catch{return <><Header/><main><h1>Senate editor is temporarily unavailable</h1><p>Please reload shortly.</p></main></>}}
