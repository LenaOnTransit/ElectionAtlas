import {getWorld} from '../../../db/world';
import {ArticleElectionLink} from '../election-link';
import {AppLink} from '../../../src/navigation';
import {content} from '../../../db/content';import {Header,Footer} from '../../components';import {notFound} from '../../../src/navigation';

export default async function Article({params}:any){const {id}=await params;const {articles}=await content();const a=articles.find(a=>a.id===id);if(!a)notFound();const world=a.electionId?await getWorld():null;const election=world?.elections.find(e=>e.id===a.electionId&&e.publication==='published');return <><Header/><main className="articlepage"><AppLink action href="/">« All coverage</AppLink><div className="kicker">{a.category}</div><h1>{a.title}</h1><p className="standfirst">{a.summary}</p><div className="meta">By {a.author} · {a.date}</div><div className="articlebody">{a.body.split('\n\n').map((p:string,i:number)=><p key={i}>{p}</p>)}</div>{election&&<ArticleElectionLink election={election} country={world?.countries.find(c=>c.id===election.countryId)?.name}/>}</main><Footer/></>}
