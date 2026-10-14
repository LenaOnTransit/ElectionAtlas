"""Build evidence-scoped result-table patches; never connects to the database."""
from pathlib import Path
import json,re,copy,unicodedata,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/archive-gap-import';CACHE=ROOT/'.cache/archive-gaps'
BASE=json.loads((OUT/'pre-import-backup.json').read_text());MEMBERS=json.loads((OUT/'swiss-members.json').read_text());BALLOTS=json.loads((OUT/'swiss-winner-lines.json').read_text());PEERS=json.loads((OUT/'scottish-peer-terms.json').read_text())
PDF='https://www.parlament.ch/centers/documents/de/wa-br-wahlresultate.pdf';PEER_SOURCE='https://en.wikipedia.org/wiki/List_of_Scottish_representative_peers'
records=[];audit=[]
def norm(s):return re.sub('[^a-z]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def row(e,name,seats=1,votes=None,party='',color='#385b82',winner=True):
 r=dict(id=e['id']+'-result-'+str(len(e['results'])+1),name=name,party=party,color=color,votes=votes,share=None,seats=seats,previousSeats=None,electoralVotes=None,winner=winner,ideologyIds=[]);e['results'].append(r);return r
def patch(base):
 e=copy.deepcopy(base['data']);e.update(results=[],checked='2026-10-14',version=e['version']+1,resultStatus='final',resultCoverage='partial');return e
def source(label,url):return dict(label=label,url=url)
def finish(e,kind,scope):
 records.append(e);audit.append(dict(id=e['id'],kind=kind,resultRows=len(e['results']),seats=sum(r['seats'] or 0 for r in e['results']),scope=scope,sources=e['sources']))
for b in BASE:
 e=b['data'];year=int(e['startDate'][:4]) if e['startDate'] else None
 if e['countryId']=='ch':
  e=patch(b);groups={}
  for x in BALLOTS:
   if x['date'].startswith(str(year)+'-'):groups.setdefault(x['date'],[]).append(x)
  candidates=[(d,rows) for d,rows in groups.items() if len(rows)==7]
  full_ballots=candidates[0] if len(candidates)==1 else None
  e['totalSeats']=7;e['turnout']=None;e['electionMethod']='indirect';e['title']=f'Switzerland Federal Council renewal election {year}'
  if full_ballots:
   date,ballots=full_ballots;e.update(startDate=date,precision='day',dateStatus='confirmed')
   for x in ballots:
    surname=x['name'].replace('PILEZ','PILET');possible=[]
    for m in MEMBERS:
     key=m['originalName'].split()[0] if not m['originalName'].lower().startswith('von ') else ' '.join(m['originalName'].split()[:2])
     if norm(key)==norm(surname) and m['elected']<=date<=m['end']:possible.append(m)
    assert len(possible)==1,(date,surname,possible)
    m=possible[0];name=m['name']
    if m['originalName'].lower().startswith('von '):name=' '.join(m['originalName'].split()[2:]+m['originalName'].split()[:2])
    row(e,name,votes=x['votes'],party=m['party'])
   scope='Seven elected members and each winner’s decisive seat-ballot vote count'
   e['voteBasis']='Winner votes in seven separate Federal Assembly seat ballots; no common national vote-share denominator'
   e['notes']='The United Federal Assembly elected the seven-member collective executive through separate seat ballots. The table records each successful candidate’s decisive-ballot count from Parliament’s historical compilation; it is not a full table of all losing candidates or earlier rounds. Votes for different seats must not be added as a national vote total. Shares and public turnout are not applicable. Party labels retain the historical source abbreviations; personal ideology is unassessed.'
  else:
   cutoff=f'{year+1}-01-01';roster=[m for m in MEMBERS if m['elected']<=cutoff<m['end']]
   assert len(roster) in [6,7],(year,len(roster))
   for m in roster:row(e,m['name'],party=m['party'],votes=None)
   if year==1848:e.update(startDate='1848-11-16',precision='day',dateStatus='confirmed')
   scope='Accepted elected-member roster reconstructed from official election/tenure chronology; individual ballot counts unavailable'
   e['voteBasis']='Accepted elected members of the collective executive after renewal; individual parliamentary votes not transcribed'
   e['notes']='This is an indirect renewal of Switzerland’s collective executive, not a popular presidential ballot. The named-member table is reconstructed from Parliament’s official election and tenure chronology, taking the accepted members entering the following calendar year. Individual seat-ballot votes, losing candidates, earlier rounds and public turnout remain blank. The result coverage is partial; this roster does not constitute a reconstructed vote tally. Historical source party abbreviations are retained, without inferring personal ideologies.'
   if year==1869:e['notes']+=' Six accepted members entering the following year are verified. Victor Ruffy died on 29 December; the seventh renewal outcome and any subsequent replacement are not assigned in this transcription.'
   if year==1878:e['notes']+=' Six continuing/elected members are verified in the chronology. Johann Jakob Scherer died late in December and the seventh renewal result has not been resolved in this transcription; no fictional vacancy candidate or successor is added.'
  e['summary']='Parliament selected the members of the Federal Council; the table distinguishes named outcomes from unavailable ballot detail.'
  e['sources']+=[source('Swiss Parliament: historical seat-ballot results and elected-member chronology, pp.25–61 and 74–78',PDF),source('Federal authorities: renewal procedure, declined elections and non-re-election history','https://www.admin.ch/en/federal-council-elections-since-1848')]
  finish(e,'swiss-executive',scope)
 elif e['countryId']=='gb':
  e=patch(b);date=e['startDate'];names=sorted({p['name'] for p in PEERS if p['start']<=date<p['end']})
  if date=='1880-04-16':
   names.remove('James St Clair, 14th Lord Sinclair');e['sources'].append(source('London Gazette, 23 April 1880: official sixteen-peer return','https://www.thegazette.co.uk/London/issue/24837/page/2657/data.pdf'))
  assert len(names)==(15 if date=='1868-12-03' else 16),(date,len(names))
  for name in names:row(e,name)
  e['title']=f'United Kingdom Scottish representative peers election {year}'
  e['summary']=f'The recorded return identifies {len(names)} elected Scottish representative peers for the House of Lords.'
  e['voteBasis']='Elected representative-peer seats; candidate vote marks and eligible-peer turnout unavailable'
  e['notes']='This table covers the elected Scottish component of the House of Lords, not its entire membership. Named winning peers are reconstructed from the cited election/service intervals and the election chronology. Re-election during a continuous recorded service interval is distinguished from succession to the peerage. Each verified elected representative receives one seat. Candidate vote marks, losing candidates, party affiliations and personal ideologies are not inferred; public turnout does not apply. Result coverage is partial because the complete ballot tally has not been transcribed.'
  e['sources'].append(source('Representative-peer election and service intervals',PEER_SOURCE))
  if date=='1868-12-03':
   e['notes']+=' The return certified fifteen peers; the sixteenth seat was unresolved because the Earl of Kellie and Lord Rollo received equal votes. The later July 1869 election is not substituted for this result.'
   e['sources'].append(source('Hansard, 10 December 1868: certificate of fifteen peers and tied final seat','https://api.parliament.uk/historic-hansard/lords/1868/dec/10/preamble'))
  if date=='1880-04-16':e['notes']+=' The official Gazette return supersedes the compiled service interval for Lord Sinclair; he is excluded from this election’s sixteen selected peers.'
  finish(e,'scottish-peers','Named elected component only; vote tally remains unavailable')
records.sort(key=lambda e:(e['countryId'],e['startDate'],e['id']))
def find(id):return next(b for b in BASE if b['id']==id)
# Exact, source-scoped seat outcomes; approximate figures remain in prose only.
for id,entries,total,scope in [
 ('world-belgium-chamber-1843-06-13',[('Catholics',32),('Liberals',13),('Independents',2)],47,'47 seats renewed in the 95-seat Chamber; historical Catholic/Liberal group labels'),
 ('world-france-1818-french-legislative-election',[('Liberals',22),('Ministerials',17),('Liberal-adjacents',10),('Ultra-royalists',4)],53,'53 seats in the partial renewal; not the full Chamber composition'),
 ('world-romania-chamber-1867-12-01',[('Concordia Agreement (including Free and Independent Faction)',85),('Whites',34),('Moderate liberals',30)],157,'Exact reported Assembly seats; eight seats not assigned in this transcription'),
 ('world-romania-chamber-1892-02-01',[('Consolidated Conservatives',148),('National Liberal Party',None)],None,'Exact reported conservative Assembly allocation only; liberal allocation is approximately 32–35'),
 ('world-romania-senate-1892-02-01',[('Consolidated Conservatives',57),('National Liberal Party',None)],None,'Conservative Senate seats derived from 205 combined seats minus 148 Assembly seats; approximate liberal total not entered'),
 ('world-tunisia-2005-07-03-chamber-of-councillors',[('Representatives of local collectivities',43),('Tunisian Union of Industry, Trade and Handicrafts (UTICA)',14),('Tunisian Union of Agriculture and Fisheries (UTAP)',14)],85,'71 indirectly elected seats filled; fourteen UGTT seats unfilled; forty-one presidential appointments excluded'),
 ('world-tunisia-2008-08-10-chamber-of-councillors',[('Representatives of local collectivities',21),('Tunisian Union of Industry, Trade and Handicrafts (UTICA)',7),('Tunisian Union of Agriculture and Fisheries (UTAP)',7)],35,'35 indirectly elected renewal seats; twenty presidential appointments excluded'),
 ('world-tunisia-2022-12-17-assembly-of-people-s-representatives',[('Elected individual constituency candidates (aggregate)',154)],161,'154 individually elected members across the December first round and January runoff; seven positions unfilled'),
 ('world-tunisia-2024-03-28-national-council-of-regions-and-districts',[('Elected regional and district delegates (aggregate)',77)],77,'77 certified indirect winners; no party breakdown or candidate vote tally inferred')]:
 e=patch(find(id));e['totalSeats']=total
 for name,seats in entries:row(e,name,seats=seats,winner=False)
 if id=='world-france-1818-french-legislative-election':e['endDate']='1818-07-19'
 e['title']={'be':'Belgium','fr':'France','ro':'Romania','tn':'Tunisia'}[e['countryId']]+' '+e['title']+' '+e['startDate'][:4]
 e['voteBasis']='Recorded election seat allocation only; candidate/party vote counts and shares unavailable'
 e['summary']=scope+'.'
 e['notes']='The table records only the cited seat outcome: '+scope+'. Vote counts and vote shares are left blank. Result coverage is partial; a result table does not imply a complete vote tally. Historical group labels or delegation categories are not invented political parties. No ideology is assigned without election-era evidence. Previous-seat comparisons are not inferred.'
 if e['countryId']=='tn' and '-councillors' in id:
  e['electionMethod']='indirect';e['notes']+=' Total seats denotes the indirectly elected positions in this contest, not the entire chamber. Presidential appointments are outside this table.'
 if id=='world-tunisia-2022-12-17-assembly-of-people-s-representatives':
  e['endDate']='2023-01-29';e['notes']+=' Voting was for individual constituency candidates, not party lists. The aggregate does not assert that all winners were politically unaffiliated. Parliamentary blocs formed after the election are not substituted for election results.'
 if id=='world-tunisia-2024-03-28-national-council-of-regions-and-districts':e['electionMethod']='indirect';e['turnout']=None;e['notes']+=' The certified total does not supply a comparable national popular-vote denominator; different electoral bodies voted in separate ballots. The aggregate is not a political party.'
 finish(e,'verified-seat-outcome',scope)
e=patch(find('world-france-president-1871-designation'));e['title']='France parliamentary presidential designation 1871';e['electionMethod']='indirect';row(e,'Adolphe Thiers',seats=None,party='',winner=True)
e['voteBasis']='Named presidential designation under the Rivet law; parliamentary vote tally not transcribed'
e['summary']='The Rivet law formalised Adolphe Thiers’s title as President of the French Republic.'
e['notes']='This is the National Assembly’s parliamentary designation under the law of 31 August 1871, not a popular presidential election. The table identifies the designated office-holder only. Legislative roll-call votes, rival candidates, popular turnout and vote shares are not inferred from the legal act.'
finish(e,'named-designation','Confirmed office-holder; vote tally unavailable')
# Fundación BBVA historical statistics, table 14.3, printed p.1091.
# These are observed deputy compositions, not popular vote shares.
for date,entries in [
 ('1846-12-06',[('Moderados',225),('Puritan moderate faction of Pacheco',43),('Progresistas',60),('Other deputies (source aggregate)',21)]),
 ('1850-08-31',[('Moderados',309),('Puritan moderate faction of Pacheco',16),('Other deputies (source aggregate)',24)]),
 ('1851-05-10',[('Ministerial moderates',212),('Opposition moderates',48),('Progresistas',46),('Other deputies (source aggregate)',43)]),
 ('1853-02-04',[('Ministerial moderates',232),('Anti-government moderates',81),('Other deputies (source aggregate)',36)]),
 ('1863-10-11',[('Ministerial moderates',248),('Opposition moderates',26),('Progresistas',8),('Uncertain affiliation (source category)',31),('Other deputies (source aggregate)',36)])]:
 e=patch(find('world-spain-congress-'+date));e['title']='Spain Congress of Deputies election '+date[:4]
 for name,seats in entries:row(e,name,seats=seats,winner=False)
 e['summary']='Reported post-election deputy composition by historical political grouping.'
 e['voteBasis']='Observed deputy composition in historical statistics; seat percentages are not popular vote shares'
 e['notes']='The table transcribes Fundación BBVA historical statistics, table 14.3 (printed page 1091). Its total of 349 describes deputies counted by the historical sources and may differ from the legal number of seats because credentials could be pending, rejected or disputed, seats vacant, or later by-elections outstanding. The source acknowledges minor discrepancies between historical accounts. Other and uncertain-affiliation rows are source categories, not political parties. Votes, vote shares, previous seats and personal ideologies remain unassigned. Coverage is partial because the electoral vote tally is unavailable.'
 e['sources'].append(source('Fundación BBVA: historical statistics of Spain, table 14.3, p.1091','https://www.fbbva.es/wp-content/uploads/2017/05/dat/autores.pdf'))
 finish(e,'historical-deputy-composition','349 observed deputies; not popular vote shares or a claim of all legal seats filled')
records.sort(key=lambda e:(e['countryId'],e['startDate'],e['id']))
for name,data in [('records',records),('reconciliation',audit)]: (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(len(records),'result tables;',sum(len(e['results']) for e in records),'rows')
