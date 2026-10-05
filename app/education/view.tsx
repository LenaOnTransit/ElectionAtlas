import {useState} from 'react';
import {AppLink} from '../../src/navigation';
import {educationCategories,educationCategory,educationalRoute,readingMinutes,type Educational} from '../../lib/education.mjs';
export default function EducationIndex({items,categoryId}:{items:Educational[];categoryId?:string}){
 const [query,setQuery]=useState(''),category=categoryId?educationCategory(categoryId):undefined;
 const inCategory=items.filter(a=>!category||a.educationCategory===category.id);
 const found=inCategory.filter(a=>[a.title,a.summary,a.body,...a.sections.map(s=>s.title+' '+s.body),educationCategory(a.educationCategory)?.name].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
 return <main className="world-main education-index"><div className="kicker">Understand the vote</div><h1>{category?category.name:'Education'}</h1><p className="standfirst">{category?category.description:'Clear explainers from our desk on how elections, political ideas and government work. Choose a topic or find an educational below.'}</p>
  <nav className="education-tabs" aria-label="Educational categories"><AppLink href="/education" className={!category?'active':''}>All educationals</AppLink>{educationCategories.map(c=><AppLink key={c.id} href={'/education/category/'+c.id} className={category?.id===c.id?'active':''}>{c.name}</AppLink>)}</nav>
  {!category&&<div className="ideology-grid education-categories">{educationCategories.map(c=><article key={c.id}><h2><AppLink href={'/education/category/'+c.id}>{c.name}</AppLink></h2><p>{c.description}</p><AppLink action href={'/education/category/'+c.id}>Explore topic →</AppLink></article>)}</div>}
  <div className="ideology-index-tools"><label>Find an educational<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search titles, topics or lesson text…"/></label><AppLink action href="/editor/education">Education newsroom</AppLink></div>
  <h2>{category?'Educationals in this topic':'Our educationals'}</h2><p className="meta" role="status">{found.length} {found.length===1?'educational':'educationals'}{query?' matching your search':''}</p>
  {found.length?<div className="ideology-grid">{found.map(a=><article key={a.id}><div className="kicker">{educationCategory(a.educationCategory)?.name}</div><h2><AppLink href={educationalRoute(a.id)}>{a.title}</AppLink></h2><p>{a.summary}</p><p className="meta">{readingMinutes(a)} min read · {a.date}</p><AppLink action href={educationalRoute(a.id)}>Read educational →</AppLink></article>)}</div>:<div className="empty-state">{query?'No educationals match your search. Try another term.':'Educationals will appear here as they are published.'}</div>}
  {(!category||category.id==='parties-ideology')&&<aside className="education-related"><h2>Our ideology library</h2><p>Explore the political traditions behind parties and elections in our existing ideology guides.</p><AppLink action href="/ideologies">Explore ideologies →</AppLink></aside>}
 </main>;
}
