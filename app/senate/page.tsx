import {getSenate} from '../../db/senate';import SenateView from './view';import {Header,Footer} from '../components';

export default async function Page(){try{return <><Header/><SenateView data={await getSenate()}/><Footer/></>}catch{return <><Header/><main><h1>Senate coverage is temporarily unavailable</h1><p>Please reload shortly.</p></main><Footer/></>}}
