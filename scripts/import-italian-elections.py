"""Build Italy's national election archive from reviewed snapshots; never publishes."""
from pathlib import Path
from bs4 import BeautifulSoup
from us_presidential_html import Tables, expand
import re, json, hashlib, datetime

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/italy';OUT=ROOT/'scripts/italian-election-import'
CHECKED='2026-10-09';records=[];audit=[];reconciliation=[]
MONTHS={m.lower():i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
ITALIAN_MONTHS=dict(zip(['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'],range(1,13)))

def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def number(v):
 v=v.replace(',','').replace('%','').replace('\xa0','').strip()
 return float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
def integer(v):
 if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+',v.strip()):return int(re.sub('[.,]','',v))
 n=number(v);return int(n) if n is not None and n.is_integer() else None
def seat(v):
 if '/' in v:v=v.split('/')[0].strip()
 parts=v.split()
 if len(parts)>1 and all(p.isdigit() for p in parts) and sum(map(int,parts[1:]))==int(parts[0]):return int(parts[0])
 return 0 if v in ['–','—','-','—N/a'] else integer(v)
def read(key,url):
 p=CACHE/(key+'.html');s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,script,style'):n.decompose()
 audit.append(dict(file=p.name,url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return s
def grid(t):
 for c in t.select('td,th'):
  for a in ['rowspan','colspan']:
   if c.has_attr(a):c[a]=re.match(r'\d+',c[a]).group()
 p=Tables();p.feed(str(t));return expand(p.tables[0]['rows'])
def dates(s,y):
 pattern=r'(\d{1,2})(?:\s*(?:and|–|-|to)\s*(\d{1,2}))?\s+('+'|'.join(MONTHS)+r')\s*(\d{4})?'
 ps=[txt(p).split('. ')[0] for p in s.select('p') if re.search(r'(?:elections? (?:were|was)|election.* held)',txt(p),re.I)]
 box=s.select_one('table.infobox')
 if box:ps.extend(txt(c) for c in box.select('td') if '→' in txt(c) and len(txt(c))<350)
 for lead in ps:
  ds=[]
  for m in re.finditer(pattern,lead,re.I):
   a,b,month,year=m.groups()
   if year and int(year)!=y:continue
   ds.append(datetime.date(y,MONTHS[month.lower()],int(a)).isoformat())
   if b:ds.append(datetime.date(y,MONTHS[month.lower()],int(b)).isoformat())
  if ds:return sorted(set(ds)),'day'
 return [f'{y}-01-01'],'year'
def base(key,s,scope):
 y=int(key[:4]);ds,precision=dates(s,y)
 if scope=='european' and y in [2009,2024]:ds=[f'{y}-06-'+d for d in (['06','07'] if y==2009 else ['08','09'])];precision='day'
 body={'chamber':'Chamber of Deputies','senate':'Senate of the Republic','constituent':'Constituent Assembly','european':'European Parliament — Italy delegation','president':'President of the Republic'}[scope]
 e=dict(id=f'world-italy-{scope}-{ds[0]}',countryId='it',title=body,type='presidential' if scope=='president' else 'parliamentary',body=body,startDate=ds[0],endDate=ds[-1] if len(ds)>1 else '',precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='it-'+('chamber' if scope=='constituent' else scope),snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='Source-scoped valid votes',results=[],sources=[dict(label='Historical results and cited source bibliography',url='https://en.wikipedia.org/wiki/'+key)],checked=CHECKED,notes='',articleId='',version=1,electionMethod='indirect' if scope=='president' else 'direct')
 if precision!='day':e['notes']+='Exact polling day is not established; no precise day is invented. '
 if y<1919:e['notes']+='Restricted historical male franchise; territorial boundaries and political groupings differ from those of the modern republic. '
 if y<=1913 and y not in [1882,1886,1890]:e['notes']+='Popular votes, where available, refer to the first round; seat distribution follows the final constituency results. '
 if scope=='senate':e['notes']+='Only elected Senate seats are recorded. Life senators and the transitional senators by right are excluded. Chamber and Senate electorates historically differed; their votes are never combined. '
 if scope=='constituent':e['round']='Constituent election';e['notes']+='Election of the Constituent Assembly, separate from the concurrent monarchy/republic referendum. '
 if y in [1929,1934]:e['round']='Single-list approval vote';e['notes']+='Fascist-era plebiscitary approval of a single list, not a competitive multi-party election. Yes/no figures are approval ballots; the No row is not an opposition party winning seats. '
 if y==1924:e['notes']+='The Acerbo law awarded a majority bonus; Fascist intimidation and violence compromised electoral competition. '
 return e
def result(e,name,votes=None,share=None,seats=None,color='#808080',party=None,winner=False):
 name=re.sub(r'\s*\[(?:it|de|fr|en)\]','',name).strip()
 e['results'].append(dict(id=e['id']+'-'+str(len(e['results'])+1),name=name[:200],party=(name if party is None else party)[:200],color=color,votes=votes,share=share,seats=seats,electoralVotes=None,winner=winner,ideologyIds=[]))
def results_tables(s):
 found=[]
 for t in s.select('table.wikitable'):
  if t.find_parent('table'):continue
  g=grid(t);hi=next((i for i,r in enumerate(g) if 'Votes' in [c['text'] for c in r] and '%' in [c['text'] for c in r] and any('Seats' in c['text'] or c['text']=='Total seats' for c in r)),None)
  if hi is None:continue
  h=[c['text'] for c in g[hi]]
  if not any(c['text'] in ['Total','Totals','Valid votes'] for row in g[hi+1:] for c in row):continue
  headings=[txt(h) for h in t.find_all_previous(['h2','h3','h4'])]
  institution=next(('senate' if 'Senate of the Republic' in h else 'chamber' for h in headings if 'Senate of the Republic' in h or 'Chamber of Deputies' in h),'chamber')
  if headings and 'Leaders' in headings[0]:continue
  found.append((t,g,hi,h,institution))
 return found
def fill(e,table,mixed=False):
 t,g,hi,h,institution=table
 namecols=[i for i,v in enumerate(h) if v in ['Party','Party or alliance','Party or coalition','National party']]
 if not namecols:return
 ni=namecols[-1];vi=h.index('Votes');pi=h.index('%')
 si=h.index('Total seats') if 'Total seats' in h else next((i for i,v in enumerate(h) if v.startswith('Seats')),None)
 if si is None and 'FPTP' in h:si=h.index('FPTP')
 denominator=None;sourceSeats=None;votesSeen={};seatSeen=set();valid=None;ballots=None;invalid=None
 for row in g[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)<=ni:continue
  name=r[ni]
  if name in ['Total','Totals']:
   if integer(r[vi]) is not None:denominator=integer(r[vi])
   if si is not None and len(r)>si and seat(r[si]) is not None:sourceSeats=sum(seat(r[i]) or 0 for i,v in enumerate(h) if v in ['FPTP','Proportional']) if 'FPTP' in h and 'Proportional' in h else seat(r[si])
   continue
  if name=='Valid votes':valid=integer(r[vi]);continue
  if name.lower().startswith(('invalid/blank','blank and invalid')):invalid=integer(r[vi]);continue
  if name in ['Total votes','Total turnout']:ballots=integer(r[vi]);continue
  if name.startswith(('Registered voters/turnout','Electorate')):e['turnout']=number(r[pi]) if number(r[pi]) is not None and number(r[pi])<=100 else None;continue
  if not name or name in ['Party','National party'] or name.startswith(('Source','Invalid','Blank','Electorate','Registered','Total seats')) and name!='Invalidated seats':continue
  v=integer(r[vi]) if len(r)>vi else None;p=number(r[pi]) if len(r)>pi else None
  seats=seat(r[si]) if si is not None and len(r)>si else None
  if 'FPTP' in h and 'Proportional' in h:seats=sum(seat(r[i]) or 0 for i,v in enumerate(h) if v in ['FPTP','Proportional'])
  if v is None and p is None and seats is None:continue
  if si is not None and len(row)>si:
   cell=id(row[si]);seats=None if cell in seatSeen else seats;seatSeen.add(cell)
  cell=id(row[vi])
  if cell in votesSeen and v is not None:
   old=votesSeen[cell];old['name']+=' / '+name;old['party']=old['name'];old['seats']=(old['seats'] or 0)+(seats or 0);continue
  m=re.search(r'background(?:-color)?\s*:\s*(#[A-Fa-f0-9]{6})',row[0].get('style',''))
  result(e,name,v,p,seats,m.group(1) if m else '#808080');votesSeen[cell]=e['results'][-1]
 if valid is not None:denominator=valid
 elif denominator and invalid and ballots is None:ballots=denominator;denominator-=invalid
 totalvotes=sum(r['votes'] or 0 for r in e['results']);totalseats=sum(r['seats'] or 0 for r in e['results'])
 if e['seriesId']=='it-european':
  # A "x / delegation" cell uses x as elected seats, not the denominator.
  sizes=[int(re.search(r'/\s*(\d+)',row[si]['text']).group(1)) for row in g[hi+1:] if si is not None and len(row)>si and re.search(r'/\s*(\d+)',row[si]['text'])]
  if sizes:sourceSeats=sizes[0]
  if sourceSeats is None:sourceSeats={1979:81,1984:81,1989:81,1994:87,1999:87,2004:78,2009:72,2014:73,2019:73,2024:76}[int(e['startDate'][:4])]
 e['totalSeats']=sourceSeats;e['resultStatus']='final' if e['results'] else 'not-entered'
 e['voteBasis']=('Domestic proportional/list vote component; full elected-seat allocation' if mixed and h.count('Votes')>1 else 'Source-scoped valid votes')+(f' ({denominator:,})' if denominator else '; vote denominator unavailable')
 if mixed:
  e['notes']+='The vote column follows the first domestic voting component in the source; seats cover the full elected allocation. Special regional, constituency and overseas vote denominators are not added to this percentage column. Shared coalition vote cells are counted once and their party seat rows are combined. Coverage is partial across electoral components. '
 if denominator and totalvotes!=denominator:e['notes']+=f'Entered rows sum to {totalvotes:,} votes versus the source denominator {denominator:,}; discrepancy is retained as partial coverage. '
 if sourceSeats is not None and totalseats!=sourceSeats:e['notes']+=f'Entered seat rows sum to {totalseats} versus the source total {sourceSeats}; coverage is partial. '
 if sourceSeats is not None and totalseats>sourceSeats:
  for r in e['results']:r['seats']=None
  e['notes']+='Conflicting seat allocations are omitted to avoid an overfull seat diagram. '
 e['resultCoverage']='complete' if not mixed and denominator and totalvotes==denominator and sourceSeats is not None and totalseats==sourceSeats and abs(sum(r['share'] or 0 for r in e['results'])-100)<.2 else 'partial'
 reconciliation.append(dict(id=e['id'],voteTotal=denominator,recordedVotes=totalvotes,seatTotal=sourceSeats,recordedSeats=totalseats,ballots=ballots,mixedScope=mixed))

read('overview','https://en.wikipedia.org/wiki/Elections_in_Italy')
links=json.loads((OUT/'links.json').read_text())
for key,url in links.items():
 s=read(key,url);y=int(key[:4])
 if 'presidential' in key or 'provisional' in key:continue
 scope='european' if 'European_Parliament' in key else 'constituent' if y==1946 else 'chamber'
 tables=results_tables(s)
 if scope=='european':
  e=base(key,s,scope);fill(e,tables[0]);records.append(e);continue
 for institution in ['chamber','senate'] if y>=1948 else ['chamber']:
  e=base(key,s,scope if institution=='chamber' else institution);candidates=[t for t in tables if t[4]==institution]
  assert candidates,(key,institution)
  if y==1994 and institution=='senate':
   chosen=candidates[-1];chosen[3][:]=[c['text'] for c in chosen[1][chosen[2]+1]];chosen=(chosen[0],chosen[1],chosen[2]+1,chosen[3],chosen[4]);fill(e,chosen)
  else:fill(e,candidates[0],mixed=y>=1994)
  if y==1946:
   oldid=e['id'];e.update(id='world-italy-constituent-1946-06-02',startDate='1946-06-02',endDate='1946-06-03')
   next(a for a in reconciliation if a['id']==oldid)['id']=e['id']
  if y in [1929,1934]:
   for r in e['results']:
    if 'Fascist' in r['name']:r['name']='Yes — approve Fascist single list';r['party']='National Fascist Party'
    else:r['name']='No — reject single list';r['party']=''
   e['voteBasis']='Single-list approval/rejection ballots; not competitive party votes'
  records.append(e)

# Official presidential archive: the decisive electoral-college ballot, including
# blank/invalid/dispersed outcomes, with participating voters as the denominator.
preslinks=json.loads((OUT/'official-presidential-links.json').read_text())
for key,url in preslinks.items():
 s=read(key,url);text=txt(s)
 if key=='official-president-1-0':
  for year,date,v,total in [(1946,'1946-06-28',396,501),(1947,'1947-06-26',405,431)]:
   wiki=f'{year}_Italian_provisional_head_of_state_election';e=base(wiki,read(wiki,links[wiki]),'president');e.update(id='world-italy-provisional-head-'+date,title='Provisional Head of State — Constituent Assembly election',body='Provisional Head of State',startDate=date,endDate='',precision='day',dateStatus='confirmed',round='Constituent Assembly ballot',voteBasis=f'Votes of participating assembly members ({total}); not popular votes')
   e['sources'].insert(0,dict(label='Presidency: election and re-election of Enrico De Nicola',url=url))
   result(e,'Enrico De Nicola',v,round(v/total*100,4),party='',winner=True)
   e['resultStatus']='final';e['notes']=f'The primary account records {v} votes for De Nicola among {total} participating members. Remaining ballot outcomes are not itemized here; coverage is partial. This was the provisional head of state, preceding the constitutional presidency.';records.append(e)
  continue
 ds=re.search(r'(\d{1,2})\s+('+'|'.join(ITALIAN_MONTHS)+r')\s+(\d{4})',text,re.I);assert ds,key
 day,month,year=ds.groups();year=int(year);date=datetime.date(year,ITALIAN_MONTHS[month.lower()],int(day)).isoformat()
 wiki=f'{year}_Italian_presidential_election';e=base(wiki,read(wiki,links[wiki]),'president');e.update(id='world-italy-president-'+date,startDate=date,endDate='',precision='day',dateStatus='confirmed',round='Decisive electoral-college ballot')
 part=re.search(r'votanti\s*:?\s*(\d+)',text,re.I);assert part,key;total=int(part.group(1))
 t=s.select_one('table');assert t,key
 for row in grid(t)[1:]:
  r=[c['text'] for c in row]
  if len(r)<2 or integer(r[-1]) is None:continue
  result(e,r[0],integer(r[-1]),round(integer(r[-1])/total*100,4),party='')
 assert e['results'],key;e['results'][0]['winner']=True
 e['sources'].insert(0,dict(label='Presidency: official decisive-ballot results',url=url));e['voteBasis']=f'Decisive ballot: {total} participating electors, including blank/invalid ballots; not popular votes';e['resultStatus']='final';e['resultCoverage']='complete' if sum(r['votes'] for r in e['results'])==total else 'partial'
 ballot=re.search(r'(\d+|I)[°º]\s*scrutinio',text,re.I)
 if ballot:e['round']+=' ('+ballot.group(1)+')'
 e['notes']='The President is elected indirectly by Parliament in joint session, with regional delegates under the constitutional rules. Votes shown are from the decisive ballot only; earlier rounds are not combined. Percentages use participating electors, including explicitly labelled blank, invalid and dispersed ballots. No popular turnout is inferred. '
 if e['resultCoverage']=='partial':e['notes']+=f'The primary table itemizes {sum(r["votes"] for r in e["results"])} of {total} participating ballots; the discrepancy remains partial. '
 reconciliation.append(dict(id=e['id'],voteTotal=total,recordedVotes=sum(r['votes'] for r in e['results']),seatTotal=None,recordedSeats=0,mixedScope=False));records.append(e)

# 2024 EP final national-party shares and seats supersede secondary election-night
# counts. No raw votes are inferred from rounded official percentages.
s=read('official-european-2024','https://results.elections.europa.eu/en/national-results/italy/2024-2029/')
e=next(e for e in records if e['seriesId']=='it-european' and e['startDate'].startswith('2024'))
old={r['name']:r for r in e['results']};e['results']=[]
reviewed=json.loads((OUT/'official-european-2024.json').read_text())
for row in reviewed['rows']:result(e,row['name'],share=row['share'],seats=row['seats'],color=row['color'])
e.update(totalSeats=76,resultCoverage='complete',resultStatus='final',voteBasis='European Parliament final national-party vote shares; raw votes unavailable in this primary table',turnout=reviewed['turnout'])
e['sources'].insert(0,dict(label='European Parliament: final national-party results and constitutive-session seats',url='https://results.elections.europa.eu/en/national-results/italy/2024-2029/'));e['notes']='Final vote shares and the 76-seat elected delegation follow the European Parliament national results page. Raw vote counts are omitted because the primary table publishes percentages; secondary counts differ from these final shares. Shares and seats are by national list, not by later political-group affiliation. '
reconciliation[:]=[a for a in reconciliation if a['id']!=e['id']];reconciliation.append(dict(id=e['id'],voteTotal=None,recordedVotes=0,seatTotal=76,recordedSeats=76,mixedScope=False,primaryShares=True))

# Validated Senate tables: keep distinct domestic, regional and overseas scopes.
s=read('official-senate-2001','https://www.parlamento.it/leg/14/Elettorale/riepilogo.htm')
e=next(e for e in records if e['seriesId']=='it-senate' and e['startDate'].startswith('2001'));e['results']=[]
t=next(t for t in s.select('table') if not t.find('table') and 'Gruppo elettorale' in txt(t))
for row in t.select('tr')[1:]:
 r=[txt(c) for c in row.find_all(['td','th'])]
 if len(r)!=4 or r[0]=='Totali':continue
 result(e,r[0],integer(r[1]),float(r[2].replace(',','.')),seat(r[3]))
e.update(totalSeats=315,turnout=None,resultCoverage='partial',voteBasis='Validated Senate electoral-group votes (33,873,256); not Chamber votes')
e['sources'].insert(0,dict(label='Senate: validated 2001 national results',url='https://www.parlamento.it/leg/14/Elettorale/riepilogo.htm'))
e['notes']='Only elected senators are included. The official validated table itemizes 314 assigned seats against the 315-seat elected chamber; the remaining seat is not invented. Electoral-group votes are retained as reported. No turnout is inferred from unavailable registered-voter totals. '
reconciliation[:]=[a for a in reconciliation if a['id']!=e['id']];reconciliation.append(dict(id=e['id'],voteTotal=33873256,recordedVotes=sum(r['votes'] for r in e['results']),seatTotal=315,recordedSeats=sum(r['seats'] or 0 for r in e['results']),mixedScope=True))
reviewed=json.loads((OUT/'official-senate-2022.json').read_text())
for key,url in reviewed['sources'].items():read(key,url)
e=next(e for e in records if e['seriesId']=='it-senate' and e['startDate'].startswith('2022'));e['results']=[]
for row in reviewed['rows']:result(e,row['name'],row.get('votes'),row.get('share'),row['seats'])
e.update(totalSeats=200,turnout=None,resultCoverage='partial',voteBasis='Validated domestic list votes in the main 189-seat table (27,568,811); regional and overseas seats are labelled separately')
e['sources']=[dict(label='Senate: validated 2022 results',url=url) for url in reviewed['sources'].values()]+e['sources']
e['notes']='The main domestic table reports 189 seats. Valle d’Aosta (1), Trentino-Alto Adige (6) and overseas (4) allocations are separate seat-only rows, making 200 elected seats. Their votes and percentages are not mixed into the domestic denominator. Coalition totals are used once. The primary valid-ballot line differs from its list-vote total by one ballot; this discrepancy is retained. Life senators are excluded; no turnout is inferred. '
reconciliation[:]=[a for a in reconciliation if a['id']!=e['id']];reconciliation.append(dict(id=e['id'],voteTotal=27568811,recordedVotes=sum(r['votes'] or 0 for r in e['results']),seatTotal=200,recordedSeats=sum(r['seats'] for r in e['results']),mixedScope=True))

history='https://storia.camera.it/legislature/legs-sabaudo'
read('official-electoral-history',history)
for e in records:
 if e['startDate'][:4] in ['1929','1934']:
  source=dict(label='Chamber of Deputies: Fascist single-list electoral system',url=history)
  e['sources'].insert(0,source);e['legitimacy']=dict(level='uncompetitive',summary='Our assessment: a Fascist single-list approval vote under restricted political competition. The Chamber’s historical account describes a single 400-person list selected by the Fascist Grand Council and submitted for approval or rejection.',reviewed=CHECKED,sources=[source])
 if e['seriesId']=='it-president' and e['body']=='President of the Republic':
  names={1948:'Luigi Einaudi',1955:'Giovanni Gronchi',1962:'Antonio Segni',1964:'Giuseppe Saragat',1971:'Giovanni Leone',1978:'Sandro Pertini',1985:'Francesco Cossiga',1992:'Oscar Luigi Scalfaro',1999:'Carlo Azeglio Ciampi',2006:'Giorgio Napolitano',2013:'Giorgio Napolitano',2015:'Sergio Mattarella',2022:'Sergio Mattarella'}
  e['results'][0]['name']=names[int(e['startDate'][:4])]

for e in records:
 for i,r in enumerate(e['results']):r['id']=e['id']+'-'+str(i+1);r['name']=r['name'][:200];r['party']=r['party'][:200]
 e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['precision']=='day' and e['precision']=='day' and x['startDate']==e['startDate']]
 e['summary']=e['body']+(': '+str(e['totalSeats'])+' elected seats.' if e['totalSeats'] is not None else ': '+('indirect constitutional election.' if e['type']=='presidential' else 'historical national election.'))
records.sort(key=lambda e:(e['startDate'],e['id']));assert len({e['id'] for e in records})==len(records)
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,recordCount=len(records),sources=audit),indent=2)+'\n');(OUT/'reconciliation.json').write_text(json.dumps(reconciliation,indent=2)+'\n')
print('Built',len(records),'records. Counts:',{k:sum(e['seriesId']==k for e in records) for k in set(e['seriesId'] for e in records)})
print('Unresolved dates:',[(e['id'],e['precision']) for e in records if e['precision']!='day'])
print('Reconciliation gaps:',[(a['id'],a['recordedVotes'],a['voteTotal'],a['recordedSeats'],a['seatTotal']) for a in reconciliation if (a['voteTotal'] and a['recordedVotes']!=a['voteTotal']) or a['recordedSeats']!=a['seatTotal'] and a['seatTotal'] is not None])
