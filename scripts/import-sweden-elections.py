"""Build sourced Swedish national elections; never infer missing ballots or party identities."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys,datetime
P=Path(__file__).resolve().parent/'sweden-election-import';EX=json.loads((P/'source-extract.json').read_text());records=[];profiles={};audit=[];omissions=[]
INFO={
'Social Democrats':('S','#e8112d',['social-democracy'],'Swedish_Social_Democratic_Party'),
'Moderate Party':('M','#52bdec',['liberal-conservatism'],'Moderate_Party'),
'Centre Party':('C','#009933',['liberalism'],'Centre_Party_(Sweden)'),
'Liberals':('L','#006ab3',['liberalism'],'Liberals_(Sweden)'),
'Left Party':('V','#da291c',['democratic-socialism'],'Left_Party_(Sweden)'),
'Christian Democrats':('KD','#000077',['christian-democracy'],'Christian_Democrats_(Sweden)'),
'Green Party':('MP','#83cf39',['green-politics'],'Green_Party_(Sweden)'),
'Sweden Democrats':('SD','#dddd00',['national-conservatism'],'Sweden_Democrats'),
}
ALIASES={
'Swedish Social Democratic Party':'Social Democrats','Sveriges socialdemokratiska arbetareparti':'Social Democrats','Socialdemokraterna':'Social Democrats',
'General Electoral League':'Moderate Party','Allmänna valmansförbundet':'Moderate Party','Right Party':'Moderate Party','Högerpartiet':'Moderate Party','Moderata samlingspartiet':'Moderate Party','Högerns riksorganisation':'Moderate Party',
"Farmers’ League":'Centre Party',"Farmers\' League":'Centre Party','Bondeförbundet':'Centre Party','Centerpartiet':'Centre Party',
"People's Party":'Liberals','Folkpartiet':'Liberals',
'Communist Party':'Left Party','Left Party Communists':'Left Party','Vänsterpartiet kommunisterna':'Left Party','Sveriges kommunistiska parti':'Left Party','Sveriges kommunistiska parti (Sillénare)':'Left Party',
'Christian Democratic Unity':'Christian Democrats',
'Frisinnade landsföreningen':'Free-minded National Association','Frisinnade folkpartiet':'Free-minded National Association',
'Sveriges liberala parti':'Liberal Party of Sweden (1923–1934)',
'Lantmannapartiet':'Lantmanna Party','Ministeriella partiet':'Ministerial Party','Nyliberala partiet':'New Liberal Party','Nya centern':'New Centre','Center-högern':'Centre Right',
'Protektionistiska partiet':'Protectionist Party','Minoritetspartiet':'Minority Party','Första kammarens moderata parti':'First Chamber Moderate Party','Det förenade högerpartiet':'United Right Party',
'Partilösa':'Independents','Obundna':'Independents','Övriga':'Other parties',
}
def num(s):
 s=re.sub(r'[\s,\u00a0]','',s);return float(s.rstrip('%')) if re.fullmatch(r'\d+(?:\.\d+)?%?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def source(label,url):return dict(label=label,url=url)
def party(n,y):
 n=re.sub(r'\s*\[\s*sv\s*\]','',n).strip();n=re.sub(r'\s+\([A-Za-z]{1,4}\)$','',n);key=ALIASES.get(n,n)
 if n=='Centre Party' and y<1957:key='Centre Party (1873–1882)' if y<1900 else 'Centre Party (1932 electoral group)'
 if n=='Liberals' and y<1900:key='Liberal electoral group (pre-1900)'
 if n in ['Liberal Party', 'Frisinnade landsföreningen'] and 1923<=y<=1933:key='Liberal Party of Sweden (1923–1934)' if n=='Liberal Party' else 'Free-minded National Association'
 if n in ['Liberal People’s Party',"Liberal People's Party"]:key='Liberals'
 if n in ['Christian Democratic Society Party']:key='Christian Democrats'
 if n in ['National Organisation of the Right','National Organization of the Right','Rightist Party']:key='Moderate Party'
 if n in ['Landsbygdspartiet Bondeförbundet']:key='Centre Party'
 if n=='Communist Party' and y>=1967:key='Communist Party of Sweden (1967–1987)'
 if n=='Communist Party (Sillénare)':key='Left Party'
 if n=='Communist Party (Kilbommare)':key='Sveriges kommunistiska parti (Kilbomare)'
 if n=='Sveriges kommunistiska parti (Silénare)':key='Left Party'
 if n in ['Social Democratic Left Party of Sweden','Sverges socialdemokratiska vänsterparti']:key='Social Democratic Left Party (1921–1923)'
 if n in ['Jordbrukarnas riksförbund',"National Farmers' Association"]:key='National Farmers’ Association'
 if n in ['Vänstervilde','Högervilde']:return None
 if not key or key in ['Independents','Other parties','Write-in votes','Parties not on the ballot','Free traders','Protectionists','Frihandlare','Protektionister'] or 'other parties' in key.lower() or key.lower().startswith(('other parties','other participating')):return None
 # Similar labels from splits are separate organisations; the 1917 left joined a separate majority in 1921.
 if key=='Liberal–Social Democratic electoral cooperation':return None
 if key in ['Social Democratic Left Party','Sveriges socialdemokratiska vänsterparti']:key='Social Democratic Left Party (1917–1921)' if y<=1920 else 'Social Democratic Left Party (1921–1923)'
 if key=='Communist Party of Sweden':key='Communist Party of Sweden (1995–)'
 if key=='Centern (Centre–KDS joint list)':return None
 if key=='Left Party' and y<1967:tags=[]
 else:tags=INFO.get(key,('',None,[],None))[2]
 short,color,_,page=INFO.get(key,('',None,[],None))
 if key=='Centre Party' and y<1957:tags=['agrarianism']
 if key=='Left Party' and y<1990:tags=[]
 if key=='Sweden Democrats' and y<2000:tags=[]
 if key=='Moderate Party' and y<1969:tags=['conservatism']
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/se/'+key)),country_id='se',name=key,short_name=short,color=color,ideology_ids=['ideology-'+t for t in INFO.get(key,('',None,[],None))[2]],notes='Colours are a display palette. '+('Party history: https://en.wikipedia.org/wiki/'+page if page else 'Historical organisation or electoral list; ideology unassessed.'),archived=False)
 return profiles[key],tags,page

def base(y,body,date=None,precision='year',suffix=''):
 date=date or str(y)+'-01-01';slug={'Riksdag':'riksdag','Andra kammaren':'andra-kammaren','Första kammaren':'forsta-kammaren'}[body]
 return dict(id='world-sweden-'+slug+'-'+date+('-'+suffix if suffix else ''),countryId='se',title='Sweden '+body+' election'+(' ('+suffix+')' if suffix else '')+' '+str(y),type='parliamentary',body=body,startDate=date,endDate='',precision=precision,dateStatus='confirmed',status='held',publication='published',round='',seriesId='SE-'+('riksdag-lower' if body!='Första kammaren' else 'forsta-kammaren'),snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked='2026-10-16',notes='',articleId='',version=1,electionMethod='indirect' if body=='Första kammaren' else 'direct')
def row(e,n,v,p,s):
 y=int(e['startDate'][:4]);pr=party(n,y);n=re.sub(r'\s*\[\s*sv\s*\]','',n).strip();n=re.sub(r'\s+\([A-Za-z]{1,4}\)$','',n)
 r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=n,party=n,color=pr[0]['color'] if pr else '#808080',votes=v,share=p,seats=s,previousSeats=None,electoralVotes=None,winner=False,ideologyIds=['ideology-'+t for t in pr[1]] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=y,note='Broad party tradition for this era, not an individual-candidate assessment.',sources=[source('Party history and tradition','https://en.wikipedia.org/wiki/'+pr[2])])
 e['results'].append(r);return r

def finish(e,x,total=None,votes=None,**extra):
 ss=sum(r['seats'] or 0 for r in e['results']);vv=sum(r['votes'] or 0 for r in e['results']);assert e['results'],x['name']
 if total is not None:assert ss==total,(x['name'],'seats',ss,total)
 if votes is not None and vv!=votes:
  e['notes']+=f' The published party figures sum to {vv:,} votes, while the aggregate is {votes:,}. This source discrepancy is retained without assigning the difference to a party.';extra['unreconciledPublishedVotes']=votes;votes=None
 audit.append(dict(id=e['id'],source=x['url'],sha256=x['sha256'],expectedSeats=total,recordedSeats=ss,expectedVotes=votes,recordedVotes=vv,**extra));records.append(e)

MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
def lowerdate(x,y):
 p=x['prose'];suffix='';end=''
 if '1887' in x['name']:return str(y)+('-03-01' if x['name'].startswith('March') else '-08-01'),'month',('spring' if x['name'].startswith('March') else 'autumn'),''
 if x['name'].startswith('March_1914'):return '1914-03-27','day','spring','1914-04-07'
 if x['name'].startswith('September_1914'):return '1914-09-05','day','autumn','1914-09-13'
 m=re.search(r'(?:between|on) (\d+) and (\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:return f'{y}-{MONTHS[m[3]]:02}-{int(m[1]):02}','day','',f'{y}-{MONTHS[m[3]]:02}-{int(m[2]):02}'
 m=re.search(r'(?:on |on the )(\d+) ([A-Z][a-z]+) '+str(y),p)
 if m:return f'{y}-{MONTHS[m[2]]:02}-{int(m[1]):02}','day','',''
 m=re.search(r'in (September) '+str(y),p)
 if m:return f'{y}-09-01','month','',''
 return str(y)+'-01-01','year','',''

for x in EX:
 if 'general_election' not in x['name'] or x['name'].startswith(('1869','1884','2026')):continue
 y=int(re.search(r'\d{4}',x['name'])[0]);date,prec,suff,end=lowerdate(x,y);e=base(y,'Riksdag' if y>=1970 else 'Andra kammaren',date,prec,suff);e['endDate']=end;e['sources']=[source('Historical election result table',x['url'])]
 t=next(t for t in x['tables'] if any('Party' in h and 'Seats' in h for h in t[:3]));hi,h=next((i,h) for i,h in enumerate(t[:3]) if 'Party' in h and 'Seats' in h);ni=max(i for i,v in enumerate(h) if v=='Party');si=h.index('Seats');vi=h.index('Votes') if 'Votes' in h else None;pi=h.index('%') if '%' in h else None;total=None;valid=None
 for r in t[hi+1:]:
  if len(r)<=si:continue
  n=r[ni]
  if n=='Total':total=integer(r[si]);valid=integer(r[vi]) if vi is not None else None;break
  if not n or n in ['By party','Party'] or n.startswith('Source'):continue
  s=integer(r[si]);v=integer(r[vi]) if vi is not None else None;p=num(r[pi]) if pi is not None else None
  if s is None and v is None:continue
  row(e,n,v,p,s)
 for r in t:
  if len(r)>3 and r[0].startswith('Registered voters/turnout'):e['turnout']=num(r[pi]) if pi is not None else None
 if y==1887:
  sv=next(x for x in EX if x['name']=='Andrakammarvalet_i_Sverige_1887_'+('(vår)' if suff=='spring' else '(september)'));e['results']=[];st=sv['tables'][0]
  for sr in st[2:]:
   if sr[1].startswith('Antal giltiga'):total=integer(sr[4]);valid=integer(sr[2]);break
   n=re.sub(r'\s*\[.*?\]','',sr[1]);seat=integer(sr[4]);vote=integer(sr[2]);share=float(sr[3].replace(',','.')) if num(sr[3]) is not None else None
   row(e,n,vote,share,seat)
  e['sources']=[source('Swedish historical result table, citing Statistics Sweden',sv['url'])]
 if y==1985:
  e['results']=[r for r in e['results'] if r['name'] not in ['Centre Party','Christian Democratic Unity','Centre ( CDU – C )']]
  row(e,'Centern (Centre–KDS joint list)',691258,round(691258/5567022*100,2),44)
  row(e,'Christian Democratic Unity',5000,round(5000/5567022*100,2),0)
 if y in [1893,1896,1899]:
  joint=next(r for r in e['results'] if r['name']=='Liberals');v,p=joint['votes'],joint['share'];
  for r in e['results']:
   if r['name'] in ['Liberals','Swedish Social Democratic Party']:r['votes']=None;r['share']=None
  row(e,'Liberal–Social Democratic electoral cooperation',v,p,None)
 e['totalSeats']=total;e['summary']=str(total)+' seats returned to '+e['body']+'.';e['voteBasis']='Published national party or electoral-list votes; historical affiliations as classified by the source'
 e['notes']='The franchise, electoral system and party organisations changed over time. Historical votes are not comparable to universal-suffrage elections. Unknown figures remain unreported. Colours are a display palette.'
 if y==1985:
  e['notes']+=' The Centre Party and KDS contested under the joint Centern label: 691,258 votes and 44 seats, including one KDS member. A further 5,000 votes were cast under KDS’s own label and won no seats. Component ballots within Centern are not counted again.'
  e['sources'].append(source('Statistics Sweden: 1985 national summary and joint-list breakdown, pp. 8 and 12','https://share.scb.se/ov9993/data/historisk%20statistik/SOS%201911-%2FValstatistiken%2FAllm%C3%A4nna%20valen%20(SOS)%201970-1998%2FValstatistik-Allmanna-valen-1985-Del-1-Riksdagsvalet.pdf'))
 if y in [1917,1920]:e['notes']+=' The National Farmers’ Association and Farmers’ League are shown separately; SCB’s long-run summary groups them under the Centre-party lineage.'
 if y in [1924,1932,1936,1940]:e['notes']+=' Left-wing splits are listed separately. SCB’s long-run historical summary combines some communist and socialist organisations that are separate in this table.'
 if y==1944:e['notes']+=' The detailed historical table reports a 46.55% Social Democratic share; SCB’s long-run summary gives 46.7%. The detailed figure is retained.'
 if y in [1893,1896,1899]:e['notes']+=' The source repeats a shared Liberal–Social Democratic vote figure. It is counted once in a joint electoral-cooperation row; separate party rows retain seats only.'
 if y<1911:e['notes']+=' Early elections could combine direct voting and indirect selection through electors; the figures retain the source’s classification.'
 if y==1887:e['notes']+=' The Swedish source classifies historical tariff alignments and subsequent parliamentary groups. These differ from classifications used in some international handbooks. The autumn seat totals reflect the settlement after Stockholm’s list disqualification; later party-group labels are retrospective.'
 
 finish(e,sv if y==1887 else x,total,valid)
# Swedish-language tables retain the two early lower-house results missing from English pages.
for y in [1869,1884]:
 x=next(x for x in EX if x['name']=='Andrakammarvalet_i_Sverige_'+str(y));e=base(y,'Andra kammaren');e['sources']=[source('Historical Second Chamber results',x['url'])];t=x['tables'][0]
 if y==1869:
  for r in t[1:]:
   if r[1]=='Totalt':break
   row(e,r[1],None,None,integer(r[-1]))
  e['totalSeats']=192
 else:
  for r in t[2:]:
   if r[1].startswith(('Antal','Ogiltiga','Totalt')):break
   if integer(r[-2]) is None:continue
   row(e,r[1],None,None,integer(r[-2]))
  e['totalSeats']=214;e['turnout']=25.2
 e['summary']=str(e['totalSeats'])+' seats returned to Andra kammaren.';e['voteBasis']='Party-group seat totals; popular votes not reported on a comparable national basis';e['notes']='These elections combined direct voting with indirect selection through electors under a restricted male franchise. Direct votes and electoral-college ballots are not combined into a national party popular vote. Historical parliamentary groups are not necessarily modern membership parties. Colours are a display palette.';finish(e,x,e['totalSeats'])
# First Chamber: import only the seats selected in each election, never the entire post-election chamber for a rotating renewal.
for x in EX:
 if not x['name'].startswith('Förstakammarvalet'):continue
 y=int(re.search(r'\d{4}',x['name'])[0])
 if not x['tables']:
  omissions.append(dict(source=x['url'],year=y,reason='No verified national party-result breakdown; early entries may be by-elections. No empty election record created.'));continue
 t=next((t for t in x['tables'] if t and 'Parti' in t[0]),None)
 if t is None:continue
 suffix='';month=9
 if '(november)' in x['name']:suffix='november';month=11
 if '(september)' in x['name']:suffix='september'
 if '(juni–juli)' in x['name']:suffix='june-july';month=6
 prec='month' if y>=1909 else 'year';e=base(y,'Första kammaren',f'{y}-{month if prec=="month" else 1:02}-01',prec,suffix);e['sources']=[source('First Chamber election results and scope',x['url'])]
 h=t[0];h2=t[1];ni=max(i for i,v in enumerate(h) if v=='Parti');vi=None;previous=None;full=None
 if 'Efter' in h2:si=h2.index('Efter');previous=h2.index('Innan');full=len(h)-1
 elif 'Valda' in h:si=h.index('Valda');full=5
 else:si=next(i for i,v in enumerate(h) if v in ['Mandatfördelning','Mandat']);vi=next(i for i,v in enumerate(h) if v=='Röster')
 total=None;valid=None;fulltotal=None
 for r in t[2:]:
  if len(r)<=si:continue
  n=r[ni]
  if n in ['Totalt','Antal giltiga röster']:
   total=integer(r[si]);valid=integer(r[vi]) if vi is not None else None;fulltotal=integer(r[full]) if full is not None else None;break
  if not n:continue
  r0=row(e,n,integer(r[vi]) if vi is not None else None,None,integer(r[si]))
  # A previous rotating cohort is comparable only where the source explicitly supplies it.
  if previous is not None:r0['previousSeats']=integer(r[previous])
 votes=sum(r['votes'] or 0 for r in e['results'])
 if valid is not None and votes==valid and valid:
  for r in e['results']:
   if r['votes'] is not None:r['share']=round(r['votes']/valid*100,2)
 else:
  for r in e['results']:r['votes']=None
  valid=None
 e['totalSeats']=fulltotal or (150 if y>=1909 else None);e['summary']=str(total)+' seats selected in this First Chamber election.';e['voteBasis']='Electoral-college ballots where separately reported and reconcilable; seats are this election’s selected cohort'
 e['notes']='The First Chamber was elected indirectly by county councils and specified city councils or electors. Recorded votes, where available, are electoral-college ballots, not a national popular vote. Vote shares are calculated from the published valid electoral-college total. Turnout among the general electorate is not applicable. The table counts only the mandates selected in this election; continuing senators are excluded. Previous seats, where shown, refer to the corresponding outgoing cohort, not the full chamber. Colours are a display palette.'
 if valid is None:e['notes']+=' No comparable party ballot totals are reported here; council membership or historical multi-vote tallies are not substituted for votes cast.'
 if y==1921:e['notes']+=' The secondary source repeats a shared vote figure across left-wing organisations, so those non-additive party votes are omitted.'
 if suffix=='june-july':e['notes']+=' The election extended across June and July; month precision is used.'
 if y in [1911,1919,1921] and (suffix in ['november','june-july'] or y==1921):e['snap']=True
 finish(e,x,total,valid,fullChamberSeats=fulltotal)
# Preserve the existing 2026 record identity and official figures, improve metadata and link previous results.
e=json.loads((P/'pre-import-backup.json').read_text())[0]['data'];assert e['id']=='world-sweden-2026';e=json.loads(json.dumps(e));e.update(title='Sweden Riksdag election 2026',seriesId='SE-riksdag-lower',summary='349 seats returned to the Riksdag.',checked='2026-10-16',electionMethod='direct')
for r in e['results']:
 r['previousSeats']=None;n=r['name'].removeprefix('The ').removesuffix(' Party');mapping={'Social Democratic':'Social Democrats','Moderate':'Moderate Party','Sweden Democrats':'Sweden Democrats','Left':'Left Party','Centre':'Centre Party','Christian Democrats':'Christian Democrats','Green':'Green Party','Liberal':'Liberals'}
 key=mapping.get(n);pr=party(key,2026) if key else None
 if pr:r['partyId']=pr[0]['id'];r['party']=key;r['ideologyIds']=['ideology-'+t for t in pr[1]];r['ideologyBasis']=dict(kind='party-era',year=2026,note='Broad party tradition.',sources=[source('Party history','https://en.wikipedia.org/wiki/'+pr[2])])
records.append(e)
scb='https://www.scb.se/hitta-statistik/statistik-efter-amne/demokrati/allmanna-val/allmanna-val-valresultat/pong/tabell-och-diagram/historisk-valstatistik/historisk-statistik-over-valaren-19102022.-procentuell-fordelning-av-giltiga-valsedlar-efter-parti-och-typ-av-val'
for e in records:
 y=int(e['startDate'][:4])
 if e['body']!='Första kammaren' and 1911<=y<=2022:e['sources'].append(source('Statistics Sweden: national historical turnout and party-share series',scb))
 if e['body']=='Första kammaren' and 1965<=y<=1969:e['sources'].append(source('Statistics Sweden: First Chamber elections 1965–1969, tables 2.1–2.2','https://share.scb.se/ov9993/data/historisk%20statistik/SOS%201911-%2FValstatistiken%2FRiksdagsmannavalen%20(SOS)%201909-1968%2FValstatistik-Riksdagsmannavalen-1965-1968-2.pdf'))
 if y==1921:e['sources'].append(source('Statistics Sweden: Riksdagsmannavalen 1921','https://share.scb.se/ov9993/data/historisk%20statistik/SOS%201911-%2FValstatistiken%2FRiksdagsmannavalen%20(SOS)%201909-1968%2FValstatistik-Riksdagsmannavalen-1921.pdf'))
# Adjacent complete lower-house elections; labels from splits and coalition lists do not imply continuity.
previous={}
for e in sorted([r for r in records if r['body']!='Första kammaren'],key=lambda r:r['startDate']):
 for r in e['results']:
  if r.get('partyId') in previous:r['previousSeats']=previous[r['partyId']]
 previous={r['partyId']:r['seats'] for r in e['results'] if r.get('partyId') and r['seats'] is not None}
for e in records:
 if e['id']!='world-sweden-2026':
  for i,r in enumerate(e['results'],1):r['id']=e['id']+'-r'+str(i)
used={r['partyId'] for e in records for r in e['results'] if r.get('partyId')};profiles={k:p for k,p in profiles.items() if p['id'] in used}
records.sort(key=lambda e:(e['startDate'],e['id']))
for name,data in [('records',records),('parties',list(profiles.values())),('reconciliation',audit),('research-gaps',omissions)]:
 (P/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(len(records),'records;',sum(len(e['results']) for e in records),'rows;',len(profiles),'parties;',len(omissions),'unimported early upper-house entries')
