"""Build source-linked historical midterm templates; never writes to Supabase.

House: official initial party divisions, not every district.
Senate/governors: separate state contests, no combined national vote percentage.
Missing counts remain null. Attribution is an editorial interpretation of sources.
"""
from pathlib import Path
import re,json,csv,hashlib,collections,urllib.parse,gzip
from us_midterm_html import read
from us_presidential_html import expand,read as simple_read

ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/us-midterms'
STATES=json.loads((ROOT/'lib/us-states-map.json').read_text())
BY_NAME={s['name']:s for s in STATES};BY_CODE={s['code']:s for s in STATES}
HOUSE='https://history.house.gov/Institution/Party-Divisions/Party-Divisions/'
SENATE='https://www.senate.gov/history/partydiv.htm'
PLATFORMS='https://www.presidency.ucsb.edu/documents/app-categories/elections-and-transitions/party-platforms'
MIT='https://doi.org/10.7910/DVN/PEJ5QU'
GOV538='https://github.com/fivethirtyeight/election-results/blob/main/election_results_gubernatorial.csv'
HIST='https://doi.org/10.7910/DVN/DGUMFI'
YEARS=list(range(1790,2023,4));warnings=[]

def source(label,url):return {'label':label,'url':url}
def clean(s):return re.sub(r'\s+',' ',s).strip()
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:70]
def number(s):
 s=s.strip().replace(',','').replace('%','').replace('\u200b','')
 return float(s)if re.fullmatch(r'\d+(?:\.\d+)?',s)else None
def name(s):return clean(re.sub(r'\([^)]*(?:incumbent|withdrawn)[^)]*\)','',s,flags=re.I))
def normal(s):return re.sub(r'[^a-z]','',s.lower()).replace('incumbent','')
def party(s):
 s=clean(s);lookup={'D':'Democratic','R':'Republican','DEM':'Democratic','REP':'Republican','LIB':'Libertarian','GRE':'Green','CON':'Constitution','IND':'Independent','Pro-Admin.':'Pro-Administration','Anti-Admin.':'Anti-Administration','Democrats':'Democratic','Republicans':'Republican','Federalists':'Federalist','Democratic Republicans':'Democratic-Republican','Democratic Republican':'Democratic-Republican','Whigs':'Whig','Anti-Masonics':'Anti-Masonic'}
 return lookup.get(s,s)
def color(p):
 p=p.lower()
 for term,c in [('democratic-republican','#397b46'),('anti-administration','#397b46'),('pro-administration','#c79b39'),('federalist','#c79b39'),('democratic','#005ac2'),('republican','#e60000'),('whig','#cc9a27'),('progressive','#26805b'),('socialist','#b52b43'),('green','#32843f'),('libertarian','#bd9400'),('free soil','#76512b'),('populist','#805aaa'),('farmer','#805aaa'),('jackson','#005ac2')]:
  if term in p:return c
 return '#7b6c9b'

# Party platforms are first-party documents preserved by UCSB. For early factions,
# the public historical overview is the source; no contemporary D/R back-projection.
platforms=[]
html=(CACHE/'platforms.html').read_text()
for href,title in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',html,re.S):
 title=clean(re.sub('<[^>]+>','',title));m=re.search(r'(18\d\d|19\d\d|20\d\d)',title)
 if m and 'Platform' in title:platforms.append((int(m[0]),title,'https://www.presidency.ucsb.edu'+href if href.startswith('/')else href))

