"""Build the UK's Commons chronology and historical elected Lords components.
Generates reviewed fixtures only; never writes to the live database.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from us_presidential_html import Tables,expand
import re,json,hashlib,datetime,collections
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/uk-history';OUT=ROOT/'scripts/uk-historical-election-import';CHECKED='2026-10-09';audit=[];reconciliation=[]
links=json.loads((OUT/'election-links.json').read_text());primary=json.loads((OUT/'primary-links.json').read_text());controls=json.loads((OUT/'primary-extract.json').read_text());baseline=json.loads((OUT/'pre-import-backup.json').read_text());records=[r['data'] for r in baseline if r['kind']=='world_election']
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def integer(v):
 v=v.strip();return int(v.replace(',','')) if re.fullmatch(r'\d+(?:,\d{3})*',v) else None
def number(v):
 v=v.strip().replace('%','');return float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
def read(key,url=None):
 p=CACHE/(key+'.html');s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,script,style'):n.decompose()
 if not any(a['file']==p.name for a in audit):audit.append(dict(file=p.name,url=url or primary.get(key) or links.get(key),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return s
def grid(t):
 for c in t.select('td,th'):
  for a in ['colspan','rowspan']:
   if c.has_attr(a):c[a]=re.match(r'\d+',c[a]).group()
 p=Tables();p.feed(str(t));return expand(p.tables[0]['rows'])
def dates(text,year):
 out=[]
 for m in re.finditer(r'(\d{1,2})\s+('+'|'.join(MONTHS)+r')(?:\s+(\d{4}))?',text):
  d,mo,y=m.groups();out.append(datetime.date(int(y) if y else year,MONTHS[mo],int(d)).isoformat())
 return out
colors={'CON':'#0087dc','LAB':'#e4003b','LD':'#fdbb30','PC/SNP':'#808080','UUP':'#1683c4','SDLP':'#2aa82c','DUP':'#d46a4a','SF':'#326760'}
def base(scope,date,end='',title=None):
 title=title or {'commons':'House of Commons — general election','scottish-peers':'House of Lords — Scottish representative peers','lords-officers':'House of Lords — hereditary office-holder selection','lords-groups':'House of Lords — hereditary party/group selections'}[scope]
 return dict(id='world-uk-'+scope+'-'+date,countryId='gb',title=title,type='parliamentary',body='House of Commons' if scope=='commons' else 'House of Lords — elected component',startDate=date,endDate=end,precision='day',dateStatus='confirmed',status='held',publication='published',round='General' if scope in ['commons','scottish-peers'] else 'Restricted peer selection',seriesId='UK-HOC' if scope=='commons' else 'UK-LORDS-SCOTTISH' if scope=='scottish-peers' else 'UK-LORDS-HEREDITARY',snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=1,electionMethod='direct' if scope=='commons' else 'indirect',linkedElectionIds=[])
def result(e,name,votes=None,share=None,seats=None,party=None,color='#808080',winner=False):
 e['results'].append(dict(id=e['id']+'-'+str(len(e['results'])+1),name=name,party=name if party is None else party,color=color,votes=votes,share=share,seats=seats,electoralVotes=None,winner=winner,ideologyIds=[]))
# First nine elections: reviewed secondary chronology. Official Library dates
# establish every later polling interval, distinct from result declarations.
chronology={};overview=read('overview')
for t in overview.select('table'):
 for tr in t.select('tr'):
  cells=tr.find_all(['td','th'],recursive=False)
  if len(cells)<3:continue
  a=next((a for a in cells[0].select('a[href]') if 'United_Kingdom_general_election' in a['href']),None)
  if a:
   key=a['href'].rsplit('/',1)[-1];year=int(re.search(r'\d{4}',key).group());ds=dates(txt(cells[2]),year)
   if ds:chronology[key]=[ds[0],ds[-1] if len(ds)>1 else '']
s=read('official-dates')
for tr in s.select('tr'):
 cells=tr.find_all(['td','th'],recursive=False)
 if len(cells)!=2 or not re.match(r'\d{4}',txt(cells[0])):continue
 label=txt(cells[0]);year=int(label[:4]);key=('January_' if 'Jan' in label else 'December_' if 'Dec' in label else 'February_' if 'Feb' in label else 'October_' if 'Oct' in label else '')+str(year)+'_United_Kingdom_general_election'
 ds=dates(txt(cells[1]).split('(')[0],year)
 if ds:chronology[key]=[ds[0],ds[-1] if len(ds)>1 else '']
assert len(chronology)==58,len(chronology)
for key,(date,end) in sorted(chronology.items(),key=lambda x:x[1][0]):
 year=int(date[:4])
 if year>=2010:continue
 e=base('commons',date,end);e['totalSeats']=controls['capacities'][str(year)];e['majorityThreshold']=e['totalSeats']//2+1
 e['sources']=[dict(label='Commons Library: historical seat capacities',url=controls['seatSource'])]
 if year>=1832:e['sources'].insert(0,dict(label='Commons Library: national election dates and polling intervals',url=primary['official-dates']))
 e['sources'].append(dict(label='Historical election and result bibliography',url=links[key]))
 s=read(key);e['notes']='Only House of Commons seats are counted; the upper chamber has a separate institutional history. Seat totals include unopposed returns and abstentionist MPs. Historic constituencies, franchise and territory differ from today. '
 if year>=1918:
  code=str(year)+('F' if key.startswith('February_') else 'O' if key.startswith('October_') else '')
  rows=controls['national'][code];denom=rows[0]['totalVotes'];assert rows[0]['totalSeats']==e['totalSeats']
  labels={'CON':'Conservative and source-grouped allies' if year<=1970 else 'Conservative','LAB':'Labour','LD':'Liberal and Coalition Liberal groups' if year==1918 else 'Liberal and National Liberal groups' if year==1922 else 'Liberal / Independent Liberal group' if year==1931 else 'SDP–Liberal Alliance' if year in [1983,1987] else 'Liberal Democrat' if year>=1992 else 'Liberal','PC/SNP':'Plaid Cymru and Scottish National Party — source aggregate','Other':'Other parties and non-party candidates'}
  for r in rows:
   if r['code']=='Other':continue
   if r['votes'] or r['seats']:result(e,labels[r['code']],r['votes'],round(r['votes']/denom*100,4),r['seats'],color=colors.get(r['code'],'#808080'),party='' if r['code']=='PC/SNP' else None)
  other=next(r for r in rows if r['code']=='Other').copy()
  # Rebase the explicitly separate NI parties onto the UK denominator. Do not
  # copy NI percentages or split an unreported residual by inference.
  if year>=1974:
   for r in controls['northernIreland'][code]:
    if r['code'] not in ['UUP','SDLP','DUP','SF'] or not(r['votes'] or r['seats']):continue
    assert r['votes']<=other['votes'] and r['seats']<=other['seats']
    result(e,{'UUP':'Ulster Unionist Party','SDLP':'Social Democratic and Labour Party','DUP':'Democratic Unionist Party','SF':'Sinn Féin'}[r['code']],r['votes'],round(r['votes']/denom*100,4),r['seats'],color=colors[r['code']]);other['votes']-=r['votes'];other['seats']-=r['seats']
  result(e,labels['Other'],other['votes'],round(other['votes']/denom*100,4),other['seats'],party='')
  assert sum(r['votes'] for r in e['results'])==denom;assert sum(r['seats'] for r in e['results'])==e['totalSeats']
  e.update(resultStatus='final',resultCoverage='complete',turnout=controls['turnout'][code],voteBasis=f'Commons Library reported national vote total ({denom:,}); source group definitions retained')
  e['sources'].insert(0,dict(label='Commons Library: national results, source group definitions and Northern Ireland details',url=controls['resultSource']))
  e['notes']+='The primary Commons Library historical series takes precedence over conflicting secondary counts. Results use its published categories, not invented party-by-party detail. The CON series includes source-grouped National/National Liberal/National Labour allies in specified historical years; the Liberal series includes Coalition Liberal in 1918, National Liberal in 1922 and Independent Liberal in 1931. SNP and Plaid Cymru remain a labelled source aggregate, not a claimed alliance. Explicit Northern Ireland parties from 1974 are deducted once from UK Other and use the UK denominator. Shares are calculated from the exact source vote totals; historical published rounded percentages may differ. The Speaker follows the source convention: former party through 1992, Other from 1997. Turnout follows the source electorate convention, excluding unopposed contests where relevant. '
  if year<=1945:e['weightedVotes']=True;e['notes']+='Plural/university voting and multi-member districts prevent interpreting every historical candidate-vote mark as a unique person or ballot. '
  if year==1918:e['notes']+='The 1918 territorial total includes all Ireland; from 1922 only Northern Ireland remains. '
  if year==1945:e['endDate']='1945-07-19';e['notes']+='Most polling was on 5 July; 22 constituencies polled on 12 July and one on 19 July. Results declaration on 26 July is not the polling end date. '
 else:
  selected=None
  for t in s.select('table'):
   if t.find_parent('table') or 'infobox' in t.get('class',[]):continue
   g=grid(t);hi=next((i for i,r in enumerate(g[:6]) if 'Elected' in [c['text'] for c in r] and 'No.' in [c['text'] for c in r] and 'Party' in [c['text'] for c in r]),None)
   if hi is not None:selected=(g,hi);break
  if selected:
   g,hi=selected;h=[c['text'] for c in g[hi]];ni=max(i for i,v in enumerate(h) if v=='Party');si=h.index('Elected');vi=h.index('No.');pi=h.index('%')
   for row in g[hi+1:]:
    if len(row)<=max(ni,si,vi,pi):continue
    name=row[ni]['text'];v=integer(row[vi]['text']);seats=integer(row[si]['text'])
    if not name or name.lower().startswith(('total','source')) or (v is None and seats is None):continue
    color=row[0].get('bgcolor') or '#808080';m=re.search(r'background(?:-color)?\s*:\s*(#[a-f0-9]{6})',row[0].get('style',''),re.I)
    if m:color=m.group(1)
    if not re.fullmatch(r'#[a-f0-9]{6}',color,re.I):color='#808080'
    result(e,name,v,number(row[pi]['text']),seats,color=color)
   e['weightedVotes']=True;e['voteBasis']='Reported historical candidate votes in contested seats; multi-member districts and unopposed returns apply';e['notes']+='Historical results and party labels follow the reviewed national table and bibliography. Votes in multi-member districts are candidate selections, not necessarily unique voters. Votes are not imputed for unopposed seats; published percentages remain on the source basis. '
  else:
   info=s.select_one('table.infobox');fields={}
   for tr in info.select('tr'):
    cells=tr.find_all(['td','th'],recursive=False)
    if cells and txt(cells[0]) in ['Party','Seats won','Popular vote','Percentage']:fields[txt(cells[0])]=[txt(c) for c in cells[1:]]
   for i,name in enumerate(fields.get('Party',[])):
    result(e,name,integer(fields.get('Popular vote',['']*len(fields['Party']))[i]),number(fields.get('Percentage',['']*len(fields['Party']))[i]),integer(fields['Seats won'][i]))
   e['voteBasis']='Partial historical party/seat reconstruction; complete national vote denominator not established';e['notes']+='Only source-supported leading party/faction figures are entered. A complete national party allocation or voter denominator is not established; missing seats and votes are not inferred. '
  if e['results']:e['resultStatus']='final'
  if sum(r['seats'] or 0 for r in e['results'])>e['totalSeats']:
   e['notes']+='The reported seat allocations exceed the official chamber capacity; conflicting seat figures are omitted pending reconciliation. '
   for r in e['results']:r['seats']=None
  if year>=1832 and sum(r['seats'] or 0 for r in e['results'])==e['totalSeats']:e['resultCoverage']='complete'
  if sum(r['share'] or 0 for r in e['results'])>100.2:
   e['notes']+='Inconsistent published percentages are omitted; no normalization is inferred. ';e['resultCoverage']='partial'
   for r in e['results']:r['share']=None
 records.append(e)
# Scottish representative elections: exact peer-only days, not Commons days.
s=read('scottish-election-dates');g=grid(s.select('table')[0]);scottish=[]
for row in g[1:]:
 if len(row)<2 or row[1]['text']!='G':continue
 ds=dates(row[0]['text'],1700)
 if not ds or ds[0]<'1801':continue
 if ds[0]=='1922-01-13':continue # Hansard confirms a three-seat by-election, mislabelled G in the secondary chronology.
 e=base('scottish-peers',ds[0]);e['totalSeats']=16;e['voteBasis']='Selection among eligible Scottish hereditary peers; national public vote not applicable';e['notes']='Election of sixteen Scottish representative peers for the elected component of the UK House of Lords. Only peers eligible under the historical Scottish system voted. Peers present is not the full eligible electorate and is not a turnout denominator. No whole-chamber party allocation or public vote share is inferred. A full candidate/seat allocation remains unentered where unavailable. The Peerage Act 1963 ended this system. '
 e['sources']=[dict(label='Historical representative-peer election chronology and bibliography',url=primary['scottish-election-dates']),dict(label='Commons Library: peerage membership and representative-peer system',url=primary['official-lords-membership']),dict(label='National Records of Scotland: representative-peer election archive',url=primary['official-nrs-peers'])]
 scottish.append(e);records.append(e)
# The final 1959 peer contest has an explicit candidate-vote table.
e=next(e for e in scottish if e['startDate']=='1959-10-06');s=read('scottish-1959');t=next(t for t in s.select('table') if 'Peer' in txt(t) and 'Votes' in txt(t));unsuccessful=False
for row in grid(t)[1:]:
 if len(row)<2:continue
 name=row[0]['text'];v=integer(row[1]['text'])
 if name=='Unsuccessful':unsuccessful=True;continue
 if v is not None:result(e,name,v,seats=0 if unsuccessful else 1,party='',winner=not unsuccessful)
assert sum(r['seats'] for r in e['results'])==16
e.update(resultStatus='final',weightedVotes=True,voteBasis='Individual peer-candidate endorsements; percentages not inferred from peers present');e['sources'].insert(0,dict(label='Parliament Hansard: confirmed final representative-peer polling date',url=primary['official-1959-date']));e['sources'].append(dict(label='1959 candidate totals and contemporary election-minute bibliography',url=links['scottish-1959']));e['notes']+='The final 1959 contest records all candidate endorsements in the reviewed table, with sixteen elected. Individual endorsements may exceed the number of people voting; no percentage or turnout is inferred from the 25 peers physically present. '
# 1999 retained hereditary members: two ballots, 90 seats, not the whole Lords.
for scope,start,end,key,total in [('lords-officers','1999-10-27','1999-10-28','official-lords-1999-deputies',15),('lords-groups','1999-11-03','1999-11-04','official-lords-1999-results',75)]:
 e=base(scope,start,end);e['totalSeats']=total;e['voteBasis']='Official winning-member roster; vote counts and percentages not entered';e['resultStatus']='final';s=read(key)
 tables=[t for t in s.select('table') if not t.find_parent('table') and ('Strabolgi' in txt(t) or 'Milner of Leeds' in txt(t))];assert len(tables)==1
 for row in grid(tables[0]):
  text=row[0]['text'];party=''
  if scope=='lords-groups':
   party=next(p for p in ['Labour','Conservative','Cross-bench','Liberal Democrat'] if text.startswith(p));text=text.removeprefix(party).strip()
  names=[n.strip() for n in re.findall(r'(?:L|E|V|B|D|Ly|C)\.\s+.*?(?=(?:L|E|V|B|D|Ly|C)\.\s+|$)',text)]
  for name in names:result(e,name,seats=1,party=party,color={'Labour':'#e4003b','Conservative':'#0087dc','Liberal Democrat':'#fdbb30'}.get(party,'#808080'),winner=True)
 assert len(e['results'])==total,(scope,len(e['results']))
 e['sources']=[dict(label='Parliament: official retained hereditary-member election results',url=primary[key]),dict(label='Parliament: separate 15-member and 75-member election procedures',url=primary['official-lords-1999']),dict(label='Parliament Companion 2013: polling intervals, section 1.04 footnote 5',url=primary['official-lords-companion'])]
 e['notes']='Restricted indirect selection under the House of Lords Act 1999, not a public Senate election or an election of the whole House of Lords. The separate ballots elected 15 office-holders by the whole House and 75 retained hereditary peers within party/Crossbench groups. The two hereditary office-holders exempted without election are excluded from these 90 elected seats. Official winning rosters are transcribed; raw candidate votes, electorate counts and percentage denominators are not inferred. Polling on 27–28 October is distinct from the 29 October results announcement; polling on 3–4 November is distinct from the 5 November announcement. Subsequent individual hereditary by-elections are outside this general-election chronology. The 2026 reform ended hereditary membership rights; no future Lords general election is invented. '
 records.append(e)
# Related chambers/stages can have different days. Preserve recent existing IDs.
for e in records:
 if e['id'].startswith('world-uk-general-') or e['id']=='world-uk-commons-2024':continue
 if e['seriesId']=='UK-LORDS-SCOTTISH':
  nearby=[x for x in records if x['seriesId']=='UK-HOC' and abs((datetime.date.fromisoformat(x['startDate'])-datetime.date.fromisoformat(e['startDate'])).days)<130]
  if nearby:
   x=min(nearby,key=lambda x:abs((datetime.date.fromisoformat(x['startDate'])-datetime.date.fromisoformat(e['startDate'])).days));e['linkedElectionIds'].append(x['id']);x['linkedElectionIds'].append(e['id'])
 if e['seriesId']=='UK-LORDS-HEREDITARY':e['linkedElectionIds']=[x['id'] for x in records if x['seriesId']==e['seriesId'] and x['id']!=e['id']]
 e['summary']=e['body']+f': {e["totalSeats"]} seats in the recorded elected component.'
 reconciliation.append(dict(id=e['id'],voteBasis=e['voteBasis'],votes=sum(r['votes'] or 0 for r in e['results']),shareSum=round(sum(r['share'] or 0 for r in e['results']),4),seats=sum(r['seats'] or 0 for r in e['results']),totalSeats=e['totalSeats'],coverage=e['resultCoverage']))
for key,url in primary.items():
 p=CACHE/(key+('.xlsx' if 'xlsx' in key else '.csv' if 'csv' in key else '.html'))
 if p.exists() and not any(a['file']==p.name for a in audit):audit.append(dict(file=p.name,url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
records.sort(key=lambda e:(e['startDate'],e['id']));assert len(records)==len({e['id'] for e in records})
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,sources=audit),indent=2)+'\n');(OUT/'reconciliation.json').write_text(json.dumps(reconciliation,indent=2)+'\n')
print('Built',len(records),collections.Counter(e['seriesId'] for e in records));print('Partial',[e['id'] for e in records if e['resultCoverage']=='partial']);print('No results',[e['id'] for e in records if not e['results']])
