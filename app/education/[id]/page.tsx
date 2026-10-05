import {getEducation} from '../../../db/education';
import {educationCategory} from '../../../lib/education.mjs';
import {AppLink,notFound} from '../../../src/navigation';
import {Header,Footer} from '../../components';
import {EducationalArticle} from '../article';
export default async function Page({params}:any){const {id}=await params,items=await getEducation(),article=items.find(a=>a.id===id);if(!article)notFound();const category=educationCategory(article.educationCategory);return <><Header/><main className="articlepage"><div className="education-breadcrumb"><AppLink action href="/education">« Education</AppLink><AppLink href={'/education/category/'+article.educationCategory}>{category?.name}</AppLink></div><EducationalArticle article={article}/></main><Footer/></>;}