def party_ideology(p,y):
 p=party(p);q=p.lower();ids=[];era='';term=None
 if 'democratic-republican'in q or 'anti-administration'in q or 'jacksonian'in q or q=='jackson republicans':ids=['agrarianism','republicanism'];era='Early agrarian republican tradition'
 elif 'federalist'in q or 'pro-administration'in q:ids=['classical-conservatism','republicanism'];era='Early Federalist / pro-administration tradition'
 elif q in ('democratic','democrat') or q.startswith('democratic/'):
  term='Democratic'
  if y<1896:ids=['classical-liberalism','social-conservatism'];era='Nineteenth-century limited-government Democratic tradition; broad and internally divided'
  elif y<1934:ids=['economic-progressivism','agrarianism'];era='Progressive-era and agrarian Democratic platform tradition'
  elif y<1966:ids=['social-liberalism','economic-progressivism'];era='New Deal Democratic platform tradition; conservative regional factions also existed'
  else:ids=['social-liberalism','social-progressivism'];era='Post-civil-rights Democratic platform tradition'
 elif q in ('republican','republicans') or q.startswith('republican/'):
  term='Republican'
  if y<1878:ids=['republicanism','social-progressivism'];era='Early anti-slavery / Reconstruction Republican tradition; not the modern conservative coalition'
  elif y<1934:ids=['economic-liberalism','nationalism'];era='Industrial-era Republican platform tradition; progressive insurgents assessed separately where sourced'
  elif y<1982:ids=['economic-liberalism','liberal-conservatism'];era='Mid-century Republican platform tradition, before the later conservative coalition'
  elif y<2018:ids=['economic-liberalism','social-conservatism'];era='Reagan-era and subsequent conservative Republican platform tradition'
  else:ids=['economic-liberalism','national-conservatism'];era='Contemporary national-conservative Republican platform tradition'
 elif 'whig'in q or q in ('anti-jacksonians','anti-jacksonian','adams','adams-clay republicans'):ids=['economic-progressivism','classical-conservatism'];era='National-development and institutional-conservative Whig / National Republican tradition';term='Whig'
 elif 'progressive'in q:ids=['progressivism','economic-progressivism'];era='Progressive party reform tradition';term='Progressive'
 elif 'populist'in q or q in ('people\'s','peoples') or 'farmer-labor'in q:ids=['agrarianism','left-wing-populism'];era='Agrarian / farmer-labor reform tradition'
 elif 'libertarian'in q:ids=['libertarianism','economic-liberalism'];era='Libertarian Party tradition';term='Libertarian'
 elif q=='green' or q=='green-rainbow':ids=['green-politics','social-progressivism'];era='Green party tradition'
 elif q=='socialist' or 'socialist party'in q or q=='socialist labor':ids=['democratic-socialism'];era='American socialist party tradition'
 elif 'free soil'in q:ids=['social-progressivism','republicanism'];era='Anti-extension-of-slavery Free Soil tradition';term='Free Soil'
 elif q in ('american','know nothing','know-nothing'):ids=['nationalism','social-conservatism'];era='Nativist American / Know-Nothing party tradition';term='American'
 elif 'constitution'in q or 'american independent'in q:ids=['national-conservatism','social-conservatism'];era='Constitution / American Independent conservative party tradition';term='American Independent'if'american independent'in q else None
 elif 'nullifier'in q:ids=['regionalism','social-conservatism'];era='Nullification and states-rights tradition'
 elif 'anti-masonic'in q:ids=['right-wing-populism'];era='Anti-Masonic populist tradition'
 refs=[]
 if ids:
  available=[x for x in platforms if x[0]<=y and term and term in x[1]]
  refs=[source(available[0][1],available[0][2])]if available else [source('Historical party divisions and factions',HOUSE)]
 return ['ideology-'+i for i in ids],{'kind':'party-era'if ids else 'unassessed','year':y,'note':era+'. Editorial mapping to our ideology guides; a broad election-era fallback, not a claim that every candidate or faction agreed.'if ids else 'No sufficiently supported candidate or election-era party assessment is entered. Independent and miscellaneous labels alone do not establish an ideology.','sources':refs}

