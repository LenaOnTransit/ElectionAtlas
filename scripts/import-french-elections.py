"""Build sourced French lower-house/presidential records; never publishes.
Requires beautifulsoup4. Source HTML lives in ignored .cache/france.
"""
from pathlib import Path
import json,re,hashlib,datetime
from bs4 import BeautifulSoup
from us_presidential_html import Tables,expand
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/france';OUT=ROOT/'scripts/french-election-import';OUT.mkdir(exist_ok=True)
records=[];audit=[];CHECKED='2026-10-08'
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def text(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def soup(p):
 s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,style,script'):n.decompose()
 return s
def tables(p):
 parser=Tables();parser.feed(re.sub(r'colspan="(\d+)[^"]*"',r'colspan="\1"',p.read_text()))
 for t in parser.tables:
  for row in t['rows']:
   for c in row:
    for k in ['colspan','rowspan']:
     if k in c:c[k]=re.match(r'\d+',c[k]).group() if re.match(r'\d+',c[k]) else '1'
 return [expand(t['rows']) for t in parser.tables]
def num(x):
 x=x.replace('\u202f','').replace('\xa0','').replace(',','').replace('%','').strip()
 return float(x) if re.fullmatch(r'\d+(?:\.\d+)?',x) else None
def integer(x):
 n=num(x);return int(n) if n is not None and n.is_integer() else None
def color(c):
 m=re.search(r'background(?:-color)?\s*:\s*(#[a-fA-F0-9]{6})',c.get('style',''));return m.group(1) if m else '#808080'
def source(label,url):return dict(label=label,url=url)
def dateinfo(s,year):
 box=s.select_one('table.infobox')
 if not box:return [f'{year}-01-01'],'year'
 cells=[x for x in box.select('td') if '→' in text(x) and len(text(x))<400]
 st=text(cells[0]) if cells else text(box)[:500]
 st=re.sub(r'←\s*(?:\w+\s+)?\d{4}','',st);st=re.sub(r'\d{4}\s*→','',st);dates=[]
 for match in re.finditer(r'(\d{1,2})(?:\s*(?:and|–|-|to)\s*(\d{1,2}))?\s+('+'|'.join(MONTHS)+r')\s*(\d{4})?',st):
  d,other,month,y=match.groups();y=int(y or year)
  if y!=year:continue
  try:
   dates.append(datetime.date(y,MONTHS[month],int(d)).isoformat())
   if other:dates.append(datetime.date(y,MONTHS[month],int(other)).isoformat())
  except ValueError:pass
 if dates:return sorted(set(dates)),'day'
 for m,i in MONTHS.items():
  if re.search(r'\b'+m+r'\b',st):return [f'{year}-{i:02}-01'],'month'
 return [f'{year}-01-01'],'year'
def base(key,typ,dates,precision,url):
 year=int(dates[0][:4]);body='President' if typ=='presidential' else ('Legislative Assembly' if year==1791 else 'National Convention' if year==1792 else 'Council of Five Hundred' if 1795<=year<=1799 else 'Chamber of Representatives' if key.startswith('May_1815') else 'Chamber of Deputies' if 1815<=year<=1846 or 1876<=year<=1936 else 'Legislative Body' if 1852<=year<=1869 else 'Constituent Assembly' if year==1848 or key.startswith(('1945','June_1946')) else 'National Assembly')
 e=dict(id='world-france-'+re.sub('[^a-z0-9]+','-',key.lower()).strip('-'),countryId='fr',title=body,type=typ,body=body,startDate=dates[0],endDate=dates[-1] if len(dates)>1 else '',precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='FR-PRES' if typ=='presidential' else 'FR-LOWER',snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='National valid votes',results=[],sources=[source('Historical results and cited source bibliography',url)],checked=CHECKED,notes='',articleId='',version=1,electionMethod='direct')
 if precision!='day':e['notes']='The source does not establish an exact election day; the date has '+precision+' precision. '
 if year<1945:e['notes']+='The franchise and territorial boundaries differed from present-day France; women were excluded from these national elections. '
 if year<1831:e['electionMethod']='indirect' if year<1800 or key.startswith('May_1815') else 'direct';e['notes']+='Restricted historical franchise; representative selection and political groups are not equivalent to modern party-list elections. '
 if key.startswith(('1817','1818','1819','1797','1798','1799')):e['round']='Partial chamber renewal';e['notes']+='This was a partial renewal, not an election of every chamber seat. '
 return e
def result(e,name,party,votes,share,seats,c='#808080',winner=False):
 e['results'].append(dict(id=e['id']+'-'+str(len(e['results'])+1),name=name[:200],party=party[:200],color=c,votes=votes,share=share,seats=seats,electoralVotes=None,winner=winner,ideologyIds=[]))
def resulttable(p):
 for t in tables(p):
  for i,row in enumerate(t):
   h=[c['text'] for c in row]
   if 'Votes' in h and '%' in h and any('Party' in v or 'Candidate' in v for v in h) and len(h)<15:
    if any(any(c['text']=='Total' for c in r) for r in t[i+1:]):return t,i,h
 return None
def fill(e,p,roundidx=0,pres=False):
 found=resulttable(p)
 if not found:return False
 t,hi,h=found;vi=[i for i,v in enumerate(h) if v=='Votes'][roundidx];pi=[i for i,v in enumerate(h) if v=='%'][roundidx]
 seatcols=[i for i,v in enumerate(h) if 'seat' in v.lower()];si=seatcols[-1] if seatcols and not pres else None
 ni=max(i for i,v in enumerate(h[:vi]) if ('Party' in v or 'Candidate' in v));partycol=next((i for i,v in enumerate(h[:vi]) if v in ['Party','Parties']),None) if pres else None
 if pres:ni=max(i for i,v in enumerate(h[:vi]) if 'Candidate' in v)
 total=None;valid=None;vote_groups={};seat_seen=set()
 for row in t[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)>pi and all(x in ['Total',''] for x in r[:ni+1]) and 'Total' in r[:ni+1]:
   valid=integer(r[vi]);total=integer(r[si]) if si is not None else None;break
 for row in t[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)<=pi:continue
  if all(x in ['Total',''] for x in r[:ni+1]) and 'Total' in r[:ni+1]:break
  name=r[ni]
  if not name or name=='Total' or name.startswith(('Source:','Valid votes','Invalid','Registered','Total votes','Blank votes')):continue
  v=integer(r[vi]);share=num(r[pi]);seats=integer(r[si]) if si is not None else None
  if v is None and share is None and not seats:continue
  seatkey=id(row[si]) if si is not None else None
  if seatkey in seat_seen:seats=None
  if seatkey is not None:seat_seen.add(seatkey)
  votekey=id(row[vi])
  if not pres and votekey in vote_groups and v is not None:
   prev=vote_groups[votekey];prev['name']+=' / '+name;prev['party']=prev['name'];prev['seats']=(prev['seats'] or 0)+(seats or 0);e['notes']+='Shared source votes are recorded once for the combined political group. ';continue
  result(e,re.sub(r'\s*\(incumbent\)','',name),r[partycol] if partycol is not None else name,v,share,seats,color(row[0]));vote_groups[votekey]=e['results'][-1]
 for row in t[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)>pi and ('Registered voters/turnout' in r or (pres and 'Turnout' in r)):e['turnout']=num(r[pi])
 e['totalSeats']=total;e['resultStatus']='final' if e['results'] else 'not-entered'
 if e['results']:
  votes=sum(r['votes'] or 0 for r in e['results']);seats=sum(r['seats'] or 0 for r in e['results']);share=sum(r['share'] or 0 for r in e['results'])
  if valid and votes!=valid:e['notes']+=f'The published rows sum to {votes:,} votes against denominator {valid:,}; the discrepancy is preserved, not attributed to a party. '
  if total is not None and seats!=total:e['notes']+=f'The source reports {total} seats but the rows sum to {seats}; coverage is partial. '
  if total is not None and seats>total:e['totalSeats']=None;e['notes']+='The conflicting chamber total is left unavailable. '
  e['resultCoverage']='complete' if valid and votes==valid and (pres or (total is not None and seats==total)) and abs(share-100)<.2 else 'partial'
  if valid:e['voteBasis']=f'Valid votes ({valid:,}); '+('first round' if roundidx==0 else 'second round')
  if pres and (roundidx==1 or h.count('Votes')==1):max(e['results'],key=lambda r:r['votes'] or 0)['winner']=True
 return bool(e['results'])

# Seat-only historical compilation. Labels come from the source's party-colour metadata.
overview=soup(CACHE/'overview.html');seatbars={}
for a in overview.select('td > a'):
 key=a.get('href','').rsplit('/',1)[-1]
 if not re.search(r'(legislative|National_Convention|Constituent_Assembly)_election$',key):continue
 td=a.parent.find_next_sibling('td')
 if not td:continue
 data=[]
 for c in td.select('table td'):
  n=integer(text(c))
  if n is None:continue
  label={'#D45555':'Far-left republicans','#DA7B8B':'Miscellaneous left','#FDEE00':'Liberals'}.get(color(c.attrs),'Historical political group')
  try:
   v=json.loads(c.get('data-mw',''))['attribs'][0][1]['html'].replace('\\"','"');m=re.search(r'"params":\{"1":\{"wt":"([^"]+)"',v)
   if m:label=m.group(1)
  except (ValueError,KeyError,IndexError):pass
  data.append((label,n,color(c.attrs)))
 if data:seatbars[key]=data
for p in sorted(CACHE.glob('*.html')):
 key=p.stem
 if not re.search(r'_(legislative|National_Convention|Constituent_Assembly)_election$',key):continue
 s=soup(p);year=int(re.search(r'\d{4}',key).group());dates,prec=dateinfo(s,year);e=base(key,'parliamentary',dates,prec,'https://en.wikipedia.org/wiki/'+key);fill(e,p)
 if not e['results']:
  for name,seats,c in seatbars.get(key,[]):result(e,name,name,None,None,seats,c)
  if e['results']:
   e['totalSeats']=sum(r['seats'] for r in e['results']);e['resultStatus']='final';e['sources'].append(source('Historical seat-distribution compilation','https://en.wikipedia.org/wiki/Legislative_elections_in_France'));e['notes']+='Only the compiled seat distribution is entered. Retrospective political groups are not national popular-vote results; no votes or shares are inferred. '
  else:e['notes']+='No reconciled quantitative results are entered; this election is retained in the chronology. '
 if year>=1936 and year!=1986:e['notes']+='Popular votes refer to the first round; seats are the final distribution after all rounds. '
 if year==1958:e['notes']+='The table covers metropolitan France (466 seats), not the full 576-member chamber including overseas territories. ';e['resultCoverage']='partial'
 if year in [1852,1857,1863,1869]:e['notes']+='The Second Empire used official candidates and government pressure; interpret reported votes in that restricted political context. '
 for a in s.select('a[href]'):
  u=a['href']
  if 'archives-resultats-elections.interieur.gouv.fr' in u and u.startswith('https:') and not any(x['url']==u for x in e['sources']) and len(e['sources'])<4:e['sources'].append(source('Ministry of the Interior: official results',u))
 e['summary']=f'{e["body"]}: '+(f'{e["totalSeats"]} seats in the recorded source scope.' if e['totalSeats'] else 'Historical election / chamber renewal.');records.append(e);audit.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for year in [1848,1965,1969,1974,1981,1988,1995,2002,2007,2012,2017,2022]:
 p=CACHE/f'{year}_French_presidential_election.html';s=soup(p);dates,prec=dateinfo(s,year);found=resulttable(p);assert found,year;n=found[2].count('Votes');assert n in [1,2];assert len(dates)>=n,(year,dates)
 for i in range(n):
  e=base(f'president-{year}-'+('first' if i==0 else 'runoff'),'presidential',[dates[i]],prec,'https://en.wikipedia.org/wiki/'+p.stem);e['round']='First round' if n==2 and i==0 else 'Runoff' if i==1 else 'General';e['seriesId']=f'france-president-{year}';fill(e,p,i,True)
  if i==0 and n==2:
   for r in sorted(e['results'],key=lambda r:r['votes'] or 0,reverse=True)[:2]:r['advanced']=True
  for a in s.select('a[href]'):
   u=a['href']
   if ('conseil-constitutionnel.fr' in u or 'archives-resultats-elections.interieur.gouv.fr' in u) and u.startswith('https:') and not any(x['url']==u for x in e['sources']) and len(e['sources'])<4:e['sources'].append(source('Official proclamation / results',u))
  e['summary']='National popular-vote presidential election. '+('The top two candidates advanced to the runoff.' if i==0 and n==2 else next(r['name'] for r in e['results'] if r['winner'])+' won.');records.append(e)
 audit.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
p=CACHE/'indirect.html';s=soup(p)
DATES=['1873-05-24','1879-01-30','1885-12-28','1887-12-03','1894-06-27','1895-01-17','1899-02-18','1906-01-17','1913-01-17','1920-01-17','1920-09-23','1924-06-13','1931-05-13','1932-05-10','1939-04-05','1947-01-16','1953-12-23','1958-12-21']
for h,date in zip(s.select('h3'),DATES):
 year=int(date[:4]);parser=Tables();parser.feed(str(h.find_next('table')));grid=expand(parser.tables[0]['rows']);rows=[[c['text'] for c in row] for row in grid];e=base('president-'+date+'-indirect','presidential',[date],'day','https://en.wikipedia.org/wiki/List_of_indirect_presidential_elections_in_France');e['electionMethod']='indirect';e['round']='Decisive parliamentary ballot' if year!=1958 else 'Electoral college ballot';e['voteBasis']='Votes of parliamentarians; not a popular vote' if year!=1958 else 'Votes of the electoral college; not a popular vote';e['notes']='Decisive constitutional ballot; preliminary party meetings and unsuccessful earlier ballots are not separate elections. Published percentages may use participating members rather than valid candidate votes; no popular turnout is inferred. '
 for row,cells in zip(rows,grid):
  if len(row)<4 or not row[1] or row[1] in ['Candidate','Candidates','Total'] or row[1].startswith(('Valid','Spoilt','Turnout','Registered','Abstentions','Official')):continue
  name,party=row[1:3];v=None;share=None
  if year==1873:v=integer(row[3]);share=round(v/391*100,4) if v is not None else None
  elif year in [1947,1958]:v=integer(row[3]);share=num(row[4])
  elif year==1953:v=integer(row[-2]);share=num(row[-1])
  else:share=num(row[-1])
  if v is not None or share is not None:result(e,name,party,v,share,None,color(cells[0]))
 assert e['results'],date;max(e['results'],key=lambda r:r['share'] or 0)['winner']=True;e['resultStatus']='final';e['summary']=next(r['name'] for r in e['results'] if r['winner'])+' was elected by '+('the electoral college.' if year==1958 else 'parliament.')
 if year==1953:e['notes']+='The thirteenth and decisive ballot is shown; voting began on 17 December 1953. '
 records.append(e)
audit.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
e=base('1789-estates-general','parliamentary',['1789-01-01'],'year','https://www2.assemblee-nationale.fr/decouvrir-l-assemblee/histoire/le-suffrage-universel/la-republique-et-le-suffrage-universel/1788-1848-les-premieres-reflexions-autour-du-suffrage/la-designation-des-delegues-aux-etats-generaux-de-1789');e.update(title='Estates-General — constitutional precursor',body='Estates-General',electionMethod='indirect',summary='The three estates selected representatives under the electoral regulation of 24 January 1789; the assembly opened on 5 May.',notes='Dates varied by locality. This precursor led to the National Constituent Assembly; no national party votes, turnout or retrospective partisan seat figures are inferred.');records.append(e)

# Audited corrections and limits: do not trust inconsistent overview bars/infoboxes.
for e in records:
 y=int(e['startDate'][:4])
 if e['type']=='parliamentary':
  if y==1792:e.update(startDate='1792-09-02',endDate='1792-09-19',precision='day',dateStatus='confirmed');e['notes']+='Dates refer to the electoral colleges; primary assemblies met in August. ';e['sources'].append(source('National Assembly: Convention electoral decree','https://www.assemblee-nationale.fr/histoire/suffrage_universel/tab_synoptique.pdf'))
  if y in [1795,1797,1798,1799]:e.update(title='Directory legislature — partial renewal',body='Council of Five Hundred and Council of Ancients',totalSeats=None,round='Partial chamber renewal');e['notes']+='Compiled figures are not a reconciled full lower-house composition; no whole-chamber total is asserted. '
  if y==1830:
   e['results']=[];result(e,'Liberal opposition','Liberal opposition',None,None,274,'#FDEE00');result(e,'Government supporters','Government supporters',None,None,143,'#0067A5');e['totalSeats']=417;e['notes']+='The overview incorrectly gives the government 282 seats; the election-specific table reports 143 of 417. '
  if y==1857:e.update(startDate='1857-06-21',endDate='1857-07-05');e['notes']+='Dates corrected using the French-language historical account; the English infobox contains incorrect months. ';e['sources'].append(source('Historical account: 1857 election dates','https://fr.wikipedia.org/wiki/Élections_législatives_françaises_de_1857'))
  if y==1863:e.update(startDate='1863-05-31',endDate='1863-06-14');e['notes']+='Dates corrected using the French historical account (English infobox is inconsistent). ';e['sources'].append(source('Historical account: 1863 election dates','https://fr.wikipedia.org/wiki/Élections_législatives_françaises_de_1863'))
  if y==1819:result(e,'Liberals','Liberals',None,None,37,'#FDEE00');e['resultStatus']='final';e['notes']+='The narrative reports 37 Liberal seats won in this partial renewal; the remaining results are unavailable. '
  if y<1967:e['resultCoverage']='partial';e['notes']+='Figures retain the cited table’s historical groupings and territory; they should not be treated as a reconciled modern nationwide party dataset. '
 if e['type']=='presidential' and e['startDate']=='1920-09-23':
  e['results']=[]
  for name,party,v in [('Alexandre Millerand','Independent',695),('Gustave Delory','SFIO',69),('Other candidates','Other',22)]:result(e,name,party,v,round(v/786*100,4),None,winner=name=='Alexandre Millerand')
  e['voteBasis']='786 valid parliamentary votes';e['sources'].append(source('Official ballot transcription: Perpignan Digithèque MJP','https://mjp.univ-perp.fr/election/fr/fr1920-2.htm'));e['notes']+='MJP records 892 voters and 786 valid votes; the compilation’s 88.92% for Millerand is corrected to 695/786. '
 if e['type']=='parliamentary':e['summary']=f'{e["body"]}: '+(f'{e["totalSeats"]} seats in the recorded source scope.' if e['totalSeats'] else 'Historical election / chamber renewal.')


# Reconcile decisive ballots against the Digithèque MJP transcription.
BALLOTS={
 '1879-01-30':(670,[('Jules Grévy',563),('Alfred Chanzy',99),('Other candidates',8)]),
 '1885-12-28':(576,[('Jules Grévy',457),('Henri Brisson',68),('Charles de Freycinet',14),('Anatole de La Forge',10),('Other candidates',27)]),
 '1887-12-03':(827,[('Sadi Carnot',616),('Félix Gustave Saussier',188),('Jules Ferry',11),('Charles de Freycinet',5),('Félix Antoine Appert',5),('Charles Floquet',1),('Félix Pyat',1)]),
 '1894-06-27':(845,[('Jean Casimir-Perier',451),('Henri Brisson',195),('Charles Dupuy',97),('Victor Février',53),('Emmanuel Arago',27),('Other candidates',22)]),
 '1899-02-18':(812,[('Émile Loubet',483),('Jules Méline',279),('Other candidates',50)]),
 '1906-01-17':(848,[('Armand Fallières',449),('Paul Doumer',371),('Other candidates',28)])}
for e in records:
 if e['type']!='presidential' or e['startDate'] not in BALLOTS:continue
 valid,rows=BALLOTS[e['startDate']];e['results']=[]
 for i,(name,v) in enumerate(rows):result(e,name,'',v,round(v/valid*100,4),None,winner=i==0)
 e['voteBasis']=f'{valid} valid parliamentary votes';e['sources'].append(source('Decisive ballot transcription: Digithèque MJP','https://mjp.univ-perp.fr/election/fr/fr'+e['startDate'][:4]+'.htm'));e['notes']+='Candidate shares are calculated from the transcribed valid votes. Other candidates combine the remaining valid votes; they do not include blank or invalid ballots. '

# Thiers was designated through a constitutional law, not a candidate election.
e=base('president-1871-designation','presidential',['1871-08-31'],'day','https://www.assemblee-nationale.fr/dyn/histoire-et-patrimoine/troisieme-republique/l-assemblee-nationale-entre-1871-et-1873-le-gouvernement-thiers')
e.update(title='President — parliamentary designation',electionMethod='indirect',round='Constitutional designation',summary='The Rivet law conferred the presidential title on Adolphe Thiers.',notes='Thiers had been chosen chief of the executive by acclamation on 17 February. The law of 31 August conferred the presidential title: its 491 votes for and 94 against were legislative votes, not candidate votes. No candidate result percentages are inferred.')
e['sources'].append(source('Élysée: Adolphe Thiers','https://www.elysee.fr/adolphe-thiers'));records.append(e)

records.sort(key=lambda e:(e['startDate'],e['id']));assert len(records)==len({e['id'] for e in records})
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,recordCount=len(records),sources=audit+[dict(file='overview.html',url='https://en.wikipedia.org/wiki/Legislative_elections_in_France',sha256=hashlib.sha256((CACHE/'overview.html').read_bytes()).hexdigest())]),indent=2)+'\n')
print('Built',len(records),'records:',sum(e['type']=='parliamentary' for e in records),'parliamentary;',sum(e['type']=='presidential' for e in records),'presidential rounds/ballots.');print('No results:',[(e['startDate'],e['title']) for e in records if not e['results']])
