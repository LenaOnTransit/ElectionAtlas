"""Reproduce Romania's national election archive using existing WorldElection models.

No database writes. Reviewed source tables preserve cell identities for coalitions.
Unverified dates, missing results and incompatible voting colleges stay explicit.
"""
from pathlib import Path
import json,re,uuid,hashlib,colorsys

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/romanian-election-import'
DATA=json.loads((OUT/'source-tables.json').read_text());LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-12'
INVENTORY='https://www.enciclopediaromaniei.ro/wiki/Portal%3APolitic%C4%83'
SENATE_HISTORY='https://www.senat.ro/PAGINI/150/Stiati%20ca.html'
CHAMBER_HISTORY='https://www.cdep.ro/ords/pls/dic/site2015.page?den=istorie1'
CCR_ANNULMENT='https://legislatie.just.ro/Public/FormaPrintabila/00000G1NL9GYDZBK3E1028VNFCO1OA4E'
CCR_2025=['https://legislatie.just.ro/public/DetaliiDocument/297874','https://legislatie.just.ro/Public/DetaliiDocument/298229']
records=[];profiles={};audit=[]
PALETTE={'Social Democratic Party':'#c9232b','National Liberal Party':'#edc324','Democratic Union of Hungarians in Romania':'#278643','Alliance for the Union of Romanians':'#dab42b','Save Romania Union':'#1687b8','S.O.S. Romania':'#17385d','Party of Young People':'#855094','Romanian Communist Party':'#c6202b','Romanian Workers Party':'#c6202b','National Salvation Front':'#315faa'}
def num(s):
 s=s.replace(',','').replace('\xa0','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def clean(s):return re.sub(r'\s*\[(?:ro|de|hu|en|pl)\]','',s).strip()
def profile(name,year,url):
 name=clean(name)
 if name=='Conservative-Democratic Party' and year==1911:url=LINKS['1912_Romanian_general_election'] # shared profile bibliography remains stable
 name={'Democratic Alliance of Hungarians in Romania':'Democratic Union of Hungarians in Romania'}.get(name,name)
 if not name or name in ('Independent','Independents','Independent groups') or name.lower().startswith(('other','against','disputed','institutional','rightful')):return None
 key=('historical:' if year<1990 else 'modern:')+name
 if key not in profiles:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff
  color=PALETTE.get(name,'#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.42,.58)))
  profiles[key]={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/ro/'+key)),'country_id':'ro','name':name if year>=1990 else name+' — historical','short_name':name[:100],'color':color,'ideology_ids':[],'archived':False,'notes':'Election-era party, front or alliance label. No continuity with a similarly named organisation is inferred. Source: '+url+'. Display colour is an editorial palette; no official-branding or ideological assessment is implied.'}
 return profiles[key]
def result(e,name,votes=None,share=None,seats=None,party=None):
 name=clean(name);pname=name if party is None else clean(party);p=profile(pname,int(e['startDate'][:4]),e['sources'][0]['url'])
 r=dict(id=e['id']+'-row-'+str(len(e['results'])+1),name=name,party=pname,color=p['color'] if p else '#808080',votes=votes,share=share,seats=seats,electoralVotes=None,winner=False,advanced=False,ideologyIds=[])
 if p:r['partyId']=p['id']
 e['results'].append(r);return r
def base(date,office,url,precision='day',end=''):
 year=int(date[:4]);body={'chamber':'Assembly of Deputies' if year<=1918 else 'Chamber of Deputies','senate':'Senate','assembly':'Great National Assembly','parliament':'Parliament','president':'President of Romania'}[office]
 if year==1946:body='Assembly of Deputies'
 return dict(id=f'world-romania-{office}-{date}',countryId='ro',title=body,type='presidential' if office=='president' else 'parliamentary',body=body,startDate=date,endDate=end,precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='ro-'+office,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='No verified national result table entered',results=[],sources=[dict(label='Election history and source bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=2,electionMethod='direct',live=dict(enabled=False,reporting=None,unit='precincts',bulletin='',updated=''))
def header(t):
 return next((i,[c['text'] for c in row]) for i,row in enumerate(t['rows']) if 'Votes' in [c['text'] for c in row] or 'Seats' in [c['text'] for c in row])
def meta(t,vi,si=None):
 answer={}
 for row in t['rows']:
  texts=[c['text'] for c in row];labels={s for s in texts[:vi] if s and num(s) is None and s not in ('–','—','-')}
  for key in ('Total','Registered voters/turnout'):
   if labels=={key}:
    answer[key]=dict(votes=integer(texts[vi]) if len(texts)>vi else None,seats=integer(texts[si]) if si is not None and len(texts)>si else None,share=num(texts[vi+1]) if len(texts)>vi+1 else None)
 return answer
def reconcile(e,valid=None):
 vs=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results'])
 audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=vs,expectedSeats=e['totalSeats'],recordedSeats=ss,coverage=e['resultCoverage'],source=e['sources'][0]['url']))
def parliamentary(e,t,year):
 hi,h=header(t);si=h.index('Total seats') if 'Total seats' in h else h.index('Seats');vi=h.index('Votes') if 'Votes' in h else si
 if year==1928 and e['body']=='Senate':
  # Universal-college mandates have a verified common scope; the full-chamber
  # table mixes institutions and contains an inconsistent Magyar total.
  for row in t['rows'][2:]:
   tx=[c['text'] for c in row]
   if tx[0]=='Total':break
   if len(tx)>2 and integer(tx[2]) is not None:result(e,tx[1],seats=integer(tx[2]))
  e.update(title='Senate — universal-college election',totalSeats=113,resultStatus='final',resultCoverage='complete',voteBasis='113 universal-college elected mandates; other Senate membership excluded')
  e['notes']='The Senate also included indirectly selected and institutional/rightful senators. Only the 113 universal-college mandates are entered: 110 National Peasants’ Party and 3 Magyar Party. The secondary full-chamber table contains inconsistent component totals; it is not treated as a verified whole-Senate snapshot.'
  reconcile(e);return
 m=meta(t,vi,si);control=m.get('Total',{});valid=control.get('votes') if vi!=si else None
 mixed=len([x for x in h if x=='Votes'])>1
 if mixed:valid=None # 1922 multi-member vote marks and single-member ballots
 groups={};vseen=set();sseen=set()
 for row in t['rows'][hi+1:]:
  tx=[c['text'] for c in row]
  if len(tx)<=si:continue
  names=[]
  for x in tx[:min(vi,si)]:
   if x and x not in names:names.append(x)
  if not names:continue
  if names==['Total']:break
  if 'Total' in names or any(x.startswith(('Source:','Registered','Valid votes','Invalid','Total votes')) for x in names):continue
  name=names[0];v=integer(tx[vi]) if vi!=si and not mixed else None;seat=integer(tx[si]);seat=0 if seat is None and tx[si] in ('–','—','-') else seat
  if v is None and seat is None:continue
  x=groups.setdefault(name,dict(votes=None,seats=0,seatKnown=True))
  if v is not None and row[vi]['cell'] not in vseen:x['votes']=(x['votes'] or 0)+v;vseen.add(row[vi]['cell'])
  if seat is not None and row[si]['cell'] not in sseen:x['seats']+=seat;sseen.add(row[si]['cell'])
  elif seat is None:x['seatKnown']=False
 e['totalSeats']=control.get('seats')
 for name,x in groups.items():result(e,name,x['votes'],round(x['votes']/valid*100,6) if valid and x['votes'] is not None else None,x['seats'] if x['seatKnown'] else None)
 vs=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results'])
 e['resultStatus']='final' if e['results'] else 'not-entered';e['resultCoverage']='complete' if e['results'] and e['totalSeats'] is not None and ss==e['totalSeats'] and (valid is None or vs==valid) else 'partial'
 e['turnout']=m.get('Registered voters/turnout',{}).get('share') if vi!=si and not mixed else None
 e['voteBasis']=f'Valid votes in this chamber ({valid:,}); separate chamber ballot denominator' if valid else 'Reported seat allocation; no comparable national party-vote denominator entered'
 e['notes']='Election-era list/front labels are retained. Shared coalition cells are counted once; constituent seats are grouped under the common list. No ideology or legal organisational continuity is inferred. '
 if mixed:e['notes']+='The source separates multi-member vote marks (9,604,139) and single-member ballots (621,044). These are incomparable denominators; only total party seats are entered. '
 if e['body']=='Senate' and year<1940:e['notes']+='Seat capacity describes the elected mandates in this source table, not a verified total including every senator by right. Institutional and appointed members are not assigned invented party results. ';e['sources'].append(dict(label='Senate: electoral and constitutional history',url=SENATE_HISTORY))
 if year==1907:
  e['resultCoverage']='partial';e['notes']+='This table is an interim announcement: 90 Liberal seats, 10 Conservative seats and 2 disputed seats. The disputed mandates have no party assigned. It is not a complete final Senate allocation.';e['resultStatus']='provisional'
 if 1948<=year<=1985:
  e['round']='Single-front election';e['voteBasis']=f'Declared front/against ballot outcomes / {valid:,} valid ballots; not competitive party shares' if valid else 'Declared single-front seat allocation'
  e['notes']+='A noncompetitive Communist-era election. The front’s vote is not attributed to constituent parties; declared official totals do not establish freely expressed voter preferences. '
 if year==1939:e['notes']+='Held under Carol II’s royal dictatorship with the National Renaissance Front as the permitted organisation; not a competitive multi-party election. '
 if year==1946:e['notes']+='These are historically declared results of an election affected by large-scale falsification and repression; they are not a reconstruction of genuine voter preferences. '
 if year<1919:e['notes']+='Restricted franchise and voting colleges applied. Dates with uncertain Julian/Gregorian conversion are displayed only to month or year precision. '
 if e['totalSeats'] is not None and ss!=e['totalSeats']:e['notes']+=f'Entered rows account for {ss} of {e["totalSeats"]} source-scoped seats; missing mandates are not assigned to an invented residual party. '
 if valid is not None and vs!=valid:e['notes']+=f'Entered vote rows total {vs:,}, compared with the source denominator {valid:,}; coverage remains partial. '
 e['summary']='Declared election results; historical scope and limitations are explained in the notes.'
 reconcile(e,valid)

# National parliamentary event inventory, including separate early dissolutions.
# Month/year precision deliberately avoids fake exact-day confirmations.
EARLY=[(1864,11,'chamber'),(1866,4,'chamber'),(1866,11,'both'),(1867,12,'both'),(1868,7,'senate'),(1869,3,'chamber'),(1869,8,'senate'),(1870,0,'parliament'),(1871,0,'parliament'),(1874,0,'senate'),(1875,0,'parliament'),(1876,0,'parliament'),(1877,0,'senate'),(1879,5,'parliament'),(1883,4,'parliament'),(1884,11,'parliament'),(1888,1,'parliament'),(1888,10,'parliament'),(1891,4,'both'),(1892,2,'both'),(1895,11,'parliament'),(1899,5,'parliament'),(1901,3,'both'),(1905,2,'both'),(1907,6,'both'),(1911,3,'both'),(1912,11,'both'),(1914,2,'parliament'),(1914,5,'both'),(1918,5,'both')]
LATE={1919:('11-04','11-08'),1920:('05-25','05-27'),1922:('03-01','03-03'),1926:('05-25','05-27'),1927:('07-07','07-14'),1928:('12-12','12-19'),1931:('06-01','06-08'),1932:('07-17','07-26'),1933:('12-20','12-29'),1937:('12-20','12-28'),1939:('06-01','06-02'),1946:('11-19',''),1948:('03-28',''),1952:('11-30',''),1957:('02-03',''),1961:('03-05',''),1965:('03-07',''),1969:('03-02',''),1975:('03-09',''),1980:('03-09',''),1985:('03-17',''),1990:('05-20',''),1992:('09-27',''),1996:('11-03',''),2000:('11-26',''),2004:('11-28',''),2008:('11-30',''),2012:('12-09',''),2016:('12-11',''),2020:('12-06',''),2024:('12-01','')}
def source_key(year):
 return next((k for k in DATA if k.startswith(str(year)) and ('general' in k or 'parliamentary' in k or 'Senate' in k)),None)
for year,month,scope in EARLY:
 key=source_key(year);url=LINKS[key] if key else INVENTORY
 if year==1914 and month==2:key=None;url=INVENTORY
 offices=['chamber','senate'] if scope=='both' else [scope]
 for office in offices:
  e=base(f'{year}-{month or 1:02}-01',office,url,'month' if month else 'year')
  ts=DATA[key]['tables'] if key else []
  chosen=[t for t in ts if t['heading']==('Senate' if office=='senate' else 'Assembly of Deputies' if year==1990 else 'Chamber of Deputies')]
  if chosen:parliamentary(e,chosen[0],year)
  elif year==1911:
   allocation=[('Conservative Party',160),('National Liberal Party',10),('Conservative-Democratic Party',10),('Independents',2)] if office=='chamber' else [('Conservative Party',85),('National Liberal Party',16),('Conservative-Democratic Party',11)]
   e.update(totalSeats=183 if office=='chamber' else 112,resultStatus='final',resultCoverage='partial' if office=='chamber' else 'complete',voteBasis='Final reported elected-seat allocation; college-level votes are not combined')
   for name,seats in allocation:result(e,name,seats=seats)
   e['summary']='Final reported seat allocation after all voting stages and ballotage.'
   e['notes']='The source reports 160 Conservative, 10 Liberal, 10 Conservative-Democratic and 2 independent deputies: 182 of 183 elected mandates. The unaccounted mandate is not assigned to an invented party. Senate elected mandates reconcile at 85, 16 and 11 respectively, totalling 112. No aggregate popular vote is entered because electors and vote marks from different colleges/chambers are incomparable. Institutional senators are outside these elected-seat totals.'
   reconcile(e)
  else:
   e['summary']='Documented historical election; a verified national result table is not yet available.'
   e['notes']='The event is retained in the national timeline. Exact polling days, party votes, seat capacity and allocations are not inferred from later parliamentary composition. Month/year display precision is intentional; the internal first-day date is only a sorting anchor. Restricted franchise and historical voting colleges must be considered before entering results.'
   reconcile(e)
  if year==1869 and office=='senate':e['sources'].append(dict(label='Senate: August 1869 dissolution election',url=SENATE_HISTORY))
  if year==1914 and month==2:e['sources'].append(dict(label='Rădulescu: February 1914 elections, Studia Politica 5(1), 2005',url='https://www.ssoar.info/ssoar/bitstream/handle/document/56278/ssoar-sp-rpsr-2005-1-radulescu-Alegeri_parlamentare_inainte_de_razboi.pdf?isAllowed=y&sequence=1'))
  if year==1864:e['notes']+=' The Senate established under Cuza was appointed, so no popular Senate election is invented.'
  if year==1866 and month==4:e['sources'].append(dict(label='Senate: April 1866 election of a single chamber',url=SENATE_HISTORY))
  records.append(e)
for year,(start,end) in LATE.items():
 key=source_key(year);assert key,year
 offices=['assembly'] if 1948<=year<=1985 else ['chamber'] if year==1946 else ['chamber','senate']
 for office in offices:
  e=base(f'{year}-{start}',office,LINKS[key],end=f'{year}-{end}' if end else '')
  ts=DATA[key]['tables'];heading='Results' if office=='assembly' or year==1946 else 'Senate' if office=='senate' else 'Assembly of Deputies' if year==1990 else 'Chamber of Deputies'
  t=next(t for t in ts if t['heading']==heading);parliamentary(e,t,year)
  if year==1919:e['notes']+='Voting was staggered by chamber and territory between 4 and 8 November. These are regional elected-seat allocations; uncontested seats and different regional systems prevent inventing a nationwide party popular vote. '
  if year>=1990:e['notes']+='Minority representative mandates are retained in the Chamber allocation. Historical chamber size is taken from that election’s table, not today’s statutory allocation. '
  records.append(e)

PRES={1990:['05-20'],1992:['09-27','10-11'],1996:['11-03','11-17'],2000:['11-26','12-10'],2004:['11-28','12-12'],2009:['11-22','12-06'],2014:['11-02','11-16'],2019:['11-10','11-24'],2024:['11-24'],2025:['05-04','05-18']}
for year,dates in PRES.items():
 key=f'{year}_Romanian_general_election' if year<=2004 else f'{year}_Romanian_presidential_election'
 ts=DATA[key]['tables'];t=next(t for t in ts if t['heading'] in ('President','Results'));hi,h=header(t);vis=[i for i,x in enumerate(h) if x=='Votes'];ci=max(i for i,x in enumerate(h) if x=='Candidate');pi=h.index('Party')
 for round_index,md in enumerate(dates):
  e=base(f'{year}-{md}','president',LINKS[key]);e['round']='First round' if len(dates)>1 or year==2024 else 'General'
  if round_index:e['round']='Runoff'
  vi=vis[round_index];m=meta(t,vi);valid=m['Total']['votes']
  for row in t['rows'][hi+1:]:
   tx=[c['text'] for c in row]
   if len(tx)<=vi:continue
   if tx[ci]=='Total':break
   v=integer(tx[vi])
   if v is not None and tx[ci] not in ('','Candidate'):result(e,tx[ci],v,round(v/valid*100,6),party=tx[pi])
  e.update(resultStatus='final',resultCoverage='complete' if sum(r['votes'] for r in e['results'])==valid else 'partial',turnout=m.get('Registered voters/turnout',{}).get('share'),voteBasis=f'Candidate votes / {valid:,} valid ballots in this round')
  e['notes']='Every round uses a separate valid-ballot denominator. Candidate party/support labels reflect the election-era source; independent candidates remain independent. No ideology is inferred. '
  ranked=sorted(e['results'],key=lambda r:r['votes'],reverse=True)
  if year==2024:
   e['title']='President of Romania — annulled first round';e['round']='Annulled first round';e['status']='cancelled'
   e['notes']+='The first round was held on 24 November, but CCR Decision 32 of 6 December annulled the entire presidential process. The recorded ballot counts are historical annulled returns, not a valid election outcome. No candidate is marked elected or advanced. The planned 8 December runoff was cancelled. '
   e['sources'].insert(0,dict(label='CCR Decision 32: annulment of the 2024 presidential process',url=CCR_ANNULMENT))
   e['summary']='Annulled ballot returns, retained for historical reference; no valid winner.'
  elif e['round']=='First round':
   for r in ranked[:2]:r['advanced']=True
   e['summary']='The two leading candidates advanced to the separately recorded runoff.'
  else:ranked[0]['winner']=True;e['summary']=ranked[0]['name']+' was elected President.'
  if year==2025:
   e['sources'].insert(0,dict(label='CCR: certified candidate totals and validation',url=CCR_2025[round_index]))
   # Certified turnout uses the Court's final register/attendance, not the live
   # reporting denominator copied into secondary tables.
   registered,attendance=(17996367,9571899) if round_index==0 else (17996537,11641999)
   e['turnout']=round(attendance/registered*100,6)
   e['notes']+='Candidate totals were cross-checked against the CCR’s final validation decision. Turnout uses certified attendance divided by the final permanent-register denominator; overseas/supplementary voters are included in attendance. '
  records.append(e);reconcile(e,valid)

e=base('2024-12-08','president',CCR_ANNULMENT);e.update(title='President of Romania — cancelled runoff',round='Cancelled runoff',status='cancelled',summary='The planned runoff did not take place after the entire electoral process was annulled.',notes='The 8 December runoff was cancelled by the annulment of the 2024 presidential process. Overseas polling had begun before cancellation, but no certified runoff result exists; no votes or winner are invented.')
records.append(e);reconcile(e)

# Indirect, noncompetitive presidential selections. The reported unanimous
# choice is known, but no attendance/ballot count is invented.
INDIRECT=[('1974-03-28','https://www.iiccmer.ro/comunism/cronologie/'),('1975-03-17','https://www.bibliotecadeva.ro/periodice/scanteia/1975/03/scanteia_1975_03_10131.pdf'),('1980-03-28','https://www.iiccmer.ro/comunism/cronologie/'),('1985-03-29','https://lege5.ro/Gratuit/g44tgmjq/discorsu-nr-1-1985-rostit-de-tovarasul-nicolae-ceausescu-cu-prilejul-realegerii-sale-in-supreme-position-of-president-of-rsr')]
for date,url in INDIRECT:
 e=base(date,'president',url);e.update(electionMethod='indirect',round='Assembly selection',resultStatus='final',summary='The Great National Assembly selected Nicolae Ceaușescu in a noncompetitive indirect election.',voteBasis='Assembly selection; verified individual ballot counts unavailable',notes='The President was chosen by the Communist-controlled Great National Assembly, not by a nationwide popular presidential ballot. The office was established in 1974. The selected candidate is recorded, but votes, turnout and vote share remain null because attendance and exact ballot totals are unverified. This is partial numerical coverage, not an outstanding live election.')
 result(e,'Nicolae Ceaușescu',party='Romanian Communist Party')['winner']=True;records.append(e);reconcile(e)

primary=json.loads((OUT/'primary-reconciliation.json').read_text())
for p in primary:
 e=next(e for e in records if e['id']==p['id'])
 assert sum(r['votes'] for r in e['results'])==p['validVotes']
 for r in e['results']:assert r['votes']==p['candidates'][r['name']],(e['id'],r['name'])
for e in records:
 if int(e['startDate'][:4])<1919:e.pop('electionMethod',None) # mixed colleges or selection methods not reduced to one method
 # Link chamber/round records within a year, never combine their denominators.
 peers=[x['id'] for x in records if x['id']!=e['id'] and x['startDate'][:4]==e['startDate'][:4]]
 if peers:e['linkedElectionIds']=peers
 assert sum(r['share'] or 0 for r in e['results'])<=100.2,e['id']
 if e['totalSeats'] is not None:assert sum(r['seats'] or 0 for r in e['results'])<=e['totalSeats'],e['id']
records.sort(key=lambda e:(e['startDate'],e['body']))
for name,obj in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('Built',len(records),'records,',len(profiles),'party/front profiles.')
print('Missing results',len([e for e in records if e['status']=='held' and not e['results']]))
print('Partial result tables',[(e['id'],e['resultStatus']) for e in records if e['results'] and e['resultCoverage']=='partial'])