PROGRESSIVES='https://www.senate.gov/artandhistory/senate-stories/progressive-era.htm'
OVERRIDES=[
 (r'George (?:C\.? |Corley )?Wallace',1962,1974,['social-conservatism','white-supremacism'],source('Stanford King Institute: George Wallace','https://kinginstitute.stanford.edu/wallace-george-corley-jr')),
 (r'Jesse Ventura',1998,2002,['libertarianism','economic-liberalism','social-liberalism'],source('Minnesota Historical Society: Ventura governorship','https://www.mnhs.org/mnopedia/search/index/event/governorship-jesse-ventura')),

 (r'Robert (?:M\.? )?La Follette(?: Sr\.?)?$',1898,1926,['progressivism','economic-progressivism'],source('NGA: Robert M. La Follette','https://www.nga.org/governor/robert-m-la-follette/')),
 (r'(?:William E\.?|William) Borah',1906,1940,['progressivism','economic-progressivism'],source('Senate: Progressive Era',PROGRESSIVES)),
 (r'George (?:W\.? )?Norris',1910,1942,['progressivism','economic-progressivism'],source('Senate: Progressive Era',PROGRESSIVES)),
 (r'Hiram (?:W\.? )?Johnson',1910,1946,['progressivism','economic-progressivism'],source('Senate: Progressive Era',PROGRESSIVES)),
 (r'Robert (?:L\.? )?Owen',1906,1926,['progressivism','economic-progressivism'],source('Senate: Progressive Era',PROGRESSIVES)),
 (r'Thomas (?:J\.? )?Walsh',1910,1934,['progressivism','economic-progressivism'],source('Senate: Progressive Era',PROGRESSIVES)),
 (r'(?:Bernie|Bernard) Sanders',2015,2022,['democratic-socialism','progressivism'],source('Sanders on democratic socialism','https://www.presidency.ucsb.edu/documents/remarks-georgetown-university-washington-dc')),
]
def result(n,p,y,ident,v=None,share=None,winner=False,candidate=True):
 p=party(p);ids,basis=party_ideology(p,y)
 if candidate:
  for pattern,start,end,ideologies,ref in OVERRIDES:
   if start<=y<=end and re.fullmatch(pattern,name(n),re.I):
    ids=['ideology-'+i for i in ideologies];basis={'kind':'candidate','year':y,'note':'Candidate-specific editorial classification based on the cited political record; it overrides the party fallback.','sources':[ref]};break
 return {'id':ident,'name':name(n)or'Other / write-in','party':p,'color':color(p),'votes':int(v)if v is not None else None,'share':share,'seats':None,'electoralVotes':None,'winner':winner,'ideologyIds':ids,'ideologyBasis':basis}

def template(y,office):
 titles={'house':'House of Representatives','senate':'Senate','governor':'Gubernatorial elections'}
 return {'id':f'world-us-{office}-{y}','countryId':'us','title':titles[office],'type':'gubernatorial'if office=='governor'else'parliamentary','body':titles[office],'startDate':f'{y}-01-01','endDate':'','precision':'year','dateStatus':'expected','status':'held','publication':'published','round':'Midterm cycle'+(' · '+str(y)+'–'+str(y+1)if office=='senate'and y<1914 else''),'seriesId':f'us-{office}-midterms','snap':False,'summary':'','government':'','turnout':None,'totalSeats':None,'resultStatus':'final','resultCoverage':'partial','voteBasis':'','results':[],'sources':[],'checked':'2026-10-05','notes':'','articleId':'','version':0}

def make_contest(y,office,state,title,results,ref,notes='',special=False,round='General',method=None,index=0):
 if method is None:method='indirect'if office=='senate'and y<1914 else'direct'
 rid=f'race-{office}-{y}-{state["code"].lower()}-{slug(title)}-{index}'
 for i,r in enumerate(results):r['id']=rid+'-'+str(i)
 return {'id':rid,'stateCode':state['code'],'stateName':state['name'],'title':title,'round':round,'special':special,'method':method,'voteBasis':'Legislative selection; popular-vote totals are not inferred'if method=='indirect'else'Popular votes in this state contest','notes':notes,'results':results,'sources':[ref]}

def candidate_list(text,y,indirect=False):
 out=[]
 for m in re.finditer(r'(?:▌\s*)?(Y\s+)?([^▌\n]+?)\s+\(([^()\n]+)\)\s*([^▌\n]*)',text):
  n=name(m[2].strip(' ,'));p=m[3];tail=m[4];share_match=re.search(r'(\d+(?:\.\d+)?)\s*%',tail);vote_match=re.search(r'(\d[\d,]*)\s*(?:votes|\()',tail)
  if n in ('Others','Other')or 'ballot'in n.lower()or re.search(r'\d',p):continue
  share=float(share_match[1])if share_match and not indirect else None;votes=int(vote_match[1].replace(',',''))if vote_match and not indirect else None
  if share is not None and share>100:share=None
  out.append(result(n,p,y,'pending',votes,share,bool(m[1])))
 return out

