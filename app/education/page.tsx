import {getEducation} from '../../db/education';
import {Header,Footer} from '../components';
import EducationIndex from './view';
export default async function Page(){return <><Header/><EducationIndex items={await getEducation()}/><Footer/></>;}
