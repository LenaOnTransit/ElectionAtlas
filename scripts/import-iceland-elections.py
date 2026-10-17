"""Build Iceland national elections from archived historical tables and Statistics Iceland."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys
P=Path(__file__).parent/'iceland-election-import';WEB={x['name']:x for x in json.loads((P/'web-extract.json').read_text())};records=[];profiles={};audit=[];primary=[]
INFO={
'Independence Party':('D','#1763a4',['liberal-conservatism'],'Independence_Party_(Iceland)'),
'Progressive Party':('B','#69a947',['agrarianism'],'Progressive_Party_(Iceland)'),
'Social Democratic Alliance':('S','#d53347',['social-democracy'],'Social_Democratic_Alliance'),
'Social Democratic Party':('A','#df253e',['social-democracy'],'Social_Democratic_Party_(Iceland)'),
'Reform':('C','#f28b31',['social-liberalism'],'Reform_Party_(Iceland)'),
'Left-Green Movement':('V','#488d44',['green-politics','democratic-socialism'],'Left-Green_Movement'),
"People's Party":('F','#d6a33a',[],'People%27s_Party_(Iceland,_2016)'),
'Centre Party':('M','#7aadd1',[],'Centre_Party_(Iceland)'),
'Pirate Party':('P','#674b8f',[],'Pirate_Party_(Iceland)'),
}
ALIASES={'The Social Democratic Alliance':'Social Democratic Alliance','The Left-Green Movement':'Left-Green Movement','The People´s Party':"People's Party",'The Central Party':'Centre Party','The Liberal Party':'Liberal Party (1998–2012)','The Civic Movement':"Citizens' Movement",'The Alliance of Social Democrats':'Alliance of Social Democrats (1999 electoral alliance)',"People's Unity Party – Socialist Party":'Socialist Party (1938–1968)'}
def src(label,url):return dict(label=label,url=url)
def profile(n,y):
 key=ALIASES.get(n,n)
 if n in ['Independents','Others and outside parties','Elected non-party representatives'] or n.startswith('Independent ('):return None
 if key=="Citizens' Party" and y<1930:key="Citizens' Party (1923 electoral grouping)"
 if key=='Independence Party' and y<1929:key='Independence Party (historical, 1907–1927)'
 if key=='Liberal Party' and y<1930:key='Liberal Party (1926–1929)'
 short,color,tags,page=INFO.get(key,('',None,[],None));tags=list(tags)
 if key=='Independence Party' and y<1945:tags=[]
 if key=='Social Democratic Party' and y<1945:tags=[]
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/is/'+key)),country_id='is',name=key,short_name=short,color=color,ideology_ids=['ideology-'+t for t in INFO.get(key,('',None,[],None))[2]],notes='Colours are a display palette. '+('Party history: https://en.wikipedia.org/wiki/'+page if page else 'Historical organisation or electoral list; ideology unassessed. Similar names do not establish organisational continuity.'),archived=False)
 return profiles[key],tags,page
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def official_date(label):
 y=int(label[:4]);rest=label[4:];d=f'{y}-01-01';end='';prec='year'
 if any(m in rest for m in MONTHS):
  m=next(m for m in MONTHS if m in rest);nums=re.findall(r'\d+',rest);d=f'{y}-{MONTHS[m]:02}-'+(f'{int(nums[0]):02}' if nums else '01');prec='day' if nums else 'month'
  if len(nums)>1:end=f'{y}-{MONTHS[m]:02}-{int(nums[1]):02}'
 return d,end,prec
TURN=json.loads((P/'statice-KOS02001.json').read_text());AT=json.loads((P/'statice-KOS02002.json').read_text())
def cell(d,**kw):
 i=0
 for k,size in zip(d['id'],d['size']):
  idx=d['dimension'][k]['category']['index'];i=i*size+idx[kw.get(k,next(iter(idx)))]
 return d['value'][i] if isinstance(d['value'],list) else d['value'].get(str(i))
def base(y,body='Alþingi',suffix='',date=None):
 slug='presidential' if body=='Presidency' else 'althingi-upper' if body=='Alþingi upper house' else 'althingi';e=dict(id=f'world-iceland-{slug}-{y}'+('-'+suffix if suffix else ''),countryId='is',title=('Iceland presidential election' if body=='Presidency' else 'Iceland '+body+' election')+(' ('+suffix.replace('-',' ')+')' if suffix else '')+f' {y}',type='presidential' if body=='Presidency' else 'parliamentary',body=body,startDate=f'{y}-01-01',endDate='',precision='year',dateStatus='confirmed',status='held',publication='published',round='',seriesId='IS-president' if body=='Presidency' else 'IS-upper-national' if body=='Alþingi upper house' else 'IS-AL',snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='complete',voteBasis='Valid popular candidate votes' if body=='Presidency' else 'Valid party/list votes',results=[],sources=[],checked='2026-10-17',notes='Blank and rejected ballots are excluded from result shares. Colours are a display palette. Unknown figures remain unreported.',articleId='',version=1,electionMethod='direct')
 if date:e['startDate'],e['endDate'],e['precision']=date
 return e

def row(e,n,party,v,share,seats=None,ev=None,winner=False):
 pr=profile(party,int(e['startDate'][:4])) if party and party!='Independent' else None;r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=n,party=party,color=pr[0]['color'] if pr else '#808080',votes=v,share=share,seats=seats,previousSeats=None,electoralVotes=ev,winner=winner,ideologyIds=['ideology-'+t for t in pr[1]] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=int(e['startDate'][:4]),note='Broad party tradition for this period, not an individual candidate assessment.',sources=[src('Party history and tradition','https://en.wikipedia.org/wiki/'+pr[2])])
 e['results'].append(r);return r

def finish(e,expected_votes=None,expected_seats=None,raw=None):
 ss=sum(r['seats'] or 0 for r in e['results']);vv=sum(r['votes'] or r['electoralVotes'] or 0 for r in e['results'])
 if expected_seats is not None:assert ss==expected_seats,(e['id'],ss,expected_seats)
 if expected_votes is not None and raw is None:assert vv==expected_votes,(e['id'],vv,expected_votes)
 if raw is not None:assert abs(sum(r['value'] or 0 for r in raw)-expected_votes)<.001,(e['id'],raw,expected_votes)
 if not e['results']:e['resultCoverage']='partial';e['resultStatus']='not-entered'
 audit.append(dict(id=e['id'],expectedVotes=expected_votes,recordedVotes=vv,expectedSeats=expected_seats,recordedSeats=ss,reportedAllocations=raw));records.append(e)
# Historical result rows occur in both ordinary Markdown and compact archived tables.
def parse_tables(x):
 p=x['prose'];p=p[p.find('## Results'):];p=p.split('## References')[0];blocks=re.split(r'### By-election',p);out=[]
 for b in blocks:
  if 'Party' not in b or 'Total' not in b:continue
  both='Lower' in b and 'Upper'in b;changes='+/–'in b or '+/−'in b;items=[];total=None
  for l in b.splitlines():
   l=l.strip().strip('|').strip()
   if not l or not re.search(r'\d',l):continue
   if l.startswith('Total') and not l.startswith('Total votes'):
    nums=re.findall(r'[+–−-]?\d[\d,]*(?:\.\d+)?',l);total=[float(n.replace(',','').replace('–','-').replace('−','-')) for n in nums];break
   if l.startswith(('Valid','Invalid','Registered','Source','A by-election','Parliamentary')):continue
   if '|'in l:
    cells=[v.strip() for v in l.split('|')];n=cells[0];v=cells[1] if len(cells)>1 else '';share=cells[2] if len(cells)>2 else '';lo=cells[3] if len(cells)>3 else '';up=cells[5] if len(cells)>5 else ''
    conv=lambda q:float(q.replace(',','')) if re.fullmatch(r'\d[\d,]*(?:\.\d+)?',q) else None
    v,share,lo,up=map(conv,[v,share,lo,up]);
    if v is None and n=='Independence Party' and both:lo=0;up=conv(cells[-2])
    lo=int(lo) if lo is not None else 0;up=int(up) if up is not None else 0
   else:
    m=re.search(r'\d',l)
    if not m:continue
    n=l[:m.start()].strip();rest=l[m.start():];tokens=re.findall(r'[+–−-]?\d[\d,]*(?:\.\d+)?|New',rest);nums=[float(t.replace(',','').replace('–','-').replace('−','-')) if t!='New' else None for t in tokens]
    if len(nums)<3:continue
    v,share,lo=nums[:3];lo=int(lo);up=int(nums[4 if changes else 3]) if both else 0
   if n and n not in ['Party','Seats'] and (v is not None or lo or up):items.append(dict(name=n,votes=v,share=share,lower=lo,upper=up))
  if items and total:out.append(dict(rows=items,totalVotes=total[0],totalSeats=int(total[2])+(int(total[4 if changes else 3]) if both else 0),both=both))
 return out
# Source-specific constituency ballots and at-large upper-house renewals.
for name,x in WEB.items():
 if 'parliamentary' not in name:continue
 y=int(re.search(r'\d{4}',name)[0]);upper=name.startswith('August_1916') or y in [1922,1926,1930];suffix='october' if name.startswith('October') else 'july' if name.startswith('July') else 'june' if name.startswith('June') else ''
 tabs=parse_tables(x)
 dateseries=AT if upper else TURN;matches=[(k,label) for k,label in dateseries['dimension']['Year']['category']['label'].items() if label.startswith(str(y))]
 if len(matches)>1 and suffix:matches=[m for m in matches if suffix.lower() in m[1].lower()]
 for ti,t in enumerate(tabs or [None]):
  match=matches[ti] if upper and len(matches)>ti else matches[0] if matches else None;e=base(y,'Alþingi upper house' if upper else 'Alþingi',('by-election' if upper and ti else suffix),official_date(match[1]) if match else None)
  if y==1908:e['startDate']='1908-09-10';e['precision']='day';e['endDate']=''
  e['sources']=[src('Historical electoral system and result tables',x['url'])]
  if match:
   e['turnout']=cell(dateseries,Year=match[0],**{'Votes and voters':'4'});e['sources'].append(src('Statistics Iceland: historical national turnout','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__kosningayfirlit/'+('KOS02002' if upper else 'KOS02001')+'.px/'))
  if t:
   raw=[];fractions=[];divisions=[]
   for rr in t['rows']:
    v=rr['votes'];raw.append(dict(name=rr['name'],value=v));whole=int(v) if v is not None and v.is_integer() else None
    if whole is None and v is not None:fractions.append(rr['name']+': '+str(v))
    row(e,rr['name'],rr['name'],whole,rr['share'],rr['lower']+rr['upper'])
    if t['both']:divisions.append(rr['name']+f": lower {rr['lower']}, upper {rr['upper']}")
   e['totalSeats']=t['totalSeats'];e['summary']=f"{t['totalSeats']} seats are reported in the cited {'upper-house cohort' if upper else 'Alþingi result table'}."
   if upper:e['notes']+=' This is a separate nationwide election of upper-house members, not a second copy of a constituency ballot. Seats count only the cohort elected, not the full upper house.';e['snap']=bool(ti)
   if t['both']:
    e['notes']+=' The published table describes both parliamentary divisions. Party seat totals combine lower and upper houses; the popular vote is counted once. Division allocation: '+'; '.join(divisions)+'.'
    if y<=1933:e['notes']+=' Upper-house composition includes continuing nationally elected members. These are post-election composition totals, not a claim that every seat was newly contested.'
   if fractions:e['weightedVotes']=True;e['resultCoverage']='partial';e['voteBasis']='Historical allocated vote equivalents; fractional allocations are detailed in the notes';e['notes']+=' Reported fractional vote equivalents: '+'; '.join(fractions)+'. These are historical allocations rather than whole-ballot counts.'
   finish(e,t['totalVotes'],t['totalSeats'],raw)
  elif y<=1900:
   seats=20 if y==1844 else 30;row(e,'Elected non-party representatives','',None,None,seats);e['totalSeats']=seats;e['resultCoverage']='partial';e['voteBasis']='Elected non-party representatives; no national party vote';e['notes']+=' The table counts elected representatives only; royal appointees and deputies are not added. No political party vote or 100% vote share is inferred.';e['summary']=f'{seats} elected non-party representatives in the restored Althing.';finish(e,expected_seats=seats)
  else:
   e['totalSeats']=30 if y<=1903 else 34;e['summary']='Historical general election under the franchise and constituency system then in force.';e['notes']+=' The cited sources establish the election and turnout but do not provide a verified national party seat allocation or party vote total. Royal appointments are excluded from the number of elected seats.';finish(e)
# Modern national party votes, shares and mandates from the same official table.
d=json.loads((P/'statice-KOS02121.json').read_text())
for code,ystr in d['dimension']['Year']['category']['label'].items():
 y=int(ystr);datekey,label=next((k,l) for k,l in TURN['dimension']['Year']['category']['label'].items() if l.startswith(str(y)));e=base(y,date=official_date(label));e['sources']=[src('Statistics Iceland: national parliamentary results 1963–2024','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__althingi__althurslit/KOS02121.px/'),src('Statistics Iceland: national turnout','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__kosningayfirlit/KOS02001.px/')];valid=cell(d,Category='0',Year=code,**{'Political organisation':'0'});total=cell(d,Category='2',Year=code,**{'Political organisation':'0'})
 for p,n in d['dimension']['Political organisation']['category']['label'].items():
  if p=='0':continue
  v=cell(d,Category='0',Year=code,**{'Political organisation':p});s=cell(d,Category='2',Year=code,**{'Political organisation':p})
  if v is None and s is None:continue
  if not v and not s:continue
  row(e,ALIASES.get(n,n),ALIASES.get(n,n),v,round(v/valid*100,2) if v is not None else None,s);primary.append(dict(id=e['id'],partyCode=p,votes=v,seats=s))
 if y==2024:
  # The detailed national table includes the 42 Responsible Future ballots omitted by the summary series.
  full=json.loads((P/'statice-KOS02018.json').read_text());names={'B':'Progressive Party','C':'Reform','D':'Independence Party','F':"People's Party",'J':'Socialist Party of Iceland','L':'Democratic Party – Association for Self-Determination','M':'Centre Party','P':'Pirate Party','S':'Social Democratic Alliance','V':'Left-Green Movement','Y':'Responsible Future'};e['results']=[];valid=cell(full,Category='1',**{'Political organisation':'A'});total=cell(full,Category='3',**{'Political organisation':'A'})
  primary[:]=[r for r in primary if r['id']!=e['id']]
  for pc,n in names.items():
   v=cell(full,Category='1',**{'Political organisation':pc});ss=cell(full,Category='3',**{'Political organisation':pc});row(e,n,n,v,round(v/valid*100,2),ss);primary.append(dict(id='world-iceland-2024-althingi',partyCode=pc,votes=v,seats=ss,table='KOS02018'))
  e['sources'][0]=src('Statistics Iceland: complete national parliamentary results 2024','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__althingi__althurslit/KOS02018.px/');e['notes']+=' The detailed national table includes 42 Responsible Future votes that are omitted from the long-run summary series; the detailed table is used for this election.'
 e['results'].sort(key=lambda r:-(r['votes'] or 0));e['turnout']=cell(TURN,Year=datekey,**{'Votes and voters':'4'});e['totalSeats']=total;e['summary']=f'{total} members returned to the Alþingi.';e['notes']+=' National Statistics Iceland party categories; vote shares are calculated from exact valid votes and rounded to two decimal places. Residual categories are retained without inventing allocations to individual minor lists.'
 if y<1991:e['notes']+=' The Althing then operated in two divisions; this is their combined membership elected through the same national contest, not duplicate lower- and upper-house popular ballots.'
 if y==2024:
  previous=next(r['data'] for r in json.loads((P/'pre-import-backup.json').read_text()) if r['kind']=='world_election');e['id']=previous['id'];e['title']='Iceland Alþingi parliamentary election 2024';e['snap']=previous['snap'];e['government']=previous['government'];e['summary']=previous['summary'];e['round']=previous['round'];e['version']=previous['version']+1
  for i,r in enumerate(e['results'],1):r['id']=e['id']+'-r'+str(i)
 finish(e,valid,total)
# Presidents: one indirect founding election, ten contested popular polls, eleven unopposed renewals.
pres_dates={1952:'1952-06-29',1968:'1968-06-30',1980:'1980-06-29',1988:'1988-06-25',1996:'1996-06-29',2004:'2004-06-26',2012:'2012-06-30',2016:'2016-06-25',2020:'2020-06-27',2024:'2024-06-01'}
for id,dim in [('KOS07112','Candidate and year of election'),('KOS07110','Candidates and year of election')]:
 d=json.loads((P/('statice-'+id+'.json')).read_text());groups={}
 for k,label in d['dimension'][dim]['category']['label'].items():
  m=re.search(r'(\d{4})$',label);y=int(m[1]);n=label[:m.start()].strip();groups.setdefault(y,[]).append((k,n))
 for y,entries in groups.items():
  e=base(y,'Presidency',date=(pres_dates[y],'','day'));e['sources']=[src('Statistics Iceland: presidential candidate results','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__forsetakosningar/'+id+'.px/'),src('Election date and context','https://en.wikipedia.org/wiki/'+str(y)+'_Icelandic_presidential_election')];valid=None
  for k,n in entries:
   v=cell(d,**{dim:k,'Valid votes' if id=='KOS07110' else 'Unit':'0'});sh=cell(d,**{dim:k,'Valid votes' if id=='KOS07110' else 'Unit':'1'})
   if n in ['Total','Alls']:valid=v;continue
   row(e,n,'Independent',v,sh);primary.append(dict(id=e['id'],candidate=n,votes=v,share=sh))
  e['results'].sort(key=lambda r:-(r['votes'] or 0));best=e['results'][0];best['winner']=True;e['summary']=best['name']+' elected President of Iceland.';e['notes']+=' Candidates stand for the presidency as individuals; no personal ideology is inferred from former party membership. A plurality in a single popular ballot elects the president.'
  turnout_source=json.loads((P/'statice-KOS07100.json').read_text());yk=next(k for k,n in turnout_source['dimension']['Year']['category']['label'].items() if n==str(y));ballots=cell(turnout_source,Year=yk,Votes='0',Unit='0');e['voteBasis']='Valid popular candidate votes; blank and invalid ballots excluded';
  turnout_path=P/'statice-KOS02004.json'
  if turnout_path.exists():
   td=json.loads(turnout_path.read_text());tk=next(k for k,l in td['dimension']['Year']['category']['label'].items() if l.startswith(str(y)));e['turnout']=cell(td,Year=tk,**{'Votes and voters':'4'});e['sources'].append(src('Statistics Iceland: presidential turnout','https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__kosningar__kosningayfirlit/KOS02004.px/'))
  else:
   prose=WEB.get(str(y)+'_Icelandic_presidential_election',{}).get('prose','');m=re.search(r'Turnout[^\d]{0,20}(\d+(?:\.\d+)?)%',prose);e['turnout']=float(m[1]) if m else None
  finish(e,valid)
for name,x in WEB.items():
 if 'presidential' not in name:continue
 y=int(name[:4]);p=x['prose']
 if y in pres_dates:continue
 e=base(y,'Presidency');e['sources']=[src('Presidential return and election context',x['url'])]
 if y==1944:
  e.update(startDate='1944-06-17',precision='day',electionMethod='indirect',voteBasis='Valid ballots cast by members of the Althing; not a popular election',turnout=96.15)
  row(e,'Sveinn Björnsson','Independent',None,85.71,ev=30,winner=True);row(e,'Jón Sigurðsson','Independent',None,14.29,ev=5);e['summary']='Sveinn Björnsson elected the first President of Iceland by the Althing.';e['notes']+=' Parliament selected the first president for a one-year term. The 35 valid candidate ballots exclude 15 blank or invalid ballots. Turnout describes parliamentary participation, not a national electorate.';finish(e,35);continue
 assert 'uncontested'in p.lower() or 'unopposed'in p.lower(),name
 person='Sveinn Björnsson' if y<1952 else 'Ásgeir Ásgeirsson' if y<1968 else 'Kristján Eldjárn' if y<1980 else 'Vigdís Finnbogadóttir' if y<1996 else 'Ólafur Ragnar Grímsson';row(e,person,'Independent',None,None,winner=True);e['summary']=person+' returned unopposed as President of Iceland.';e['voteBasis']='Unopposed return; no popular ballot took place';e['notes']+=' The incumbent was the only valid candidate and was returned without a poll. Votes, vote share and turnout are not applicable; no fabricated 100% share is entered.';finish(e)
# The nationwide 2010 constitutional assembly ballot was subsequently annulled.
ct=(P/'constituent-source.txt').read_text();lines=[]
for l in ct.splitlines():
 m=re.match(r'L\d+: (.*)',l)
 if m:lines.append(re.sub(r'【\d+†([^】]+)】',lambda m:m[1].split('†')[0],m[1]))
e=base(2010);e.update(id='world-iceland-constitutional-assembly-2010',title='Iceland Constitutional Assembly election (annulled) 2010',body='Constitutional Assembly',startDate='2010-11-27',precision='day',seriesId='IS-constituent-assembly',totalSeats=25,turnout=35.95,resultCoverage='partial',voteBasis='First-preference candidate votes in the nationwide STV ballot; outcome later annulled',summary='A nationwide Constitutional Assembly ballot was held on 27 November 2010; its result was annulled on 25 January 2011.',notes='The table preserves first preferences for the 25 initially returned candidates and the aggregate for the remaining 497 candidates. These are not final transferable-vote tallies. No valid elected seats or current winners are assigned because the Supreme Court annulled the election. The subsequent appointment of a Constitutional Council was a separate process. The planned assembly had 25 seats.',sources=[src('Historical first-preference results and annulment','https://en.wikipedia.org/wiki/2010_Icelandic_Constitutional_Assembly_election')])
in_table=False
for l in lines:
 if l.startswith('Candidate') and 'First pref.'in l:in_table=True;continue
 if not in_table or '|'not in l:continue
 c=[v.strip() for v in l.strip().strip('|').split('|')]
 if c[0]=='Total':break
 if c[0]=='Other 497 candidates':row(e,c[0],'',int(c[1].replace(',','')),float(c[2]));continue
 if len(c)>=4 and re.fullmatch(r'\d[\d,]*',c[-2]):row(e,c[0],'Independent',int(c[-2].replace(',','')),float(c[-1]))
assert len(e['results'])==26,len(e['results']);finish(e,82335)
# Compare like-for-like general-election composition; do not compare at-large cohorts with constituency contests.
previous={}
for e in sorted([e for e in records if e['body']=='Alþingi'],key=lambda e:e['startDate']):
 for r in e['results']:
  if r.get('partyId') in previous:r['previousSeats']=previous[r['partyId']]
 previous={r['partyId']:r['seats'] for r in e['results'] if r.get('partyId') and r['seats'] is not None}
records.sort(key=lambda e:(e['startDate'],e['id']))
for n,d in [('records',records),('parties',list(profiles.values())),('reconciliation',audit),('primary-reconciliation',primary)]: (P/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(len(records),'records',sum(len(e['results']) for e in records),'rows',len(profiles),'parties',len([e for e in records if not e['results']]),'without tables')