def detailed(t,y):
 rows=t['rows'];header=[clean(c['text'])for c in rows[0]]if rows else[]
 if not all(x in header for x in ['Party','Candidate','Votes']):return None
 ci=header.index('Candidate');pi=header.index('Party');vi=header.index('Votes');si=header.index('%')if'%'in header else None
 out=[]
 for row in rows[1:]:
  if len(row)<len(header):continue
  off=1 if row and row[0]['text']==''and len(row)>len(header)else 0
  if ci+off>=len(row)or vi+off>=len(row):continue
  n=row[ci+off]['text'];p=row[pi+off]['text'];v=number(row[vi+off]['text']);sh=number(row[si+off]['text'])if si is not None and si+off<len(row)else None
  if v is None or any(w in n.lower()for w in ['turnout','total votes','registered'])or not n.strip():continue
  if not p.strip()and 'write'in n.lower():p='Write-in'
  out.append(result(n,p,y,'pending',v,sh))
 if not out:return None
 merged=collections.defaultdict(list)
 for r in out:merged[normal(r['name'])].append(r)
 combined=[]
 for lines in merged.values():
  ordinary=[r for r in lines if r['party'].lower()!='total'];primary=max(ordinary or lines,key=lambda r:r['votes']or 0);totals=[r for r in lines if r['party'].lower()=='total'];r=primary.copy()
  if totals:r['votes']=totals[-1]['votes'];r['share']=totals[-1]['share']
  else:r['votes']=sum(r['votes']or 0 for r in lines);r['share']=sum(r['share']or 0 for r in lines)if any(r['share']is not None for r in lines)else None
  combined.append(r)
 out=combined
 if sum(r['share']or 0 for r in out)>100.2:return None
 return out

def state_of(text):
 for n in sorted(BY_NAME,key=len,reverse=True):
  if text==n or text.startswith(n+' ')or text.startswith(n+'\n')or text.startswith(n+'('):return BY_NAME[n]
 return None

records=[]
# Official House initial divisions include nonvoting delegates separately. They
# must not be included in the chamber or translated into national vote shares.
headers=[]
for row in simple_read(CACHE/'house.html')[0]:
 cells=[c['text']for c in row]
 if cells[0].startswith('Congress'):headers=cells;continue
 m=re.match(r'(\d+)(?:st|nd|rd|th) \((\d{4})[-–]',cells[0])
 if not m:continue
 y=int(m[2])-1
 if y not in YEARS:continue
 e=template(y,'house');e['totalSeats']=int(cells[1]);e['resultCoverage']='complete';e['sources']=[source('U.S. House: initial party divisions',HOUSE)];e['voteBasis']='Initial voting-member seats following the election cycle; not popular-vote percentages'
 parties=[(headers[i],int(cells[i]))for i in [2,3]if cells[i].isdigit()and int(cells[i])]
 if cells[4]!='0':
  parties.extend((n.strip(' ,'),int(v))for n,v in re.findall(r'([^()]+)\((\d+)\)',cells[4]))
 for i,(p,seats)in enumerate(parties):
  r=result(p,p,y,f'house-{y}-{i}',candidate=False);r['seats']=seats;e['results'].append(r)
 if sum(r['seats']for r in e['results'])!=e['totalSeats']:
  remaining=e['totalSeats']-sum(r['seats']for r in e['results']);r=result('Unallocated in initial source divisions','',y,f'house-{y}-unallocated',candidate=False);r['seats']=remaining;r['color']='#cbd5e1';e['results'].append(r)
 e['summary']='Party-level House results for this midterm cycle, using the House historian’s initial election divisions.'
 e['notes']='District contests are intentionally not reproduced. Nonvoting delegates and resident commissioners are excluded. Figures describe initial election results for the following Congress, not later special elections or party switches. Some state elections occurred in the following year. Ideologies reflect broad party traditions at this election, not their present-day positions.'
 records.append(e)

