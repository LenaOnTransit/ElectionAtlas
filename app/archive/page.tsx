import {getWorld} from '../../db/world';import {Header,Footer} from '../components';import Archive from './view';
export const dynamic='force-dynamic';export default async function Page(){try{return <><Header/><Archive data={await getWorld()}/><Footer/></>}catch{return <><Header/><main><h1>Archive temporarily unavailable</h1><p>Please reload shortly.</p></main></>}}
