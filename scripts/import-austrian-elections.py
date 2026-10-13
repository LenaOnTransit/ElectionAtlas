"""Reproduce the Austrian archive using existing election and party models; no database writes."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/austrian-election-import'
DATA=json.loads((OUT/'source-tables.json').read_text());LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-13'
records=[];profiles={};audit=[]
PALETTE={"Austrian People's Party":"#63c3d0","Social Democratic Party of Austria":"#e30613","Socialist Party of Austria":"#e30613","Freedom Party of Austria":"#005ca9","The Greens":"#84b414","NEOS":"#e84188","Communist Party of Austria":"#b8272d","KPÖ Plus":"#b8272d","Christian Social Party":"#202020","Social Democratic Workers' Party":"#ce2633","Federation of Independents":"#4678a8","Alliance for the Future of Austria":"#ef7a22"}
def num(s):
 s=s.replace(',','').replace('\xa0','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def clean(s):return re.sub(r'\s*\[(?:ro|de|hu|en|pl)\]','',s).strip()
def profile(name,year,url):
 name=clean(name)
 if not name or name in ('Independent','Independents','Independent groups') or name.lower().startswith(('other','against','disputed','institutional','rightful','unknown','split','independent','vacant')):return None
 key=('historical:' if year<1945 else 'modern:')+name
 if key not in profiles:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff
  color=PALETTE.get(name,'#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.42,.58)))
  profiles[key]={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/at/'+key)),'country_id':'at','name':name if year>=1945 else name+' — historical','short_name':name[:100],'color':color,'ideology_ids':[],'archived':False,'notes':'Election-era party, front or alliance label. No continuity with a similarly named organisation is inferred. Source: '+url+'. Display colour is an editorial palette; no official-branding or ideological assessment is implied.'}
 return profiles[key]
def result(e,name,votes=None,share=None,seats=None,party=None):
 name=clean(name);pname=name if party is None else clean(party);p=profile(pname,int(e['startDate'][:4]),e['sources'][0]['url'])
 r=dict(id=e['id']+'-row-'+str(len(e['results'])+1),name=name,party=pname,color=p['color'] if p else '#808080',votes=votes,share=share,seats=seats,electoralVotes=None,winner=False,advanced=False,ideologyIds=[])
 if p:r['partyId']=p['id']
 e['results'].append(r);return r
def base(date,office,url,precision='day',end=''):
 body={'parliament':'National Council','assembly':'Constituent National Assembly','imperial':'Imperial Council — House of Representatives','reichstag':'Constituent Reichstag','president':'Federal President of Austria'}[office]
 return dict(id=f'world-austria-{office}-{date}',countryId='at',title=body,type='presidential' if office=='president' else 'parliamentary',body=body,startDate=date,endDate=end,precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='at-'+office,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='No verified national result table entered',results=[],sources=[dict(label='Election results and historical bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=2,electionMethod='direct',live=dict(enabled=False,reporting=None,unit='precincts',bulletin='',updated=''))
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

BMI_HISTORY='https://www.bmi.gv.at/412/nationalratswahlen/historischer_rueckblick.aspx'
BMI_PRES='https://www.bmi.gv.at/412/bundespraesidentenwahlen/historischer_rueckblick.html'
PARLIAMENT='https://www.parlament.gv.at/verstehen/historisches/wahlen/geschichte-des-wahlrechts/index.html'
def parliamentary(e,t,year):
 hi,h=header(t);vi=h.index('Votes') if 'Votes' in h else None;si=h.index('Seats') if 'Seats' in h else None
 control=meta(t,vi,si).get('Total',{}) if vi is not None else {}
 valid=control.get('votes');e['totalSeats']=control.get('seats')
 imperial=year<1919;group='';groups={};vseen={};sseen=set()
 for row in t['rows'][hi+1:]:
  tx=[c['text'] for c in row]
  if len(tx)<len(h):continue
  if tx[0]=='Total':break
  # Expanded colspan section headings must never become result rows.
  if len(set(tx))==1:group=tx[0];continue
  names=list(dict.fromkeys(x for x in tx[:vi or si] if x))
  if not names or 'Total' in names:continue
  name=names[0]
  if name.startswith(('Source:','Registered','Valid votes','Invalid','Total votes')):continue
  if imperial and group and group not in ('Other','Unknown or split'):name+=' — '+group
  v=integer(tx[vi]) if vi is not None and not (imperial and year<1907) else None
  seat=integer(tx[si]) if si is not None else None
  if si is not None and tx[si] in ('–','—','-'):seat=0
  if v is None and seat is None:continue
  # Shared vote cells describe a common alliance/aggregate, never each member.
  vk=row[vi]['cell'] if vi is not None else None
  if v is not None and vk in vseen:
   prior=vseen[vk];groups[prior]['seats']+=seat or 0
   if name not in groups[prior]['members']:groups[prior]['members'].append(name)
   continue
  x=groups.setdefault(name,dict(votes=None,seats=0 if si is not None else None,members=[name]))
  if v is not None:x['votes']=(x['votes'] or 0)+v;vseen[vk]=name
  if seat is not None and row[si]['cell'] not in sseen:x['seats']+=seat;sseen.add(row[si]['cell'])
 for name,x in groups.items():
  label=' / '.join(x['members'])
  result(e,label,x['votes'],round(x['votes']/valid*100,6) if valid and x['votes'] is not None else None,x['seats'])
 if imperial and year<1907:valid=None;e.pop('electionMethod',None)
 vs=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results'])
 e.update(resultStatus='final' if e['results'] else 'not-entered',resultCoverage='complete' if e['results'] and e['totalSeats'] is not None and ss==e['totalSeats'] and (valid is None or vs==valid) else 'partial',voteBasis=f'Party/list votes / {valid:,} valid ballots' if valid else 'Reported seat allocations; curial votes are not comparable national popular shares',summary='Historical election returns; scope and ballot denominator are documented in the notes.')
 e['notes']='Election-era list and alliance labels are retained. Shared cells are counted once; votes are not duplicated across constituent parties. Display colours are editorial and no organisational continuity or ideology is inferred. '
 if not imperial:
  e['turnout']=meta(t,vi,si).get('Registered voters/turnout',{}).get('share')
  e['sources'].append(dict(label='Interior Ministry: national election chronology and historical returns',url=BMI_HISTORY))
 else:
  e['notes']+='This election covered historical Cisleithanian crown lands beyond modern Austrian borders. National-group qualifiers distinguish similarly named organisations. Before 1907, weighted curiae and indirect rural voting make aggregate popular percentages inappropriate; those votes and shares remain null. The House of Lords was not a nationwide elected chamber. '
  e['sources'].append(dict(label='Austrian Parliament: historical electoral systems',url=PARLIAMENT))
 if e['totalSeats'] is not None and ss!=e['totalSeats']:e['notes']+=f'Entered rows account for {ss} of {e["totalSeats"]} source-scoped seats; unaccounted mandates remain unassigned. '
 if valid and vs!=valid:e['notes']+=f'Entered vote rows total {vs:,} against {valid:,}; coverage remains partial. '
 return valid

MONTHS={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
def first_date(text,year):
 m=re.search(r'(\d{1,2}) ('+'|'.join(MONTHS)+r') '+str(year),text)
 assert m,(year,text[:150])
 return f'{year}-{MONTHS[m[2]]:02}-{int(m[1]):02}'

# All republican parliamentary cycles, with source-scoped membership snapshots.
for key,item in DATA.items():
 if not ('Austrian_legislative' in key or 'Constituent_Assembly' in key):continue
 year=int(key[:4]);date=first_date(item['infobox'],year);e=base(date,'assembly' if year==1919 else 'parliament',LINKS[key])
 valid=parliamentary(e,item['tables'][0],year)
 if year==1919:
  e['title']='Constituent National Assembly — election and membership snapshot'
  e['notes']+='The 170-member allocation includes representatives subsequently appointed for territories where voting could not take place. Only 159 were initially elected; this is a source-scoped membership snapshot, not 170 directly elected mandates. Territorial claims and control differed from present-day Austria. '
  e.pop('electionMethod',None)
 if year==1920:
  e['endDate']='1922-06-18';e['round']='General and delayed regional polls'
  e['notes']+='Voting in Carinthia took place on 19 June 1921 and in Burgenland on 18 June 1922. The 183-seat table describes the completed cycle, not the 174 members initially elected in October 1920. '
 if year in (1970,1995):
  e['endDate']='1970-10-04' if year==1970 else '1996-10-13';e['round']='General and regional repeat polls'
  e['notes']+='The final national allocation incorporates court-ordered regional repeat voting on '+e['endDate']+'. The regional repeat is not invented as a second nationwide general election. '
 records.append(e);e['_valid']=valid

# Imperial assemblies used changing territory and restricted/curial systems.
IMPERIAL_HISTORY='https://www.historickycasopis.sk/42024/lutz-georgi-political-representation-and-social-transformations-in-austria-hungary-case-study-german-elected-deputies-from-transylvania-and-bohemia-1867-1918.pdf'
for year,month in [(1848,6),(1861,0),(1867,0),(1870,0),(1871,0),(1873,0),(1879,0),(1885,6),(1891,0),(1897,3),(1900,12),(1907,5),(1911,6)]:
 key='1900-01_Cisleithanian_legislative_election' if year==1900 else f'{year}_Cisleithanian_legislative_election'
 item=DATA.get(key);url=LINKS[key] if item else PARLIAMENT if year in (1848,1861) else IMPERIAL_HISTORY
 date=f'{year}-{month or 1:02}-01';precision='month' if month else 'year';end=''
 if year==1885:date='1885-06-01';end='1885-06-05';precision='day'
 if year==1900:date='1900-12-12';end='1901-01-18';precision='day'
 if year==1907:date='1907-05-14';end='1907-05-23';precision='day'
 e=base(date,'reichstag' if year==1848 else 'imperial',url,precision,end)
 if item and item['tables'] and any('Seats'==c['text'] for row in item['tables'][0]['rows'] for c in row):valid=parliamentary(e,item['tables'][0],year)
 else:
  valid=None;e.pop('electionMethod',None)
  e['summary']='Documented historical assembly election; a verified comprehensive seat allocation is not yet entered.'
  e['notes']+='This assembly covered Austrian imperial crown lands beyond modern Austrian borders. Restricted franchise, curiae and/or selection by provincial diets applied. Unverified votes, party shares and chamber allocation remain null. Month/year dates use the first day only as an internal sorting anchor. The appointed/hereditary upper house is not recorded as a nationwide general election. '
  if year in (1861,1867,1870,1871):e['electionMethod']='indirect';e['round']='Provincial-diet delegate selection'
  if year==1891:e['notes']+='The available source provides curial vote figures without seat allocations. Those figures are not treated as a comparable national popular-vote denominator.'
 if year==1885:
  e.update(totalSeats=353,resultStatus='final',voteBasis='Partial reported parliamentary-club allocations; not a complete party result table')
  for name,seats in [('Czech Club',65),('Polish Club',56),('Conservative German forces',53)]:result(e,name,seats=seats)
  e['notes']+='Only the three documented club allocations are entered (174 of 353 mandates); the remainder is unassigned. Clubs are not assumed to be single political parties.'
 if year==1871:e['notes']+='This selection cycle extended into 1872. No exact start/end polling day is asserted. '
 if year==1911:e['notes']+='Voting took place in June and July 1911; June is the start month and no exact nationwide day range is asserted. '
 records.append(e);e['_valid']=valid

# Replace secondary parliamentary reporting with final Ministry returns.
for p in json.loads((OUT/'parliament-primary.json').read_text()):
 year=p['year'];e=next(e for e in records if e['type']=='parliamentary' and e['startDate'].startswith(str(year)))
 if year in (1970,1995) and 'wiederholungswahl' not in p['key']:continue
 old=e['results'];e['results']=[];valid=p['validVotes']
 for row in p['rows']:
  matched=next((r for r in old if r['votes']==row['votes'] and (row['seats'] is None or r['seats']==row['seats'])),None)
  name=matched['name'] if matched else {"ÖVP":"Austrian People's Party","SPÖ":"Socialist Party of Austria" if year<1991 else "Social Democratic Party of Austria","FPÖ":"Freedom Party of Austria","GRÜNE":"The Greens","NEOS":"NEOS","KPÖ":"Communist Party of Austria"}.get(row['short'],row['name'])
  if row['seats'] is None and matched is None:
   # The secondary final allocation assigns all 183 mandates to named
   # winning lists. The Ministry individually names additional zero-seat lists.
   assert sum(r['seats'] or 0 for r in old)==e['totalSeats'],(year,row)
   assert all(any(x['votes']==r['votes'] for x in p['rows']) for r in old if r['seats']),year
  result(e,name,row['votes'],round(row['votes']/valid*100,6),row['seats'] if row['seats'] is not None else matched['seats'] if matched else 0)
 e.update(totalSeats=p['seats'] if p['seats'] is not None else e['totalSeats'],resultStatus='final',resultCoverage='complete',voteBasis=f'Final Ministry party/list votes / {valid:,} valid ballots',_valid=valid)
 e['sources'].insert(0,dict(label='Interior Ministry: final party returns',url=p['source']))
 e['notes']+='Vote counts use the final Interior Ministry returns. Mandates use the Ministry table where supplied, otherwise the referenced final allocation. National seat totals describe this historical election rather than today’s capacity. '
 if year==2024:e['turnout']=round(4929745/6346059*100,6)

# Primary Ministry tables supply candidate counts for every popular round.
# Secondary tables supply election-era party/support labels and turnout only.
primary=json.loads((OUT/'primary-reconciliation.json').read_text())
PRES={1951:['05-06','05-27'],1957:['05-05'],1963:['04-28'],1965:['05-23'],1971:['04-25'],1974:['06-23'],1980:['05-18'],1986:['05-04','06-08'],1992:['04-26','05-24'],1998:['04-19'],2004:['04-25'],2010:['04-25'],2016:['04-24','05-22','12-04'],2022:['10-09']}
for year,dates in PRES.items():
 key=f'{year}_Austrian_presidential_election';t=DATA[key]['tables'][0];hi,h=header(t);vis=[i for i,x in enumerate(h) if x=='Votes'];ci=max(i for i,x in enumerate(h) if x=='Candidate');pi=h.index('Party')
 for ri,md in enumerate(dates):
  e=base(f'{year}-{md}','president',BMI_PRES);e['sources'].append(dict(label='Candidate affiliation/support and round metadata',url=LINKS[key]))
  p=next(p for p in primary if p['id']==e['id']);valid=p['validVotes'];vi=vis[ri];m=meta(t,vi)
  for row in t['rows'][hi+1:]:
   tx=[c['text'] for c in row]
   if len(tx)<=vi:continue
   if tx[ci]=='Total':break
   if integer(tx[vi]) is None:continue
   name=clean(tx[ci]);pn=next(n for n in p['candidates'] if n.casefold().endswith(name.casefold()) or name.split()[-1].casefold()==n.split()[-1].casefold())
   party=tx[pi]
   if party.startswith('Independent') or name in ('Rudolf Kirchschläger','Kurt Waldheim','Wolfgang Denk','Burghard Breitner'):party='Independent'
   r=result(e,name,p['candidates'][pn],round(p['candidates'][pn]/valid*100,6),party=party)
  assert sum(r['votes'] for r in e['results'])==valid,e['id']
  e.update(resultStatus='final',resultCoverage='complete',turnout=m.get('Registered voters/turnout',{}).get('share'),voteBasis=f'Candidate votes / {valid:,} valid ballots in this round',round='First round' if len(dates)>1 and ri==0 else 'Runoff' if ri else 'General')
  e['notes']='Candidate vote counts are checked against the Interior Ministry’s historical result tables. Every round has its own denominator; independent candidacies remain independent even when endorsed by a party. Other affiliation labels are election-era labels. No ideological assessment is inferred. '
  if year==2022:e['turnout']=round(4148082/6363336*100,6)
  ranked=sorted(e['results'],key=lambda r:r['votes'],reverse=True)
  if year==2016 and ri==1:
   e.update(status='cancelled',title='Federal President of Austria — annulled runoff',round='Annulled runoff',summary='Historical annulled returns; no valid winner is assigned.')
   e['notes']+='The Constitutional Court annulled the 22 May runoff on 1 July 2016. The April first round remained valid. These ballot counts are retained as annulled historical returns, with no elected or advanced candidate. '
   e['sources'].insert(0,dict(label='Constitutional Court: annulment of the 2016 runoff',url='https://www.vfgh.gv.at/timeline/2016__Bundespraesidentenstichwahl.en.html'))
  elif ri==0 and len(dates)>1:
   for r in ranked[:2]:r['advanced']=True
   e['summary']='The leading two candidates advanced to the separately recorded runoff.'
  else:
   ranked[0]['winner']=True;e['summary']=ranked[0]['name']+' was elected Federal President.'
   if year==2016:e['round']='Repeat runoff';e['title']='Federal President of Austria — repeat runoff'
  records.append(e);e['_valid']=valid

e=base('2016-10-02','president','https://www.parlament.gv.at/aktuelles/pk/jahr_2016/pk0985');e.update(status='postponed',title='Federal President of Austria — postponed repeat runoff',round='Postponed repeat runoff',summary='The repeat runoff planned for 2 October was postponed to 4 December.',notes='The 2 October repeat runoff did not take place because of defective postal-ballot envelopes. The December result is recorded separately; no October ballots or winner are invented.');records.append(e);e['_valid']=None

# Assembly selections are not popular votes. Counts stay null until verified.
for date,precision,name,party in [('1920-12-09','day','Michael Hainisch','Independent'),('1924-12-09','day','Michael Hainisch','Independent'),('1928-12-01','month','Wilhelm Miklas','Christian Social Party'),('1931-10-01','month','Wilhelm Miklas','Christian Social Party'),('1945-12-20','day','Karl Renner','Socialist Party of Austria')]:
 url=BMI_PRES if date[:4]!='1931' else 'https://publikacio.ppke.hu/id/eprint/1179/1/Das_Staatsoberhaupt_in_der_Zwischenkriegszeit.pdf'
 e=base(date,'president',url,precision);e.update(electionMethod='indirect',round='Federal Assembly selection',resultStatus='final',voteBasis='Federal Assembly selection; exact ballot counts not entered',summary=name+' was selected by the Federal Assembly.',notes='This was an indirect selection by the Federal Assembly, not a nationwide popular presidential election. The selected president is known, but individual ballot rounds, vote counts, turnout and shares remain null pending verification. Month precision is intentional where the polling date is not independently verified; the first day is only a sorting anchor. Michael Hainisch was independent; endorsements are not party membership. Karl Seitz’s earlier role as acting head of state is not reclassified as an election to this constitutional office.')
 result(e,name,party=party)['winner']=True;records.append(e);e['_valid']=None

for e in records:
 peers=[x['id'] for x in records if x['id']!=e['id'] and x['seriesId']==e['seriesId'] and x['startDate'][:4]==e['startDate'][:4]]
 if peers:e['linkedElectionIds']=peers
 reconcile(e,e.pop('_valid'))
 assert sum(r['share'] or 0 for r in e['results'])<=100.2,e['id']
 if e['totalSeats'] is not None:assert sum(r['seats'] or 0 for r in e['results'])<=e['totalSeats'],e['id']
records.sort(key=lambda e:(e['startDate'],e['body']))
used={r['partyId'] for e in records for r in e['results'] if 'partyId' in r}
profiles={k:p for k,p in profiles.items() if p['id'] in used}
for name,obj in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('Built',len(records),'records;',len(profiles),'profiles. Missing tables:',[e['id'] for e in records if e['status']=='held' and not e['results']]);print('Partial tables:',[e['id'] for e in records if e['results'] and e['resultCoverage']=='partial'])