for y in YEARS:
 e=template(y,'senate');p=CACHE/f'wiki-senate-{y}.html'
 if not p.exists():raise ValueError(f'Missing Senate source {y}')
 url='https://en.wikipedia.org/wiki/'+urllib.parse.quote(f'{y}–{str(y+1)[-2:]}_United_States_Senate_elections'if y<1914 else f'{y}_United_States_Senate_elections');ref=source('Historical Senate race summary and linked records',url);tables=read(p);contests=[];regular_seen=False
 for t in tables:
  rows=expand(t['rows']);head=' '.join(c['text']for r in rows[:2]for c in r)
  if 'State'not in head or not ('Candidates'in head or 'Major candidates'in head):continue
  heading=t['heading'].lower();regular='leading to'in heading or ('races'in heading and ('next'in heading or 'general'in heading))or('regular'in heading and 'special'not in heading)
  if y>=1914 and t['heading']in ('Races leading to the 118th Congress','Races leading to the 117th Congress'):regular=True
  # The first "leading to" table is the midterm's regular class. Later early
  # selections for another future Congress are not part of this class.
  if 'leading to'in heading:
   if regular_seen:continue
   regular_seen=True
  if 'special elections'in heading:regular=False
  for row in rows[2:]:
   if not row:continue
   state=state_of(row[0]['text'])
   if not state:continue
   text=row[-1]['text'];results=candidate_list(text,y,y<1914)
   if y==1862 and state['code']=='WV'and sum(r['winner']for r in results)>1:
    chosen='Waitman T. Willey'if not any(c['stateCode']=='WV'and not c['special']for c in contests)else'Peter G. Van Winkle'
    unique={}
    for r in results:
     r['winner']=r['name']==chosen;unique.setdefault(normal(r['name']),r)
    results=list(unique.values())
   if y==1818 and state['code']in ('IL','MD'):
    cls='3'if 'Class 3'in row[0]['text']else'2'if 'Class 2'in row[0]['text']else'1'
    chosen=({'3':'Ninian Edwards','2':'Jesse B. Thomas'}if state['code']=='IL'else{'3':'Edward Lloyd','1':'William Pinkney'}).get(cls)
    unique={}
    for r in results:
     r['winner']=r['name']==chosen;unique.setdefault(normal(r['name']),r)
    results=list(unique.values())
   if not results and not any(word in text.lower()for word in ['missing','vacant','unknown']):continue
   note=clean(row[-2]['text'])+'\nSource candidate / selection detail: '+text
   title=clean(row[0]['text']).replace(state['name'],'Senate',1)
   if y==1862 and state['code']=='WV'and regular:title='Senate (Class 1)'if not any(c['stateCode']=='WV'and not c['special']for c in contests)else'Senate (Class 2)'
   if title=='Senate'and not regular:title+=' · special'
   if y==1906 and state['code']=='AL'and len(results)>1:
    for i,r in enumerate(results):
     contests.append(make_contest(y,'senate',state,title+(' · successor selection'if i else''),[r],ref,note,not regular or i>0,method='indirect',index=len(contests)))
   else:
    c=make_contest(y,'senate',state,title,results,ref,note,not regular,method='indirect'if y<1914 else'direct',index=len(contests));contests.append(c)
 # Match general result tables to summary candidates; primary tables are never
 # used just because they happen to contain larger vote totals.
 if y>=1914:
  first_rounds=[]
  for c in contests:
   winner=next((r for r in c['results']if r['winner']),None)
   options=[]
   for t in tables:
    if state_of(t['state'])!=BY_CODE[c['stateCode']]:continue
    caption=t['caption'].split('\n')[0].lower();candidate=detailed(t,y)
    if candidate and 'primary'not in caption and winner and any(normal(r['name'])==normal(winner['name'])for r in candidate):
     # A final general table includes an opposing candidate from the summary.
     opposition={normal(r['name'])for r in c['results']if not r['winner']}
     if opposition and not any(normal(r['name'])in opposition for r in candidate):continue
     options.append(candidate)
   if options:
    detail=options[-1]
    for r in detail:r['winner']=normal(r['name'])==normal(winner['name'])
    for i,r in enumerate(detail):r['id']=c['id']+'-'+str(i)
    c['results']=detail
    if len(options)>1 and len(detail)==2:
     previous=options[-2];finalists={normal(r['name'])for r in detail};first_winner=next((r for r in previous if normal(r['name'])==normal(winner['name'])),None)
     if len(previous)>2 and first_winner and first_winner['share']is not None and first_winner['share']<50 and finalists.issubset({normal(r['name'])for r in previous}):
      c['round']='Runoff';first={**c,'id':c['id']+'-first','round':'First round','diagramExcluded':True,'notes':'First round of this seat election. The elected candidate is recorded in the separate runoff race. Excluded from the Senate diagram to avoid counting the same seat twice.','results':previous}
      for i,r in enumerate(previous):r['id']=first['id']+'-'+str(i);r['winner']=False;r['advanced']=normal(r['name'])in finalists
      first_rounds.append(first)
  contests+=first_rounds
 e['contests']=contests;e['sources']=[source('U.S. Senate historical party divisions',SENATE),ref,source('MIT Election Lab: Senate returns',MIT)];regular=[c for c in contests if not c['special']and not c.get('diagramExcluded',False)];e['totalSeats']=len(regular)
 e['results']=[{**r,'name':r['name']+' · '+c['stateName'],'votes':None,'share':None,'seats':1}for c in regular for r in c['results']if r['winner']]
 e['summary']='State Senate races in this midterm cycle, with separate candidate results and election-era ideology attribution.'
 e['voteBasis']='Elected candidates in regular races; continuing senators are not included'
 e['notes']='The seat diagram shows only regular seats contested in this cycle, not the full Senate. Special races remain available in the state selector. Early cycles span two years and use legislative selection; missing or non-comparable vote totals are left blank. Candidate ideology is used where sourced; otherwise the broad election-era party tradition is used. Unassessed candidates are not assigned an ideology.'
 if not regular:warnings.append(f'Senate {y}: no regular contests identified')
 records.append(e)

