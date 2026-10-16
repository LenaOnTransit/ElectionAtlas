"""Build Norway's national archive; modern results come directly from Statistics Norway."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys,datetime,collections
P=Path(__file__).resolve().parent/'norway-election-import';C=P.parents[1]/'.cache/norway';EX=json.loads((P/'source-extract.json').read_text());records=[];profiles={};audit=[]
INFO={
'Labour Party':('Ap','#e31836',['social-democracy'],'Labour_Party_(Norway)'),
'Conservative Party':('H','#0065a8',['liberal-conservatism'],'Conservative_Party_(Norway)'),
'Centre Party':('Sp','#00843d',['agrarianism'],'Centre_Party_(Norway)'),
'Progress Party':('FrP','#004f80',['national-conservatism'],'Progress_Party_(Norway)'),
'Liberal Party':('V','#00807b',['social-liberalism'],'Liberal_Party_(Norway)'),
'Socialist Left Party':('SV','#b51b2b',['democratic-socialism'],'Socialist_Left_Party_(Norway)'),
'Red Party':('R','#e5222b',['democratic-socialism'],'Red_Party_(Norway)'),
'Christian Democratic Party':('KrF','#e5b440',['christian-democracy'],'Christian_Democratic_Party_(Norway)'),
'Green Party':('MDG','#65a441',['green-politics'],'Green_Party_(Norway)'),
'Communist Party of Norway':('NKP','#a92328',['communism'],'Communist_Party_of_Norway'),
}
ALIASES={"Farmers' Party":'Centre Party','Bondepartiet (-1959)':'Centre Party','Communist Party':'Communist Party of Norway','Sosialistisk Folkeparti (1961-1969)':"Socialist People's Party",'Socialist Electoral League':'Socialist Electoral League (1973)',"Anders Langes parti (1973)":'Progress Party','The Pensioners\' Party':"Pensioners' Party",'The Welfare and Innovation Party':'Welfare and Innovation Party','Industrial-, commerce & business Party':'Industry and Business Party','Conservative':'Conservative (Konservativt)','Pasientfokus':'Patient Focus','Democratic Party of Norway':'Norway Democrats'}
def num(s):
 s=s.replace(',','').strip();return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def source(l,u):return dict(label=l,url=u)
def profile(n,y):
 n=re.sub(r'\s*\[.*?\]','',n).strip();key=ALIASES.get(n,n)
 if not key or key.lower().startswith(('other','wild','joint-list','independent','all non-partisan')) or 'electoral cooperation' in key:return None
 if y==1882 and key.startswith(('Liberals (','Conservatives (')):key='Liberal movement (pre-1884)' if key.startswith('Liberals') else 'Conservative movement (pre-1884)'
 if key=='Liberal Party' and y<1884:key='Liberal movement (pre-1884)'
 if key=='Conservative Party' and y<1884:key='Conservative movement (pre-1884)'
 short,color,tags,page=INFO.get(key,('',None,[],None));tags=list(tags)
 if key=='Labour Party' and y<1935:tags=[]
 if key=='Conservative Party' and y<1945:tags=['conservatism']
 if key=='Progress Party' and y<2000:tags=[]
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/no/'+key)),country_id='no',name=key,short_name=short,color=color,ideology_ids=['ideology-'+t for t in INFO.get(key,('',None,[],None))[2]],notes='Colours are a display palette. '+('Party history: https://en.wikipedia.org/wiki/'+page if page else 'Historical organisation or electoral list; ideology unassessed. Similar names do not imply organisational continuity.'),archived=False)
 return profiles[key],tags,page

def base(y,body='Storting',suffix=''):
 return dict(id='world-norway-'+('storting' if body=='Storting' else 'constituent-assembly')+'-'+str(y)+('-'+suffix.lower() if suffix else ''),countryId='no',title='Norway '+body+' election'+(' ('+suffix+')' if suffix else '')+' '+str(y),type='parliamentary',body=body,startDate=str(y)+'-01-01',endDate='',precision='year',dateStatus='confirmed',status='held',publication='published',round='',seriesId='NO-'+('storting' if body=='Storting' else 'constituent-assembly'),snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked='2026-10-16',notes='',articleId='',version=1,electionMethod='indirect' if y<=1903 else 'direct')
def row(e,n,v,p,s):
 y=int(e['startDate'][:4]);pr=profile(n,y);r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=re.sub(r'\s*\[.*?\]','',n).strip(),party=n,color=pr[0]['color'] if pr else '#808080',votes=v,share=p,seats=s,previousSeats=None,electoralVotes=None,winner=False,ideologyIds=['ideology-'+t for t in pr[1]] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=y,note='Broad party tradition for this period, not an assessment of an individual candidate.',sources=[source('Party history and tradition','https://en.wikipedia.org/wiki/'+pr[2])])
 e['results'].append(r);return r

def finish(e,votes=None,seats=None,**extra):
 vv=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results']);assert e['results']
 if votes is not None and vv!=votes:extra['publishedAggregateVotes']=votes;e['notes']+=f' The listed vote figures sum to {vv:,}, while the cited source reports an aggregate of {votes:,}. The discrepancy is retained without assigning it to any party.';votes=None
 if seats is not None:assert ss==seats,(e['id'],ss,seats)
 audit.append(dict(id=e['id'],expectedVotes=votes,recordedVotes=vv,expectedSeats=seats,recordedSeats=ss,**extra));records.append(e)
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def dates(e,x):
 p=x['prose'];y=int(e['startDate'][:4])
 # The 1906–1918 two-round system is one election; don't manufacture national round dates.
 if y in [1906,1909,1912,1915,1918]:return
 m=re.search(r'on (\d+) and (\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:
  e['startDate']=f'{y}-{MONTHS[m[3]]:02}-{int(m[1]):02}';e['endDate']=f'{y}-{MONTHS[m[3]]:02}-{int(m[2]):02}';e['precision']='day';return
 m=re.search(r'on (\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:e['startDate']=f'{y}-{MONTHS[m[2]]:02}-{int(m[1]):02}';e['precision']='day'
for x in EX:
 y=int(re.search(r'\d{4}',x['name'])[0])
 if y>=1945:continue
 constituent=y==1814;e=base(y,'Constituent Assembly' if constituent else 'Storting','autumn' if x['name'].startswith('Autumn') else 'Eidsvoll' if constituent else '');dates(e,x);e['sources']=[source('Historical election results and franchise',x['url'])];e['notes']='The franchise, electoral system and parliamentary size changed over time. Before national parties emerged, a non-partisan seat total does not imply a single party or common political programme. Unknown votes and vote shares remain unreported. Colours are a display palette.';e['voteBasis']='Published party/list votes where available; early non-partisan results report representatives only'
 if constituent and x['name'].startswith('February'):
  row(e,'All non-partisan representatives',None,None,112);e['totalSeats']=112;e['sources'].append(source('Storting: the 112-member assembly at Eidsvoll','https://www.stortinget.no/globalassets/pdf/grunnlovsjubileet/brosjyre-engelsk.pdf'));e['notes']+=' Elections were staggered from February; northern elections took place after the Eidsvoll assembly had finished. The table describes its 112 delegates, including 33 military representatives, rather than an invented national party vote.';e['summary']='112 delegates formed the Eidsvoll Constituent Assembly.';finish(e,seats=112);continue
 t=next(t for t in x['tables'] if any('Party' in h and 'Seats' in h for h in t[:4]));hi,h=next((i,h) for i,h in enumerate(t[:4]) if 'Party' in h and 'Seats' in h);ni=max(i for i,v in enumerate(h) if v=='Party');si=h.index('Seats');vi=h.index('Votes') if 'Votes'in h else None;pi=h.index('%') if '%'in h else None;total=None;valid=None
 for r in t[hi+1:]:
  if len(r)<=si:continue
  n=r[ni]
  if n=='Total':total=integer(r[si]);valid=integer(r[vi]) if vi is not None else None;break
  if not n or n.startswith('Source') or n=='Party':continue
  v=integer(r[vi]) if vi is not None else None;p=num(r[pi]) if pi is not None else None;s=integer(r[si])
  if v is None and s is None:continue
  row(e,n,v,p,s)
 for r in t:
  if r and r[0]=='Registered voters/turnout' and pi is not None:e['turnout']=num(r[pi])
 shared=collections.defaultdict(list)
 for r in e['results']:
  if r['votes'] is not None and r['votes']>0:shared[(r['votes'],r['share'])].append(r)
 sharednotes=[]
 for (v,p),rs in shared.items():
  if len(rs)<2:continue
  names=[r['name'] for r in rs]
  for r in rs:r['votes']=None;r['share']=None
  row(e,'Joint-list electoral cooperation: '+' + '.join(names),v,p,None);sharednotes.append(names)
 if sharednotes:e['notes']+=' Shared vote cells spanning multiple organisations are recorded once as joint-list electoral cooperation. Separate party rows retain their seats but do not repeat the shared votes.'
 if y<=1903:e['notes']+=' Representatives were chosen by indirect elections through electors under the franchise then in force.'
 if y in [1906,1909,1912,1915,1918]:e['notes']+=' This contest used a two-round single-member system. The national election is recorded once; first-ballot vote totals are not added to later ballots. Reported seats reflect final mandates. Year precision is used because district polling and runoffs were spread across dates.'
 if y==1882:e['notes']+=' Liberal and conservative movements predate the formal parties founded in 1884 and have separate historical identities.'
 e['totalSeats']=total;e['summary']=str(total)+' representatives returned to '+e['body']+'.';finish(e,votes=valid,seats=total,sourceSha256=x['sha256'],sharedVoteGroups=sharednotes)

# The three national StatBank tables share party codes. Joint-list ballots are disjoint categories.
def get(d,**kw):
 i=0
 for k,size in zip(d['id'],d['size']):i=i*size+d['dimension'][k]['category']['index'][kw.get(k,next(iter(d['dimension'][k]['category']['index'])))]
 return d['value'][i] if isinstance(d['value'],list) else d['value'].get(str(i))
v=json.loads((C/'ssb-08092.json').read_text());s=json.loads((C/'ssb-08219.json').read_text());t=json.loads((C/'ssb-08243.json').read_text());codes=v['dimension']['PolitParti']['category']['label'];years=list(v['dimension']['Tid']['category']['index'])
JOINT={'90a':'Liberal Party','90b':"Farmers' Party",'90c':'Christian Democratic Party','90d':'Conservative Party','90e':'Centre Party','90f':'Communist Party / Socialist People’s Party','90g':'New People’s Party','90h':'Non-socialist joint lists'}
for y in years:
 e=base(int(y));x=next(x for x in EX if x['name']==y+'_Norwegian_parliamentary_election');dates(e,x);e['sources']=[source('Statistics Norway: national valid votes and party/list percentages','https://www.ssb.no/en/statbank/table/08092/'),source('Statistics Norway: elected representatives by sex and party/list','https://www.ssb.no/en/statbank/table/08219/'),source('Statistics Norway: electoral turnout','https://www.ssb.no/en/statbank/table/08243/'),source('Election date and historical context',x['url'])]
 primary_rows=[]
 for p,n in codes.items():
  votes=get(v,PolitParti=p,ContentsCode='Godkjente1',Tid=y);share=get(v,PolitParti=p,ContentsCode='GodkjenteProsent',Tid=y);sexes=[get(s,PolitParti=p,Kjonn=k,Tid=y) for k in ['1','2']];seats=None if all(x is None for x in sexes) else sum(x or 0 for x in sexes)
  if not votes and not seats:continue
  if p.startswith('90'):n='Joint-list allocation — '+JOINT.get(p,n)
  row(e,n,votes,share,seats);primary_rows.append(dict(partyCode=p,name=n,votes=votes,seats=seats,publishedShare=share))
 valid=sum(r['votes'] or 0 for r in e['results'])
 for r in e['results']:
  if r['votes'] is not None:r['share']=round(r['votes']/valid*100,2)
 e['results'].sort(key=lambda r:-(r['votes'] or 0));e['turnout']=get(t,Tid=y);e['totalSeats']=sum(r['seats'] or 0 for r in e['results']);e['summary']=str(e['totalSeats'])+' representatives elected to the Storting.';e['voteBasis']='Statistics Norway valid party/list votes, excluding blank and rejected ballots';e['notes']='Official Statistics Norway national categories. Vote shares are calculated from the exact national valid-vote total and rounded to two decimal places; the source percentage series is rounded more coarsely. Joint-list allocations, where present, are displayed separately from ordinary party-list votes; these categories must not be added to a joint-list aggregate a second time. Elected representatives are attributed to the party categories used by Statistics Norway, including members elected on joint lists. Male and female representatives are summed once; deputy representatives are not added. Blank and rejected ballots are excluded from party shares. Colours are a display palette.';finish(e,votes=sum(r['votes'] or 0 for r in e['results']),seats=e['totalSeats'],primaryTables=['08092','08219','08243'],primaryRows=primary_rows)
# Seat comparisons follow the same saved organisation, never a shared electoral-list vote row.
previous={}
for e in sorted([e for e in records if e['body']=='Storting'],key=lambda e:e['startDate']):
 for r in e['results']:
  if r.get('partyId') in previous:r['previousSeats']=previous[r['partyId']]
 previous={r['partyId']:r['seats'] for r in e['results'] if r.get('partyId') and r['seats'] is not None}
records.sort(key=lambda e:(e['startDate'],e['id']))
for e in records:
 for i,r in enumerate(e['results'],1):r['id']=e['id']+'-r'+str(i)
used={r['partyId'] for e in records for r in e['results'] if r.get('partyId')};profiles={k:p for k,p in profiles.items() if p['id'] in used}
for n,d in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (P/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for n in ['08092','08219','08243']:(P/('ssb-'+n+'.json')).write_bytes((C/('ssb-'+n+'.json')).read_bytes())
print(len(records),'elections;',sum(len(e['results']) for e in records),'rows;',len(profiles),'parties')
