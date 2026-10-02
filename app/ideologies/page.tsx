import {getIdeologies} from '../../db/ideologies';import {Header,Footer} from '../components';import View from './view';
export default async function Page(){return <><Header/><View items={await getIdeologies()}/><Footer/></>;}