# Governor national summaries are supplemented by individual state pages.
def indirect_governor(code,y):return (code=='NJ'and y<1845)or(code=='MD'and y<1838)or(code=='VA'and y<1851)or(code=='SC'and y<1866)or(code=='GA'and y<1825)or(code=='NC'and y<1837)
for y in YEARS:
 e=template(y,'governor');contests=[];p=CACHE/f'wiki-governor-{y}.html';url=f'https://en.wikipedia.org/wiki/{y}_United_States_gubernatorial_elections';ref=source('Historical gubernatorial summary and linked records',url)
 if p.exists():
  for t in read(p):
   rows=expand(t['rows']);head=[clean(c['text'])for c in rows[0]]if rows else[]
   if not any(h in ('State','States')for h in head) or not any('candidates'in h.lower()for h in head):continue
   for row in rows[1:]:
    state=state_of(row[0]['text'])if row else None
    if not state:continue
    method='indirect'if indirect_governor(state['code'],y)else'direct';text=row[-1]['text'];results=candidate_list(text,y,method=='indirect');notes=''
    if 'Opposing candidates'in head:
     status_index=head.index('Status');status=row[status_index]['text'];inc=head.index('Incumbent');part=head.index('Party')
     if re.search(r're.elected',status,re.I):
      share_match=re.search(r'(\d+(?:\.\d+)?)\s*%',status);v_match=re.search(r'(\d[\d,]*)\s*\(',status)
      winner=result(row[inc]['text'],row[part]['text'],y,'pending',int(v_match[1].replace(',',''))if v_match and method=='direct'else None,float(share_match[1])if share_match and method=='direct'else None,True);results=[winner]+results
     elif results:results[0]['winner']=True
     notes=clean(status)
    elif results and not any(r['winner']for r in results):results[0]['winner']=True
    if not results:continue
    # Some summaries combine primary ballots and the general election.
    # Preserve the election outcome, while leaving incomparable counts blank.
    winners=[r for r in results if r['winner']]
    if len(winners)>1:
     chosen='Lester Maddox'if y==1966 and state['code']=='GA'else winners[0]['name']
     unique={}
     for r in results:
      r['winner']=r['name']==chosen;r['votes']=None;r['share']=None;unique.setdefault(normal(r['name']),r)
     results=list(unique.values());notes+=' Source groups multiple ballots or rounds; counts are left blank and the final selected governor is marked.'
    if sum(r['share']or 0 for r in results)>100.2:
     for r in results:r['share']=None
     notes+=' Multiple rounds or non-comparable percentages are described in the source; percentages are not combined.'
    c=make_contest(y,'governor',state,'Governor',results,ref,notes,special='special'in row[0]['text'].lower(),method=method,index=len(contests));contests.append(c)
 for state in STATES:
  p=CACHE/f'governor-{y}-{state["code"]}.html'
  if not p.exists():continue
  html=p.read_text();title=re.search(r'<title>(.*?)</title>',html,re.S)
  if not title or str(y)not in title[1]or'gubernatorial election'not in title[1].lower():continue
  ts=read(p);options=[]
  for t in ts:
   detail=detailed(t,y)
   if detail and not any(w in (t['heading']+' '+t['caption'].split('\n')[0]).lower()for w in ['primary','nomination']):options.append(detail)
  if not options:continue
  detail=options[-1];method='indirect'if indirect_governor(state['code'],y)else'direct'
  elected=None
  for t in ts[:5]:
   for row in t['rows']:
    for cell in row:
     m=re.search(r'Elected Governor\s*\n+([^\n]+)',cell['text'],re.I)
     if m:elected=clean(m[1]);break
  if elected:
   for r in detail:r['winner']=normal(r['name'])==normal(elected)
  if not any(r['winner']for r in detail):max(detail,key=lambda r:r['votes']or 0)['winner']=True
  if method=='indirect':
   for r in detail:r['votes']=None;r['share']=None
  url='https://en.wikipedia.org/wiki/'+urllib.parse.quote(f'{y}_{state["name"].replace(" ","_")}_gubernatorial_election');c=make_contest(y,'governor',state,'Governor',detail,source('Historical state result and cited records',url),'Legislative selection counts are not inferred from placeholders.'if method=='indirect'else'',method=method,index=len(contests));contests=[x for x in contests if x['stateCode']!=state['code']]+[c]
 e['contests']=sorted(contests,key=lambda c:c['stateName']);e['sources']=list({s['url']:s for c in contests for s in c['sources']}.values())[:25]if not (CACHE/f'wiki-governor-{y}.html').exists()else[ref]
 if not contests:warnings.append(f'Governor {y}: no contests found');continue
 e['summary']='State gubernatorial races held in this midterm year. Each governor is elected separately; there is no combined national percentage.'
 e['voteBasis']='Separate state governor races';e['notes']='This entry covers governor elections held in the midterm year, including available special contests, not off-year elections or every sitting governor. Candidate-specific ideology is used where sourced; election-era party ideology is the fallback. Historical indirect selections and unavailable counts are identified separately. Source summaries may omit minor candidates; blank values do not mean zero votes.'
 records.append(e)

