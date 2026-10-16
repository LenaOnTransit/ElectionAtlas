"""Reproducible Finland national archive from cited, cached result tables."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys
P=Path(__file__).parent/'finland-election-import';XS=json.loads((P/'source-extract.json').read_text());records=[];parties={};audit=[]
INFO={
'Social Democratic Party':('SDP','#e11931','social-democracy','Social_Democratic_Party_of_Finland'),
'National Coalition Party':('KOK','#006288','liberal-conservatism','National_Coalition_Party'),
'Centre Party':('KESK','#349a2b','agrarianism','Centre_Party_(Finland)'),
'Finns Party':('PS','#0066a4','national-conservatism','Finns_Party'),
'Left Alliance':('VAS','#bf1e24','democratic-socialism','Left_Alliance_(Finland)'),
'Green League':('VIHR','#61bf1a','green-politics','Green_League'),
"Swedish People's Party":('RKP','#ffdd00','social-liberalism','Swedish_People%27s_Party_of_Finland'),
'Christian Democrats':('KD','#183e81','christian-democracy','Christian_Democrats_(Finland)'),
'Movement Now':('Liik','#ae2375','liberalism','Movement_Now'),
}
def clean(s):return re.sub(r'\s*\[\s*[a-z]+\s*\]','',s).strip()
def num(s):
 s=re.sub(r'[\s,]','',s).rstrip('%');return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def src(label,url):return dict(label=label,url=url)
def profile(n,y):
 n=clean(n)
 if n.startswith(('Independent','Others','Other','Write-in','Candidature','Electoral Union','Supporters','General electoral','List ')) or ' – ' in n or '– 'in n or ' ( ' in n:return None
 key={'Agrarian League':'Centre Party','True Finns':'Finns Party','Finnish Christian League':'Christian Democrats'}.get(n,n)
 if n=="People's Party":key="People's Party (1932–1936)" if y<1940 else "People's Party of Finland"
 if n=='Centre Party' and y<1965:key='Centre Party (historical minor party)'
 if n=='Greens':key='Green electoral movement (pre-1987)' if y<1987 else 'Green League' if y==1987 else 'Greens (minor electoral list)'
 short,color,tag,page=INFO.get(key,('',None,None,None))
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 tags=[tag] if tag and (y>=1990 or key in ['Centre Party',"Swedish People's Party",'Christian Democrats']) else []
 if key not in parties:parties[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/fi/'+key)),country_id='fi',name=key,short_name=short,color=color,ideology_ids=['ideology-'+tag] if tag else [],notes='Colours are a display palette. '+('Party history: https://en.wikipedia.org/wiki/'+page if page else 'Historical organisation or electoral list; ideology unassessed. Similar names do not imply organisational continuity.'),archived=False)
 return parties[key],tags,page
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def dates(x,y):
 p=x['infobox'];m=re.search(r'(\d+)[–−-](\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:return f'{y}-{MONTHS[m[3]]:02}-{int(m[1]):02}',f'{y}-{MONTHS[m[3]]:02}-{int(m[2]):02}','day'
 m=re.search(r'(\d+) ([A-Z][a-z]+) [–−-] (\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:return f'{y}-{MONTHS[m[2]]:02}-{int(m[1]):02}',f'{y}-{MONTHS[m[4]]:02}-{int(m[3]):02}','day'
 m=re.search(r'(?:between|on) (\d+) and (\d+) ([A-Z][a-z]+) '+str(y),x['prose'])
 if m:return f'{y}-{MONTHS[m[3]]:02}-{int(m[1]):02}',f'{y}-{MONTHS[m[3]]:02}-{int(m[2]):02}','day'
 m=re.search(r'(\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:return f'{y}-{MONTHS[m[2]]:02}-{int(m[1]):02}','','day'
 return f'{y}-01-01','','year'
def base(x,body,suffix='',date=None,method='direct'):
 y=int(x['name'][:4]);d,end,precision=dates(x,y)
 if date:d,end,precision=date,'','day'
 e=dict(id=f"world-finland-{'eduskunta' if body=='Eduskunta' else 'presidential'}-{y}"+('-'+suffix if suffix else ''),countryId='fi',title=f"Finland {body} election"+(' ('+suffix.replace('-',' ')+')' if suffix else '')+f" {y}",type='parliamentary' if body=='Eduskunta' else 'presidential',body=body,startDate=d,endDate=end,precision=precision,dateStatus='confirmed',status='held',publication='published',round=suffix.replace('-',' '),seriesId='FI-eduskunta' if body=='Eduskunta' else 'FI-president',snap=False,summary='',government='',turnout=None,totalSeats=200 if body=='Eduskunta' else None,resultStatus='final',resultCoverage='complete',voteBasis='Valid party/list votes' if body=='Eduskunta' else 'Valid candidate votes',results=[],sources=[src('Historical result table and election context',x['url'])],checked='2026-10-16',notes='Blank and rejected ballots are excluded from result shares. Colours are a display palette. Unknown values remain unreported.',articleId='',version=1,electionMethod=method)
 return e

def row(e,n,party,v,p,s=None,ev=None):
 pr=profile(party,int(e['startDate'][:4]));r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=clean(n),party=clean(party),color=pr[0]['color'] if pr else '#808080',votes=v,share=p,seats=s,previousSeats=None,electoralVotes=ev,winner=False,ideologyIds=['ideology-'+t for t in pr[1]] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=int(e['startDate'][:4]),note='Broad party tradition for this period; not an assessment of the individual candidate.',sources=[src('Party history and tradition','https://en.wikipedia.org/wiki/'+pr[2])])
 e['results'].append(r)
def finish(e,x,expected,seat=None):
 v=sum((r['votes'] if r['votes'] is not None else r['electoralVotes']) or 0 for r in e['results']);s=sum(r['seats'] or 0 for r in e['results']);assert e['results'],e['id']
 if expected is not None and expected!=v:e['notes']+=f' Listed results sum to {v:,}, while the cited table reports {expected:,}; no votes have been assigned to resolve this source discrepancy.';e['resultCoverage']='partial'
 if seat is not None:assert s==seat,(e['id'],s,seat)
 audit.append(dict(id=e['id'],source=x['url'],sha256=x['sha256'],expectedVotes=expected,recordedVotes=v,expectedSeats=seat,recordedSeats=s));records.append(e)

def table(x,kind):return next(t for t in x['tables'] if any(kind in r and 'Votes'in r and ('Seats'in r if kind=='Party' else True) for r in t[:4]))
for x in XS:
 y=int(x['name'][:4])
 if 'parliamentary' in x['name']:
  e=base(x,'Eduskunta');t=table(x,'Party');hi,h=next((i,r) for i,r in enumerate(t[:4]) if 'Votes'in r and 'Seats'in r);ni=max(i for i,v in enumerate(h) if v=='Party');vi=h.index('Votes');pi=h.index('%');si=h.index('Seats');total=None
  for r in t[hi+1:]:
   if len(r)<=si:continue
   if r[ni]=='Total':total=integer(r[vi]);break
   if integer(r[vi]) is not None:row(e,r[ni],r[ni],integer(r[vi]),num(r[pi]),integer(r[si]))
  for r in t:
   if r and r[0]=='Registered voters/turnout':e['turnout']=num(r[pi])
  e['summary']='200 representatives elected to the Eduskunta, Finland’s unicameral parliament.';e['notes']+=' Joint electoral lists remain joint results rather than being divided into invented party totals. Previous seats compare the same organisation in the immediately preceding parliamentary election.'
  finish(e,x,total,200);continue
 # Distinct elector elections and candidate selection ballots.
 electors=next((t for t in x['tables'] if any('Seats'in r and 'Votes'in r for r in t[:3])),None)
 if electors:
  e=base(x,'Presidential','elector-election');h=next(r for r in electors[:3] if 'Seats'in r);vi=h.index('Votes');pi=h.index('%');si=h.index('Seats');total=None;seats=None
  e['totalSeats']=301 if y>=1982 else 300;e['voteBasis']='Popular votes for presidential electors; seats are electors, not parliamentary seats';e['notes']+=' This elected the presidential electoral college. Candidate ballots cast by the college are a separate record. Alliance subtotal rows are excluded to avoid double counting.'
  for r in electors[electors.index(h)+1:]:
   if len(r)<=si:continue
   if r[0]=='Total':total=integer(r[vi]);seats=integer(r[si]);break
   if 'Total' in r[:vi]:continue
   n=r[vi-1]
   if integer(r[vi]) is not None:row(e,n,n,integer(r[vi]),num(r[pi]),integer(r[si]))
  for r in electors:
   if r and r[0]=='Registered voters/turnout':e['turnout']=num(r[pi])
  finish(e,x,total,seats)
 candidates=[t for t in x['tables'] if any('Candidate'in r and 'Votes'in r for r in t[:3])]
 for ti,t in enumerate(candidates):
  hi,h=next((i,r) for i,r in enumerate(t[:3]) if 'Candidate'in r and 'Votes'in r);cols=[i for i,v in enumerate(h) if v=='Votes'];ni=max(i for i,v in enumerate(h) if v=='Candidate');partyidx=h.index('Party');direct=y>=1994 or y==1988 and ti==0
  rounds=range(len(cols)) if direct else [len(cols)-1]
  for ri in rounds:
   vi=cols[ri];suffix=('electoral-college' if not direct and electors else 'round-'+str(ri+1) if len(cols)>1 else 'popular-vote' if y==1988 and direct else 'electoral-college' if not direct and electors else '')
   date=None
   if direct:
    dd=re.findall(r'(\d+) ([A-Z][a-z]+) '+str(y),x['infobox']);date=f'{y}-{MONTHS[dd[ri][1]]:02}-{int(dd[ri][0]):02}' if dd and y!=1988 else None
   elif electors and y==1956:date='1956-02-15'
   e=base(x,'Presidential',suffix,date,'direct' if direct else 'indirect');
   if not direct and electors and not date:e['startDate']=f'{y}-01-01';e['endDate']='';e['precision']='year';e['notes']+=' The year is established; an exact college ballot date is not asserted here.'
   e['endDate']='' if not direct else e['endDate'];e['voteBasis']='Valid popular candidate votes' if direct else 'Final decisive candidate ballot in Parliament' if y in [1919,1946] else 'Final decisive candidate ballot in the electoral college'
   if not direct:e['notes']+=' This table reports the final decisive ballot, not a national popular vote. Public elector-election votes, where held, are recorded separately.'
   total=None
   for r in t[hi+1:]:
    if len(r)<=vi+1:continue
    if r[0]=='Total':total=integer(r[vi]);break
    n=r[ni];v=integer(r[vi])
    if v is not None:row(e,n,r[partyidx],v if direct else None,num(r[vi+1]),ev=v if not direct else None)
   for r in t:
    if r and r[0]=='Registered voters/turnout':e['turnout']=num(r[vi+1])
   final=not direct or ri==len(cols)-1 and y!=1988
   best=max(e['results'],key=lambda r:(r['votes'] if direct else r['electoralVotes']) or 0)
   if final:best['winner']=True;e['summary']=best['name']+' elected President of Finland.'
   else:
    e['summary']='Popular candidate ballot; the presidency was decided in a subsequent ballot.'
    if y!=1988:
     for r in sorted(e['results'],key=lambda r:-(r['votes'] or 0))[:2]:r['advanced']=True
   finish(e,x,total)
# Official national series: resident turnout is consistent across 1908–2023.
def cell(d,**kw):
 i=0
 for k,size in zip(d['id'],d['size']):
  idx=d['dimension'][k]['category']['index'];key=kw.get(k,next(iter(idx)));i=i*size+idx[key]
 return d['value'][i] if isinstance(d['value'],list) else d['value'].get(str(i))
turn=json.loads((P/'statfin-12i9.json').read_text());votes=json.loads((P/'statfin-13sw.json').read_text());mp=json.loads((P/'statfin-13t4.json').read_text());primary=[]
MAP={'03':'National Coalition Party','02':'Finns Party','01':'Social Democratic Party','04':'Centre Party','05':'Green League','06':'Left Alliance','07':"Swedish People's Party",'08':'Christian Democrats','09':'Movement Now'}
for e in records:
 if e['body']!='Eduskunta':continue
 y=e['startDate'][:4]
 if y in turn['dimension']['timeperiod_y']['category']['index']:
  e['turnout']=cell(turn,timeperiod_y=y,contentscode='evaa_aanpros_suom_as_skans');e['sources'].append(src('Statistics Finland: resident voting turnout, 1908–2023','https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__evaa/statfin_evaa_pxt_12i9.px/'));e['notes']+=' Turnout is the official percentage of eligible Finnish citizens resident in Finland, excluding citizens living abroad.'
 if y in votes['dimension']['timeperiod_y']['category']['index']:
  e['sources'].append(src('Statistics Finland: national party votes, 1983–2023','https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__evaa/statfin_evaa_pxt_13sw.px/'))
  total=cell(votes,timeperiod_y=y,puolue_19_20230101='SSS',contentscode='evaa_aanet')
  # Official table excludes Åland: compare named national parties, not the all-country total.
  for code,name in MAP.items():
   official=cell(votes,timeperiod_y=y,puolue_19_20230101=code,contentscode='evaa_aanet');r=next((r for r in e['results'] if r.get('partyId') and parties.get(name,{}).get('id')==r['partyId']),None)
   if official is not None and r:
    assert official==r['votes'],(e['id'],name,official,r['votes']);primary.append(dict(id=e['id'],party=name,votes=official,table='13sw'))
 if y in mp['dimension']['timeperiod_y']['category']['index']:
  e['sources'].append(src('Statistics Finland: elected MPs, 2003–2023','https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__evaa/statfin_evaa_pxt_13t4.px/'))
  for code,name in MAP.items():
   official=cell(mp,timeperiod_y=y,puolue_4_20230303=code);r=next((r for r in e['results'] if r.get('partyId') and parties.get(name,{}).get('id')==r['partyId']),None)
   if official is not None and r:assert official==r['seats'],(e['id'],name,official,r['seats']);primary.append(dict(id=e['id'],party=name,seats=official,table='13t4'))
(P/'primary-reconciliation.json').write_text(json.dumps(primary,ensure_ascii=False,indent=2)+'\n')
for e in records:
 if e['type']=='presidential':e['sources'].append(src('Office of the President: election procedures and exceptional selections','https://www.presidentti.fi/en/presidency/election-of-the-president/'))
# Parliamentary seat comparisons exclude electoral-college seats and coalition guesses.
previous={}
for e in sorted((e for e in records if e['body']=='Eduskunta'),key=lambda e:e['startDate']):
 for r in e['results']:
  if r.get('partyId') in previous:r['previousSeats']=previous[r['partyId']]
 previous={r['partyId']:r['seats'] for r in e['results'] if r.get('partyId') and r['seats'] is not None}
for e in records:
 if e['type']=='presidential':
  same=[r['id'] for r in records if r['type']=='presidential' and r['startDate'][:4]==e['startDate'][:4] and r['id']!=e['id']]
  if same:e['linkedElectionIds']=same
records.sort(key=lambda e:(e['startDate'],e['id']))
for n,d in [('records',records),('parties',list(parties.values())),('reconciliation',audit)]: (P/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(len(records),'elections',sum(len(e['results']) for e in records),'rows',len(parties),'parties')
