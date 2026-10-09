"""Generate Spain's reviewed national archive; does not publish database rows."""
from pathlib import Path
from bs4 import BeautifulSoup
from us_presidential_html import Tables,expand
import re,json,hashlib,datetime,collections
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/spain';OUT=ROOT/'scripts/spanish-election-import';CHECKED='2026-10-09'
records=[];audit=[];reconciliation=[]
MONTHS={m.lower():i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
ESMONTHS=dict(zip(['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'],range(1,13)))
def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def integer(v):
 v=v.strip().strip('.');return int(re.sub('[,.]','',v)) if re.fullmatch(r'\d+(?:[.,]\d{3})*',v) else None
def seat(v):
 return integer(v.split('/')[0].strip()) if '/' in v else integer(v)
def number(v):
 v=v.replace('%','').replace(',','').strip();return float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
def read(k,url):
 p=CACHE/(k+'.html');s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,script,style'):n.decompose()
 if not any(a['file']==p.name for a in audit):audit.append(dict(file=p.name,url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return s
def grid(t):
 for c in t.select('td,th'):
  for a in ['rowspan','colspan']:
   if c.has_attr(a):c[a]=re.match(r'\d+',c[a]).group()
 for c in t.select('td,th'):
  if c.select_one('[style*="padding-left"]'):c['data-import-detail']='true'
 p=Tables();p.feed(str(t));return expand(p.tables[0]['rows'])
def english_dates(text,y):
 pat=r'(\d{1,2})(?:\s*(?:and|–|-|to)\s*(\d{1,2}))?\s+('+'|'.join(MONTHS)+r')\s*(\d{4})?';out=[]
 for m in re.finditer(pat,text,re.I):
  a,b,mo,yr=m.groups();year=int(yr) if yr else y
  out.append(datetime.date(year,MONTHS[mo.lower()],int(a)).isoformat())
  if b:out.append(datetime.date(year,MONTHS[mo.lower()],int(b)).isoformat())
 return out
def base(scope,date,precision='day',end='',source=None,body=None):
 body=body or {'congress':'Congress of Deputies','senate':'Senate','family':'Cortes Españolas — elected family representatives','european':'European Parliament — Spain delegation','president':'President of the Republic','electors':'Presidential electoral college — citizen electors','king':'King of Spain'}[scope]
 e=dict(id='world-spain-'+scope+'-'+date,countryId='es',title=body,type='presidential' if scope in ['president','king','electors'] else 'parliamentary',body=body,startDate=date,endDate=end,precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='es-'+scope,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='Source-scoped election results',results=[],sources=[source] if source else [],checked=CHECKED,notes='',articleId='',version=1,electionMethod='indirect' if scope in ['president','king'] else 'direct')
 return e
def result(e,name,votes=None,share=None,seats=None,color='#808080',party=None,winner=False):
 e['results'].append(dict(id=e['id']+'-'+str(len(e['results'])+1),name=name[:200],party=(name if party is None else party)[:200],color=color,votes=votes,share=share,seats=seats,electoralVotes=None,winner=winner,ideologyIds=[]))
def heading_institution(t):
 for h in t.find_all_previous(['h2','h3','h4']):
  name=txt(h)
  if name=='Senate':return 'senate'
  if name=='Congress of Deputies':return 'congress'
 return 'congress'
def tables(s):
 out=[]
 for t in s.select('table'):
  if t.find_parent('table') or 'infobox' in t.get('class',[]):continue
  g=grid(t)
  hi=next((i for i,r in enumerate(g[:6]) if 'Votes' in [c['text'] for c in r] and '%' in [c['text'] for c in r]),None)
  if hi is None:hi=next((i for i,r in enumerate(g[:6]) if any(c['text'].startswith('Seats') for c in r) and any(c['text'] in ['Party','Parties and alliances','Party affiliation'] for c in r)),None)
  if hi is None:continue
  if not any(any(c['text'] in ['Total','Total elective seats','Total:','Totals:'] for c in r) for r in g[hi+1:]):continue
  h=txt(t.find_previous(['h2','h3','h4']))
  if h in ['Parties and lists','Parties and candidates','Outgoing delegation','Outgoing parliament','Electoral system','Distribution by European group']:continue
  out.append((t,g,hi,heading_institution(t)))
 return out
def fill(e,table,seatonly=False,label=''):
 t,g,hi,inst=table;h=[c['text'] for c in g[hi]]
 if 'A.29' in h:e['notes']+='Seat totals include unopposed Article 29 proclamations. Reported turnout concerns contested constituencies, not the full registered electorate; no votes are imputed for unopposed seats. '
 names=[i for i,v in enumerate(h) if v in ['Party','Parties and alliances','Party affiliation','National Parties','Electoral alliance']]
 if not names:return
 ni=names[-1];vi=h.index('Votes') if 'Votes' in h else None;pi=h.index('%') if '%' in h else None
 si=h.index('Total') if 'Total' in h else next((i for i,v in enumerate(h) if v.startswith('Seats') and i>ni),None)
 denom=None;totalSeats=None;blank=None;ballots=None;validBallots=None;votes_seen=set();seats_seen=set();groups_seen=set();rows_start=len(e['results'])
 for row in g[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)<=ni:continue
  name=r[ni]
  if row[ni].get('data-import-detail'):continue
  if name.startswith('Total ') and name!='Total elective seats':continue
  if 'registered voters' in name.lower() or 'non-voters' in name.lower():continue
  if name in ['Total','Total elective seats','Total:','Totals:']:
   denom=integer(r[vi]) if vi is not None and len(r)>vi else None
   totalSeats=integer(r[si]) if si is not None and len(r)>si else None;continue
  if name.startswith('Blank ballots'):
   blank=integer(r[vi]) if vi is not None else None
   if inst!='senate' and not seatonly and blank is not None:result(e,'Blank ballots',blank,number(r[pi]) if pi is not None else None,0,party='')
   continue
  if name in ['Votes cast / turnout','Votes cast/turnout']:
   ballots=integer(r[vi]) if vi is not None else None;p=number(r[pi]) if pi is not None else None
   if not seatonly and p is not None and p<=100:e['turnout']=p
   continue
  if name=='Valid votes':validBallots=integer(r[vi]) if vi is not None else None;continue
  if not name or name.startswith(('Sources','Source:','Footnotes:','Invalid','Abstentions','Registered','Parties and','Electoral alliance')):continue
  seats=seat(r[si]) if si is not None and len(r)>si else None
  if si is not None:
   if id(row[si]) in seats_seen:continue
   seats_seen.add(id(row[si]))
  votes=integer(r[vi]) if vi is not None and len(r)>vi and not seatonly else None
  share=number(r[pi]) if pi is not None and len(r)>pi and not seatonly else None
  if vi is not None and id(row[vi]) in votes_seen:votes=None;share=None
  if vi is not None:votes_seen.add(id(row[vi]))
  if seatonly and not seats:continue
  if seats is None and votes is None and share is None:continue
  m=re.search(r'background(?:-color)?\s*:\s*(#[a-f0-9]{6})',row[0].get('style',''),re.I)
  result(e,label+name,votes,share,seats,m.group(1) if m else '#808080')
 entered=e['results'][rows_start:];sumVotes=sum(r['votes'] or 0 for r in entered);sumSeats=sum(r['seats'] or 0 for r in entered)
 if (inst=='senate' or e['startDate'][:4]=='1869') and vi is not None:
  denom=(denom-blank) if denom is not None and blank is not None else denom
  if denom:
   for r in entered:
    if r['votes'] is not None:r['share']=round(r['votes']/denom*100,4)
  e['weightedVotes']=True;e['voteBasis']='Candidate-vote marks, excluding blank ballots; voters may select several candidates'+(f' ({denom:,})' if denom else '')
  e['notes']+='Raw totals count candidate selections, not individual voters. Blank and invalid ballots are separate from the candidate-vote share denominator. '
 elif not seatonly:e['voteBasis']='Valid list/candidate votes including labelled blank ballots'+(f' ({denom:,})' if denom else '; popular-vote denominator unavailable')
 if not seatonly:
  e['totalSeats']=totalSeats;e['resultStatus']='final' if entered else 'not-entered'
  e['resultCoverage']='complete' if denom and sumVotes==denom and totalSeats is not None and sumSeats==totalSeats else 'partial'
  if denom and sumVotes!=denom:e['notes']+=f'Entered votes sum to {sumVotes:,} against the source denominator {denom:,}; the discrepancy remains partial. '
  if totalSeats is not None and sumSeats!=totalSeats:e['notes']+=f'Entered seats sum to {sumSeats} against the source allocation {totalSeats}; coverage remains partial. '
  if totalSeats is not None and sumSeats>totalSeats:
   for r in entered:r['seats']=None
   e['notes']+='Conflicting overfull seat rows are omitted. '
 reconciliation.append(dict(id=e['id'],component=label or 'Main table',voteTotal=denom,recordedVotes=sumVotes,seatTotal=totalSeats,sourceSeatSum=sumSeats,recordedSeats=sum(r['seats'] or 0 for r in entered),blankBallots=blank,ballots=ballots,validBallots=validBallots,seatOnly=seatonly))

extra=json.loads((OUT/'extra-primary-links.json').read_text())
for key,url in extra.items():
 if (CACHE/(key+'.html')).exists():read(key,url)
links=json.loads((OUT/'links.json').read_text());official=json.loads((OUT/'official-historical-links.json').read_text())
# Primary chronology establishes every historical lower-house contest, including
# elections with no complete result table or reliable exact polling day.
for url,title in official.items():
 key=url.rsplit('/',1)[-1];s=read(key,url);m=re.search(r'(\d{1,2})\s+(?:de\s+)?('+'|'.join(ESMONTHS)+r')\s+(?:de\s+)?(\d{4})',title,re.I)
 if m:d,mo,y=m.groups();y=int(y);date=datetime.date(y,ESMONTHS[mo.lower()],int(d)).isoformat();precision='day'
 else:y=int(re.search(r'\d{4}',title).group());date=f'{y}-01-01';precision='year'
 wkeys=[k for k in links if 'general_election' in k and re.search(str(y),k)]
 if y==1836:wkeys=[k for k in wkeys if ('February' if '-02-' in date else 'July' if '-07-' in date else 'October') in k]
 if y==1872:wkeys=[k for k in wkeys if ('April' if '-04-' in date else 'August') in k]
 if y==1843:wkeys=[]
 wiki=wkeys[0] if wkeys else None;ws=read(wiki,links[wiki]) if wiki else None
 if y==1896:date='1896-04-12'
 if y==1903:date='1903-04-26'
 body='Cortes — elected procuradores' if 1834<=y<=1836 and date<'1836-10-01' else 'Cortes of Cádiz' if y<=1813 else 'Cortes' if y<=1822 else 'Congress of Deputies'
 e=base('congress',date,precision,source=dict(label='Congress: official historical election chronology',url=url),body=body)
 if y<=1836:e['electionMethod']='indirect'
 if precision=='year':e['notes']='Polling took place through a historical indirect electoral process; no single exact national polling day is established here. '
 if y<1933:e['notes']+='Historical franchise restrictions and territorial boundaries differ from the modern democratic electorate. '
 if ws:
  e['sources'].append(dict(label='Historical result tables and cited bibliography',url=links[wiki]))
  lead=next((txt(p).split('. ')[0] for p in ws.select('p') if 'held' in txt(p)), '')
  ds=english_dates(lead,y)
  if ds and e['precision']=='day' and ds[0]==date and not('for the Senate' in lead) and len(ds)>1:e['endDate']=ds[1]
  ts=[t for t in tables(ws) if t[3]=='congress']
  if ts:fill(e,ts[0])
  if y==1936:
   e['results']=[];t,g,hi,inst=ts[0];headers=[c['text'] for c in g[hi]];si=next(i for i,v in enumerate(headers) if v=='Seats (May)');ni=max(i for i,v in enumerate(headers) if v=='Party')
   for row in g[hi+1:]:
    if len(row)>si and row[ni]['text'].startswith('Total ') and seat(row[si]['text']) is not None:result(e,row[ni]['text'].removeprefix('Total ').removesuffix(':'),seats=seat(row[si]['text']))
   e['resultStatus']='final';e['resultCoverage']='partial';e['notes']+='Final May seat totals by parliamentary electoral bloc follow the source after later scrutiny and reruns. Detailed party allocations conflict and are not inferred. First-round estimated voter counts and candidate marks are not mixed into this final seat table. '

  box=ws.select_one('table.infobox');bt=txt(box) if box else ''
  n=re.search(r'All ([\d,]+)(?:\s+\[[^]]+\])? seats',bt)
  if n:e['totalSeats']=integer(n.group(1))
  if len(ts)>1 and 1871<=y<=1898:
   for i,t in enumerate(ts[1:],1):fill(e,t,True,f'Overseas component {i} — ')
   e['resultCoverage']='partial';e['notes']+='Additional overseas elected-seat allocations are separate rows; their vote denominators are not mixed into the main table. '
  if y in [1896,1903]:
   e['sources'].insert(0,dict(label='Senate: official electoral decree resolves chronology discrepancy',url=json.loads((OUT/'extra-primary-links.json').read_text())['official-decree-'+str(y)]));e['notes']+='The electoral decree takes precedence over a conflicting date label in the Congress chronology. '
 if not e['results']:e['notes']+='Chronology record: a complete national result allocation is not entered; no party votes or seats are inferred. '
 if e['totalSeats'] is not None and sum(r['seats'] or 0 for r in e['results'])>e['totalSeats']:
  e['notes']+='Source seat allocations conflict; seats are omitted pending reconciliation. ';e['resultCoverage']='partial'
  for r in e['results']:r['seats']=None
 records.append(e)
 # A separately elected historical Senate cannot use the lower-house polling day.
 if ws and 1871<=y<=1923 and y!=1873:
  if y in [1871,1876] or '1872' in str(wiki):
   se=base('senate',date,source=dict(label='Historical electoral law, decree and result bibliography',url=links[wiki]));se.update(precision='unknown',dateStatus='tba',startDate='',id='world-spain-senate-'+date+'-electoral-college',title='Senate — '+(MONTHS and datetime.date.fromisoformat(date).strftime('%B %Y') if y==1872 else date[:4])+' electoral-college election',electionMethod='indirect',totalSeats=200,resultCoverage='partial')
   se['notes']='Indirect election of the historical Senate. The lower-house polling interval does not establish the exact provincial electoral-college day here. Only elected seats are in scope; results are not entered. '
  else:
   lead=next((txt(p).split('. ')[0] for p in ws.select('p') if 'held' in txt(p)), '');ds=english_dates(lead,y);assert len(ds)>=2,(wiki,lead)
   se=base('senate',ds[-1],source=dict(label='Historical Senate election and cited electoral decree',url=links[wiki]));se['electionMethod']='indirect'
   st=[t for t in tables(ws) if t[3]=='senate']
   if st:fill(se,st[0])
   else:se['totalSeats']=180
   se['notes']+='Only the elective Senate component is included. Royal life appointments and senators by right are excluded. Territorial, corporate and provincial electoral colleges differ from a popular national election. '
  e.setdefault('pairedIds',[]).append(se['id']);se.setdefault('pairedIds',[]).append(e['id']);records.append(se)

for wiki,url in links.items():
 m=re.search(r'(\d{4})_Spanish_general_election',wiki)
 if m and int(m.group(1))>=1977:
  s=read(wiki,url);y=int(m.group(1));lead=next(txt(p).split('. ')[0] for p in s.select('p') if 'general election was held' in txt(p));ds=english_dates(lead,y);assert ds
  ts=tables(s)
  for scope in ['congress','senate']:
   e=base(scope,ds[0],source=dict(label='Historical national results and certified-source bibliography',url=url));chosen=[t for t in ts if t[3]==scope];assert chosen,(wiki,scope);fill(e,chosen[0])
   if scope=='senate':e['notes']+='Only directly elected senators are recorded. Royal appointments in 1977 and autonomous-community designations are excluded. '
   if y==1977 and scope=='congress':e['round']='Constituent legislature election'
   records.append(e)
 if 'European_Parliament_election_in_Spain' in wiki:
  s=read(wiki,url);y=int(wiki[:4]);lead=next(txt(p).split('. ')[0] for p in s.select('p') if 'election was held' in txt(p));ds=english_dates(lead,y);assert ds
  e=base('european',ds[0],source=dict(label='European election national results and cited bibliography',url=url));ts=tables(s);assert ts,wiki;fill(e,ts[0]);records.append(e)
 if wiki in ['1967_Spanish_general_election','1971_Spanish_general_election']:
  s=read(wiki,url);y=int(wiki[:4]);date='1967-10-10' if y==1967 else '1971-09-29';e=base('family',date,source=dict(label='Historical restricted family-representative election',url=url));e['totalSeats']=102 if y==1967 else 104;e['round']='Partial elected family representation';e['notes']='Franco-era restricted election of family representatives only, not the whole appointed/corporate Cortes. Eligible voters were heads of family and married women. No competitive party allocation or whole-chamber 564-seat result is inferred.';source=dict(label='Official law on elected family representation',url=links['official-franco-family-law']);e['sources'].insert(0,source);e['legitimacy']=dict(level='uncompetitive',summary='Our assessment: restricted representation under the Franco dictatorship, with a limited family-based franchise and an otherwise appointed/corporate legislature.',reviewed=CHECKED,sources=[source]);records.append(e)

# Reviewed primary results override secondary tables.
cert=json.loads((OUT/'certified-extract.json').read_text());audit.append(dict(file='official-2023-final.pdf',url=cert['source'],sha256=cert['sha256']));primary=dict(label='Junta Electoral Central: certified 2023 national results',url=cert['source'])
c=cert['congress'];e=next(e for e in records if e['id']=='world-spain-congress-2023-07-23');e['results']=[]
# PSOE and its Catalan federation are grouped once; preserve certified originals.
rows=[]
for r in c['rows']:
 if r['name'].startswith('Partit dels Socialistes'):continue
 r=r.copy()
 if r['name'].startswith('Partido Socialista Obrero'):
  psc=next(x for x in c['rows'] if x['name'].startswith('Partit dels Socialistes'));r['votes']+=psc['votes'];r['seats']+=psc['seats'];r['name']='Spanish Socialist Workers’ Party (PSOE–PSC)'
 rows.append(r)
for r in sorted(rows,key=lambda r:-r['votes']):result(e,r['name'],r['votes'],round(r['votes']/c['validBallots']*100,4),r['seats'])
result(e,'Blank ballots',c['blankBallots'],round(c['blankBallots']/c['validBallots']*100,4),0,party='')
e.update(totalSeats=350,resultCoverage='complete',voteBasis=f'Certified valid ballots including blank ballots ({c["validBallots"]:,})',turnout=round(c['ballots']/c['registered']*100,4));e['sources'].insert(0,primary);e['notes']='Certified candidate/list votes and elected seats follow the final JEC proclamation. PSOE and PSC federation votes/seats are grouped once; originals remain in the audit. Blank ballots form part of valid ballots under the official summary and remain a labelled non-party row.'
e=next(e for e in records if e['id']=='world-spain-senate-2023-07-23');e['results']=[];groups={}
def senate_group(p):
 if p.startswith(('PARTIDO POPULAR','PARTIT POPULAR')):return 'People’s Party (PP)'
 if 'PSOE' in p or p=='PARTIDO SOCIALISTA OBRERO ESPAÑOL':return 'Spanish Socialist Workers’ Party (PSOE–PSC)'
 if 'SUMAR' in p:return 'Sumar and allied electoral lists'
 if p.startswith('ESQUERRA REPUBLICANA'):return 'Republican Left of Catalonia (ERC)'
 return p
for candidate in cert['senate']['candidates']:
 p=senate_group(candidate['party']);r=groups.setdefault(p,dict(votes=0,seats=0));r['votes']+=candidate['votes'];r['seats']+=int(candidate['elected'])
for p,r in sorted(groups.items(),key=lambda kv:-kv[1]['votes']):result(e,p,r['votes'],round(r['votes']/cert['senate']['candidateVotes']*100,4),r['seats'])
e.update(totalSeats=208,resultCoverage='complete',voteBasis=f'Certified candidate selections ({cert["senate"]["candidateVotes"]:,}); excludes blank/invalid ballots, not voters',turnout=None,weightedVotes=True);e['sources']=[primary,dict(label='JEC: correction of Santiago Llorente’s vote count',url=cert['correctionSource'])]+e['sources'];e['notes']='All 1,152 certified candidate rows are summed once; 208 are elected. The subsequent official correction sets Santiago Llorente’s count to 1,007,322. Percentages are calculated shares of candidate-vote marks, excluding blank/invalid ballots; voters may choose several candidates. They are not a share of voters. PSOE federations, PP language variants and Sumar electoral alliances are grouped once; the original candidate labels remain in the audit. Autonomous-community senators are excluded; no turnout is inferred from this candidate table.'


# The elected delegation at the constitutive session excludes later treaty changes.
for year,total,counts in [(2009,50,[23,21,2,2,1,1,0]),(2019,54,[20,12,7,6,3,3,2,1,0,0,0])]:
 url=f'https://results.elections.europa.eu/en/national-results/spain/{year}-{year+5}/constitutive-session/'
 primarys=read(f'official-european-{year}',url)
 t=primarys.select('table')[1]
 rows=[[txt(c) for c in r.select('th,td')] for r in t.select('tr')]
 rows=[r for r in rows if len(r)>=2 and number(r[-1]) is not None and r[-1]!='100.00%']
 assert len(rows)==len(counts),(year,rows)
 e=next(e for e in records if e['seriesId']=='es-european' and e['startDate'].startswith(str(year)));e['results']=[]
 for row,seats in zip(rows,counts):result(e,row[0],share=number(row[-1]),seats=seats)
 e.update(totalSeats=total,resultCoverage='complete',resultStatus='final',voteBasis='European Parliament published national-party vote percentages; raw counts not provided')
 e['sources'].insert(0,dict(label='European Parliament: national results at constitutive session',url=url));e['notes']='Original elected delegation at the constitutive session; later Lisbon Treaty or Brexit reallocations are excluded. Published national-party percentages are kept on the European Parliament basis, without mixing secondary raw counts or blank-ballot denominators.'
cert24=json.loads((OUT/'certified-european-2024.json').read_text());e=next(e for e in records if e['id']=='world-spain-european-2024-06-09');e['results']=[]
for r in sorted(cert24['rows'],key=lambda r:-r['votes']):result(e,r['name'],r['votes'],round(r['votes']/cert24['validBallots']*100,4),r['seats'])
result(e,'Blank ballots',cert24['blankBallots'],round(cert24['blankBallots']/cert24['validBallots']*100,4),0,party='')
e.update(totalSeats=61,resultCoverage='complete',resultStatus='final',voteBasis=f'Certified valid ballots including blank ballots ({cert24["validBallots"]:,})',turnout=round(cert24['ballots']/cert24['registered']*100,4))
e['sources']=[dict(label='JEC: certified European election results',url=cert24['source']),dict(label='JEC: corrected PSOE and Junts counts',url=cert24['correctionSource'])]+e['sources'];e['notes']='Certified JEC totals with the subsequent official correction transferring 157 votes from Junts to PSOE. Valid ballots include labelled blank ballots. The 61-seat allocation is unchanged by that correction.'
for key,url in [('official-european-2024-certified',cert24['source']),('official-european-2024-correction',cert24['correctionSource']),('official-2023-final','https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-18907'),('official-2023-correction',cert['correctionSource'])]:read(key,url)
# National head-of-state ballots are separate from parliamentary and citizen stages.
e=base('king','1870-11-16',source=dict(label='Congress: election of Amadeo I by the Cortes',url=extra['official-sexennium']))
for name,v in [('Amadeo of Savoy',191),('Federal Republic',60),('Duke of Montpensier',27),('Baldomero Espartero',8),('Alfonso of Bourbon',2),('Unitary Republic',2),('Blank ballots',19)]:result(e,name,v,party='',winner=name=='Amadeo of Savoy')
e.update(resultStatus='final',voteBasis='Itemized parliamentary votes; complete ballot denominator not established',notes='The official Congress historical summary itemizes 309 votes. It does not establish a complete participating-ballot denominator here, so no percentages or missing votes are inferred. This was an indirect election of a monarch by the Cortes, not a popular vote.');records.append(e)
e=base('president','1931-12-10',source=dict(label='Congress: election of Niceto Alcalá-Zamora',url=extra['official-1931-presidential']));result(e,'Niceto Alcalá-Zamora',362,round(362/410*100,4),party='',winner=True)
e.update(resultStatus='final',voteBasis='410 participating parliamentary votes',notes='The Congress source states 362 votes from 410 participating deputies. Only the confirmed winning tally is entered; other choices and abstentions are not inferred. Indirect election by the constituent Cortes.');records.append(e)
presurl='https://www.boe.es/datos/pdfs/BOE/1936/132/B01379-01379.pdf'
audit.append(dict(file='official-1936-presidential.pdf',url=presurl,sha256=hashlib.sha256((CACHE/'official-1936-presidential.pdf').read_bytes()).hexdigest()))
e=base('president','1936-05-10',source=dict(label='Gaceta de Madrid: official proclamation of Manuel Azaña',url=presurl));result(e,'Manuel Azaña',754,round(754/847*100,4),party='',winner=True)
e.update(resultStatus='final',voteBasis='847 participating electoral-assembly votes',notes='The official proclamation states 754 votes out of 847 cast, in an assembly with 911 members. The winning tally is confirmed; other choices are not inferred. This indirect ballot combined deputies and citizen-elected compromisarios, whose election is linked separately.');records.append(e)
ce=base('electors','1936-04-26',source=dict(label='Historical citizen-elector election and electoral-law bibliography',url=extra['1936-presidential-electors']));ce.update(totalSeats=473,notes='Direct election of the citizen compromisarios who joined deputies in the presidential electoral assembly. A complete certified national party allocation is not established here; approximate bloc ranges are not converted into exact results. The later assembly ballot is a separate linked record.');ce['pairedIds']=[e['id']];e['pairedIds']=[ce['id']];records.append(ce)
# Preserve existing confirmed Calendar IDs, updating only scope and related chambers.
for row in json.loads((OUT/'pre-import-backup.json').read_text()):
 if row['kind']!='world_election':continue
 e=row['data'].copy();scope='congress' if 'congress' in row['id'] else 'senate';e.update(seriesId='es-'+scope,totalSeats=350 if scope=='congress' else 209,checked=CHECKED,version=1)
 e['notes']+=' Only elected seats are counted; Senate autonomous-community designations are excluded.'
 if scope=='senate':e['sources'].append(dict(label='2026 constitutional reform: Formentera separate elected senator',url='https://www.boe.es/buscar/doc.php?id=BOE-A-2026-10881'));e['notes']+=' The 2026 constitutional reform separates Ibiza and Formentera, raising directly elected seats from 208 to 209.';e['summary']=f'Confirmed national election: {e["totalSeats"]} elected seats.';records.append(e)
colors=[('popular','#1D84CE'),('socialist','#E30613'),('socialista','#E30613'),('VOX','#63BE21'),('Sumar','#E51C55'),('SUMAR','#E51C55'),('Republican Left','#FFB232'),('ESQUERRA','#FFB232'),('Junts','#20C0BE'),('JUNTS','#20C0BE')]
for e in records:
 if e['startDate']>='1977' and e['status']=='held':
  for r in e['results']:
   if r['color']=='#808080':
    for word,color in colors:
     if word.lower() in r['name'].lower():r['color']=color;break

for e in records:
 for i,r in enumerate(e['results']):r['id']=e['id']+'-'+str(i+1)
 e['linkedElectionIds']=list(dict.fromkeys(e.pop('pairedIds',[])+[x['id'] for x in records if x['id']!=e['id'] and e['precision']=='day' and x['precision']=='day' and x['startDate']==e['startDate']]))
 e['summary']=e['body']+(': '+str(e['totalSeats'])+' elected seats.' if e['totalSeats'] is not None else ': historical national election.')
records.sort(key=lambda e:(e['startDate'],e['id']));assert len(set(e['id'] for e in records))==len(records)
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,sources=audit),indent=2)+'\n');(OUT/'reconciliation.json').write_text(json.dumps(reconciliation,indent=2)+'\n')
print('Built',len(records),collections.Counter(e['seriesId'] for e in records));print('No results',[e['id'] for e in records if not e['results']]);print('Seats',[(e['id'],sum(r['seats'] or 0 for r in e['results']),e['totalSeats']) for e in records if e['totalSeats'] is not None and sum(r['seats'] or 0 for r in e['results'])!=e['totalSeats']])

(OUT/'final-reconciliation.json').write_text(json.dumps([dict(id=e['id'],voteBasis=e['voteBasis'],voteSum=sum(r['votes'] or 0 for r in e['results']),shareSum=round(sum(r['share'] or 0 for r in e['results']),4),seatSum=sum(r['seats'] or 0 for r in e['results']),totalSeats=e['totalSeats'],coverage=e['resultCoverage']) for e in records],indent=2)+'\n')