# Modern governors: first-party published dataset with a source URL per result.
# Runoffs remain distinct; ranked-choice rounds are never summed together.
govrows=list(csv.DictReader((CACHE/'governors-538.csv').open()));groups=collections.defaultdict(list)
for r in govrows:
 if int(r['cycle'])in YEARS and r['state_abbrev']in BY_CODE and r['stage']in ('general','runoff')and not re.search(r'blank|void|overvote|undervote',r['alt_result_text'],re.I):groups[(int(r['cycle']),r['race_id'],r['stage'])].append(r)
for (y,rid,stage),rows in groups.items():
 e=next((e for e in records if e['id']==f'world-us-governor-{y}'),None)
 if e is None:
  e=template(y,'governor');e['contests']=[];e['sources']=[source('FiveThirtyEight historical governor returns',GOV538)];e['summary']='State gubernatorial races held in this midterm year.';e['voteBasis']='Separate state governor races';records.append(e)
 state=BY_CODE[rows[0]['state_abbrev']];final=max(int(r['ranked_choice_round']or 0)for r in rows);rows=[r for r in rows if int(r['ranked_choice_round']or 0)==final];results=[]
 merged=collections.defaultdict(list)
 for r in rows:merged[r['candidate_name']or r['alt_result_text']or'Other / write-in'].append(r)
 for n,lines in merged.items():
  primary=max(lines,key=lambda r:number(r['votes'])or 0);votes=sum(number(r['votes'])or 0 for r in lines);share=sum(number(r['percent'])or 0 for r in lines)
  results.append(result(n,primary['ballot_party']or primary['party'],y,'pending',votes,share,any(r['winner']=='true'for r in lines)))
 if sum(r['share']or 0 for r in results)>100.2:warnings.append(f'Governor {y} {state["code"]}: fusion/round shares require review');continue
 rawsources=list({r['source']:source('State official result cited by the dataset',r['source'].replace('http:','https:'))for r in rows if r['source'].startswith(('https:','http:'))}.values())[:4]
 c=make_contest(y,'governor',state,'Governor',results,source('FiveThirtyEight historical returns with official sources',GOV538),'Final ranked-choice round '+str(final)if final else'',special=rows[0]['special']=='true',round='Runoff'if stage=='runoff'else'General',index=len(e['contests']));c['sources']+=rawsources
 if stage=='general':e['contests']=[x for x in e['contests']if x['stateCode']!=state['code']]
 e['contests'].append(c)
 if not any(s['url']==GOV538 for s in e['sources']):e['sources'].append(source('FiveThirtyEight historical returns with official sources',GOV538))

