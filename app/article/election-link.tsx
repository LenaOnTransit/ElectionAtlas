import {AppLink} from '../../src/navigation';
import {dateLabel,type WorldElection} from '../../lib/world';

export function ArticleElectionLink({election,country,preview=false}:{election:WorldElection;country?:string;preview?:boolean}) {
  const isPrivate=election.publication!=='published';
  return <aside className="article-election-link" aria-label="Related election">
    <div className="kicker">Related election{country?' · '+country:''}</div>
    <h2>{election.title}</h2>
    <p className="meta">{dateLabel(election)}{election.snap?' · Snap election':''}</p>
    {preview&&isPrivate?<p className="meta">Private election draft. This card will appear to readers once the election is published.</p>:<AppLink href={'/world/election/'+encodeURIComponent(election.id)} target={preview?'_blank':undefined}>View election in the archive</AppLink>}
  </aside>;
}
