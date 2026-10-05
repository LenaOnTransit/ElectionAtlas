import {getEducation} from '../../../../db/education';
import {educationCategory} from '../../../../lib/education.mjs';
import {notFound} from '../../../../src/navigation';
import {Header,Footer} from '../../../components';
import EducationIndex from '../../view';
export default async function Page({params}:any){const {id}=await params;if(!educationCategory(id))notFound();return <><Header/><EducationIndex items={await getEducation()} categoryId={id}/><Footer/></>;}