# MIT statewide Senate file contains general and runoff rows, fusion lines, and
# special elections. It is used to fill missing vote counts only after matching
# candidates and checking that the count agrees with the recorded percentage.
mitrows=list(csv.DictReader((CACHE/'senate.tab').open()))
for e in records:
 if e['seriesId']!='us-senate-midterms':continue
 y=int(e['startDate'][:4])
 for c in e['contests']:
  matches=[r for r in mitrows if int(r['year'])==y and r['state_po']==c['stateCode']and r['stage']=='gen'and r['special'].lower()==str(c['special']).lower()and r['mode']=='total']
  for candidate in c['results']:
   found=[r for r in matches if normal(r['candidate'])==normal(candidate['name'])]
   if not found:continue
   total=max(float(r['totalvotes'])for r in found);votes=sum(float(r['candidatevotes'])for r in found if r['candidatevotes']and r['candidatevotes']!='NA');share=100*votes/total if total else None
   if candidate['share']is not None and share is not None and abs(candidate['share']-share)>.25:continue
   candidate['votes']=int(votes)
   candidate['share']=share
  if matches and not any(s['url']==MIT for s in c['sources']):c['sources'].append(source('MIT Election Lab / House Clerk: Senate returns',MIT))
 for c in e['contests']:
  if sum(r['share']or 0 for r in c['results'])>100.2:
   warnings.append(f'Senate {y} {c["stateCode"]}: percentage conflict')
   for r in c['results']:r['share']=None

for e in records:
 if 'contests'in e:e['contests'].sort(key=lambda c:(c['stateName'],c['special'],c['round']))
 if e['seriesId']=='us-senate-midterms':e['results']=[{**r,'name':r['name']+' · '+c['stateName'],'votes':None,'share':None,'seats':1}for c in e['contests']if not c['special']and not c.get('diagramExcluded',False)for r in c['results']if r['winner']]
records.sort(key=lambda e:(e['startDate'],e['seriesId']))
(ROOT/'scripts/us-midterm-election-records.json.gz').write_bytes(gzip.compress((json.dumps(records,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
audit={'sources':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in sorted(CACHE.glob('*.html'))if p.name.startswith(('wiki','governor'))], 'records':len(records),'races':sum(len(e.get('contests',[]))for e in records),'warnings':warnings}
(ROOT/'scripts/us-midterm-sources.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:audit[k]for k in ['records','races','warnings']},indent=2))
