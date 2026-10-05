import {AppLink} from '../../src/navigation';
import {educationCategory,readingMinutes,type Educational} from '../../lib/education.mjs';
const paragraphs=(text:string)=>text.split(/\n\s*\n/).filter(p=>p.trim()).map((p,i)=><p key={i}>{p}</p>);
export function EducationalArticle({article:a,preview=false}:{article:Educational;preview?:boolean}){
 const category=educationCategory(a.educationCategory);
 return <article><div className="kicker">{category?.name||'Education'}{preview?' · Preview':''}</div><h1>{a.title||'Untitled educational'}</h1><p className="standfirst">{a.summary}</p><p className="meta">By {a.author} · {a.date} · {readingMinutes(a)} min read</p>
  {!!a.sections.length&&<nav className="education-contents" aria-label="In this educational"><b>In this educational</b>{a.sections.map((s,i)=><a key={s.id} href={'#lesson-section-'+i} onClick={event=>{event.preventDefault();const target=document.getElementById('lesson-section-'+i);target?.focus({preventScroll:true});target?.scrollIntoView();if(!preview)window.history.replaceState(null,'','#lesson-section-'+i);}}>{s.title||'Untitled section'}</a>)}</nav>}
  <div className="articlebody">{paragraphs(a.body)}{a.sections.map((s,i)=><section id={'lesson-section-'+i} tabIndex={-1} key={s.id}><h2>{s.title}</h2>{paragraphs(s.body)}</section>)}</div>
  {!!a.sources.length&&<section className="education-sources"><h2>Sources & further reading</h2>{a.sources.map((s,i)=><p key={i}><a href={(()=>{try{const u=new URL(s.url);return u.protocol==='https:'&&!u.username&&!u.password?s.url:undefined;}catch{return undefined;}})()} target="_blank" rel="noreferrer">{s.label}</a></p>)}</section>}
  {a.educationCategory==='parties-ideology'&&<aside className="education-related"><h2>Explore political ideologies</h2><p>Our ideology library covers political traditions, their principles and history.</p><AppLink action href="/ideologies">Browse our ideology library →</AppLink></aside>}
 </article>;
}
