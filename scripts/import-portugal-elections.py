"""Reproducible national result transcription. Never substitutes missing counts with zero."""
from pathlib import Path
import json,re,datetime,uuid,hashlib,colorsys,copy
P=Path(__file__).resolve().parent/'portugal-election-import'
EX=json.loads((P/'source-extract.json').read_text());records=[];profiles={};audit=[]
INFO={
 'Democratic Alliance':('AD','#e87828',['liberal-conservatism','christian-democracy'],'Democratic_Alliance_(Portugal)'),
 'AD – PSD/CDS Coalition':('AD','#e87828',['liberal-conservatism','christian-democracy'],'Democratic_Alliance_(Portugal,_2024)'),
 'Coalition PSD/CDS/PPM':('PSD/CDS/PPM','#e87828',['liberal-conservatism','christian-democracy'],'Democratic_Alliance_(Portugal,_2024)'),
 'Madeira First':('MP','#e87828',['liberal-conservatism','christian-democracy'],'Madeira_First'),
 'Portugal Ahead':('PàF','#e87828',['liberal-conservatism','christian-democracy'],'Portugal_Ahead'),
 'Socialist Party':('PS','#e23948',['social-democracy'],'Socialist_Party_(Portugal)'),
 'Social Democratic Party':('PSD','#e87828',['liberal-conservatism'],'Social_Democratic_Party_(Portugal)'),
 'Chega':('CH','#202a59',['right-wing-populism','national-conservatism'],'Chega_(political_party)'),
 'Liberal Initiative':('IL','#00a6d6',['economic-liberalism'],'Liberal_Initiative'),
 'LIVRE':('L','#80b242',['progressivism','ecologism'],'LIVRE'),
 'Left Bloc':('BE','#a52d71',['democratic-socialism'],'Left_Bloc_(Portugal)'),
 'People Animals Nature':('PAN','#218c83',['green-politics'],'People_Animals_Nature'),
 'Unitary Democratic Coalition':('CDU','#bd2525',['communism','green-politics'],'Unitary_Democratic_Coalition'),
 'Portuguese Communist Party':('PCP','#bd2525',['communism'],'Portuguese_Communist_Party'),
 'Together for the People':('JPP','#db9a19',['regionalism'],'Together_for_the_People'),
 'Democratic and Social Centre':('CDS','#1672a3',['christian-democracy'],'CDS_%E2%80%93_People%27s_Party'),
}
ALIASES={'Democratic Social Center':'Democratic and Social Centre',"CDS – People's Party":'Democratic and Social Centre','Democratic and Social Centre – People\'s Party':'Democratic and Social Centre','People\'s Democratic Party':'Social Democratic Party','Catholic Centre Party':'Portuguese Catholic Centre'}
def num(s):
 s=s.replace(',','').replace('−','-').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def src(label,url):return dict(label=label,url=url)
def profile(n,y):
 n=ALIASES.get(n,n)
 if not n or n in ['Independent','Independents','Opposition','Other parties and independents'] or ' and others' in n:return None
 key=n+(' (1979–1983)' if n=='Democratic Alliance' and y<1990 else ' (2024–)' if n=='Democratic Alliance' else '')
 short,color,tags,page=INFO.get(n,('',None,[],None))
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/pt/'+key)),country_id='pt',name=key,short_name=short,color=color,ideology_ids=['ideology-'+x for x in tags],notes='Colours are a display palette. '+('Broad party tradition: https://en.wikipedia.org/wiki/'+page if page else 'Historical ballot organisation; ideology unassessed. Similarly named organisations are not assumed to be continuous.'),archived=False)
 return profiles[key],page
def base(date,body,precision='day',round=''):
 slug={'Assembly of the Republic':'assembly','Constituent Assembly':'constituent-assembly','Constituent Cortes':'constituent-cortes',"People's Estate":'peoples-estate','Chamber of Deputies':'deputies','National Assembly':'national-assembly','Senate':'senate','Chamber of Peers':'peers','President':'president'}[body]
 return dict(id='world-portugal-'+slug+'-'+date+('-round-'+round if round else ''),countryId='pt',title='Portugal '+('presidential' if body=='President' else body)+' election '+date[:4]+(' — round '+round if round else ''),type='presidential' if body=='President' else 'parliamentary',body=body,startDate=date,endDate='',precision=precision,dateStatus='confirmed',status='held',publication='published',round=round,seriesId='PT-'+slug,snap=False,summary='',government='',turnout=None,totalSeats=1 if body=='President' else None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked='2026-10-16',notes='',articleId='',version=1,electionMethod='direct')
def result(e,n,party,v,p,s):
 y=int(e['startDate'][:4]);pr=profile(party,y);r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=n,party=party,color=pr[0]['color'] if pr else '#808080',votes=v,share=p,seats=s,previousSeats=None,electoralVotes=None,winner=False,ideologyIds=pr[0]['ideology_ids'] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=y,note='Broad party tradition; no personal candidate ideology is inferred.',sources=[src('Party history and political tradition','https://en.wikipedia.org/wiki/'+pr[1])])
 e['results'].append(r);return r
def dates(x):
 y=re.search(r'\d{4}',x['name'])[0];text=x['infobox'] or x['prose'][:500]
 if y=='1828':return '1828-05-01','','month'
 if x['name']=='1822_Portuguese_legislative_election':return '1822-08-18','','day'
 if x['name']=='1905_Portuguese_legislative_election':return '1905-02-12','','day'
 # The first year in an infobox title is followed by the previous election link; match a full date.
 m=re.search(r'(\d{1,2})(?: and |–| to )(\d{1,2}) ([A-Z][a-z]+) '+y,text)
 if m:
  a=datetime.datetime.strptime(f'{m[1]} {m[3]} {y}','%d %B %Y').strftime('%Y-%m-%d');b=datetime.datetime.strptime(f'{m[2]} {m[3]} {y}','%d %B %Y').strftime('%Y-%m-%d');return a,b,'day'
 m=re.search(r'(\d{1,2} [A-Z][a-z]+) and (\d{1,2} [A-Z][a-z]+) '+y,text)
 if m:return *(datetime.datetime.strptime(v+' '+y,'%d %B %Y').strftime('%Y-%m-%d') for v in m.groups()),'day'
 mm=list(re.finditer(r'\d{1,2} [A-Z][a-z]+ '+y,text))
 if mm:
  ds=[datetime.datetime.strptime(m[0],'%d %B %Y').strftime('%Y-%m-%d') for m in mm[:2]];return ds[0],ds[1] if len(ds)>1 and 'round' in text[mm[0].end():mm[1].end()+30] else '', 'day'
 m=re.search(r'([A-Z][a-z]+) '+y,text)
 if m:return datetime.datetime.strptime(m[0],'%B %Y').strftime('%Y-%m-01'),'','month'
 return y+'-01-01','','year'
def parse(x,t,body,ri=0):
 date,end,precision=dates(x);e=base(date,body,precision,str(ri+1) if ri or any('Second round' in r for r in t) else '')
 if body!='President':e['endDate']=end
 y=int(date[:4]);hi,h=next((i,r) for i,r in enumerate(t) if ('Party' in r or 'Party or alliance' in r or 'Candidate' in r) and ('Votes' in r or 'Seats' in r))
 vi=h.index('Votes')+ri*2 if 'Votes' in h else None;pi=h.index('%')+ri*2 if '%' in h else None;si=h.index('Seats') if 'Seats' in h else None
 if body=='President' and ri:
  matches=re.findall(r'\d{1,2} [A-Z][a-z]+ '+str(y),x['infobox']);e['startDate']=datetime.datetime.strptime(matches[1],'%d %B %Y').strftime('%Y-%m-%d');e['id']=e['id'].replace(date,e['startDate'])
 if y==1913 and body=='Chamber of Deputies':hi+=1;h=t[hi];si=h.index('Won');e['notes']='Partial renewal: 37 mandates were contested in a chamber of 153; seats show mandates won in this ballot. '
 meta={};raw=[]
 for r in t[hi+1:]:
  if len(r)<=max(i for i in [vi,pi,si,1] if i is not None):continue
  n=r[1] if r[0]=='' or r[0] in ['Party','Party or alliance','Candidate'] else r[0]
  if not n or n.startswith('Source:') or n in ['Party','Seats','Candidate']:continue
  if n in ['Total','Valid votes','Invalid/blank votes','Invalid votes','Blank votes','Total votes','Registered voters/turnout']:
   meta[n]=dict(votes=integer(r[vi]) if vi is not None else None,share=num(r[pi]) if pi is not None else None,seats=integer(r[si]) if si is not None else None);continue
  if len(r)>3 and r[2]=='Total':continue # grouped subtotal, not another ballot list
  if body!='President' and h.count('Party or alliance')==4:n=r[3]
  if x['name']=='1892_Portuguese_legislative_election':
   if n=='Other parties and independents':continue
   if n=='Regenerator Party':n='Regenerator Party and others'
  if y==1919 and body=='Senate':
   if n=='Republican Union':continue
   if n=='Evolutionist Party':n='Evolutionist Party / Republican Union'
  party=r[2] if body=='President' and h.count('Candidate')==2 else '' if body=='President' else n
  if body=='President' and not party:party='National Union' if y>=1935 else 'Independent'
  v=integer(r[vi]) if vi is not None else None;p=num(r[pi]) if pi is not None else None;s=integer(r[si]) if si is not None else None
  if 'withdrew' in n:continue
  if v is None and p is None and s is None:continue
  raw.append((n,v,p,s));result(e,n,party,v,p,s)
 total=meta.get('Total',{});ss=sum(r['seats'] or 0 for r in e['results']);vv=sum(r['votes'] or 0 for r in e['results']);expected=total.get('seats')
 if expected is not None:assert ss==expected,(x['name'],body,ss,expected)
 if total.get('votes') is not None:assert vv==total['votes'],(x['name'],body,vv,total['votes'])
 e['totalSeats']=total.get('seats') if body!='President' else 1
 if not e['totalSeats'] and body!='President':
  m=re.search(r'All ([\d,]+) seats',x['infobox']);e['totalSeats']=int(m[1].replace(',','')) if m else None
 e['turnout']=meta.get('Registered voters/turnout',{}).get('share')
 e['sources']=[src('Election results and historical references',x['url'])]
 if y>=1975:e['sources'].append(src('National Electoral Commission: official result archive','https://www.cne.pt/content/eleicoes-referendos-resultados-oficiais'))
 e['notes']+='National ballot-list results. Joint lists are retained separately from parties standing independently; subtotal rows are excluded. Colours are a display palette. Unreported votes, turnout and seats remain blank. '
 if body=='President':
  e['voteBasis']='Candidate votes; published vote shares use valid candidate ballots' if y>=1976 else 'Reported candidate ballots; historical percentage denominator follows the cited table'
  if e['results'] and (not e['round'] or ri==1):max(e['results'],key=lambda r:r['votes'] or r['share'] or 0)['winner']=True
  elif e['round']=='1':
   for r in sorted(e['results'],key=lambda r:r['votes'] or 0,reverse=True)[:2]:r['advanced']=True
 else:e['voteBasis']='Published national ballot-list vote shares; the denominator can include blank and invalid ballots'
 if y<1974:
  e['notes']+='Historical electoral franchises were restricted and changed over time. '
  if y>=1928:e['notes']+='Held under military dictatorship / Estado Novo; official reported results do not establish a free or competitive election. Opposition withdrawals and restrictions affect comparability. '
  if body!='President' and 'indirect' in x['prose'][:1800]:e['electionMethod']='indirect'
 if y==1919 and body=='Senate':e['notes']+='The 27 seats shared by the Evolutionist Party and Republican Union are reported jointly; no party split is inferred. '
 if y==1892:e['notes']+='The 103-seat grouping includes the Regenerator Party and other parties/independents. Six national-level seats and overseas returns are outside the source table. '
 if y==2026 and ri==1:e['endDate']='2026-02-15';e['notes']+='The runoff took place on 8 February, with postponed voting in affected localities on 15 February. '
 e['summary']=('Presidential '+('round '+e['round']+' ' if e['round'] else '')+'results.' if body=='President' else str(ss)+' mandates in the available result table.') if e['results'] else 'Election held; a numeric national result breakdown is not available in the cited source.'
 if not e['results']:e['resultStatus']='not-entered'
 records.append(e);audit.append(dict(id=e['id'],source=x['url'],sourceSha256=x['sha256'],expectedSeats=expected,recordedSeats=ss,expectedVotes=total.get('votes'),recordedVotes=vv,meta=meta))
for x in EX:
 if not re.search(r'\d{4}',x['name']) or '1911_Portuguese_Constituent_' in x['name']:continue
 y=int(re.search(r'\d{4}',x['name'])[0]);pres='presidential' in x['name'];body='President' if pres else 'Constituent Cortes' if y==1820 else 'Constituent Assembly' if 'Constituent' in x['name'] else 'Assembly of the Republic' if y>=1976 else 'National Assembly' if y>=1934 else 'Chamber of Deputies'
 if y==1828:body="People's Estate"
 if x['name']=='November_1836_Portuguese_legislative_election':body='Constituent Cortes'
 if y==1918 and 'general' in x['name']:
  for t,b in zip(x['tables'],['President','Chamber of Deputies','Senate']):parse(x,t,b)
 elif x['tables']:
  parse(x,x['tables'][0],body)
  if pres and any('Second round' in r for r in x['tables'][0]):parse(x,x['tables'][0],body,1)
  elif not pres and 1915<=y<=1925 and len(x['tables'])>1:parse(x,x['tables'][1],'Senate')
 else:
  date,end,precision=dates(x);e=base(date,body,precision);e['endDate']=end;e['sources']=[src('Election history and references',x['url'])];e['resultStatus']='not-entered';e['summary']='Election held; a numeric national result breakdown is not available in the cited source.';e['notes']='Historical franchise restrictions and changing electoral systems affect comparability. Unverified party totals are left blank.'
  if 'indirect' in x['prose'][:1800] or y==1820:e['electionMethod']='indirect'
  records.append(e)
  if y in [1838,1840]:
   u=copy.deepcopy(e);u['id']=u['id'].replace('deputies','senate');u['body']='Senate';u['title']=u['title'].replace('Chamber of Deputies','Senate');u['seriesId']='PT-senate-1838';records.append(u)
# The elective portion of the Chamber of Peers had four general renewals, not a ballot at every lower-house election.
for date in ['1885-12-01','1887-03-01','1890-04-01','1894-04-01']:
 e=base(date,'Chamber of Peers','month');e['electionMethod']='indirect';e['resultStatus']='not-entered';e['summary']='General election of the elective portion of the Chamber of Peers.';e['notes']='Electoral colleges chose temporary peers alongside royal appointees and peers by right. The month is documented; no single nationwide polling day or numeric party allocation is asserted. The statutory 50 elective places are not treated as a verified count of seats returned in this ballot.';e['sources']=[src('Paulo Jorge Fernandes: A Câmara dos Pares do Reino, p. 216','https://research.unl.pt/ws/portalfiles/portal/75830388/A_C_mara_dos_Pares_do_Reino.pdf'),src('Parliament: Chamber of Peers archival guide','https://www.parlamento.pt/Parlamento/Paginas/guia-fundo-camara-pares-1826-1910.aspx')];records.append(e)
e=base('1911-08-25','Senate');e['electionMethod']='indirect';e['resultStatus']='not-entered';e['totalSeats']=71;e['summary']='Constituent deputies selected 71 senators to form the new upper chamber.';e['notes']='The Constituent Assembly selected senators through four lists of 21, 21, 21 and 8 names. A verified party allocation is unavailable; no lower-house result is reused as a Senate vote.';e['sources']=[src('Parliament: election of the first Senate','https://ahpweb.parlamento.pt/Detalhe/?id=31446&pesq=pa&q=AND__topic_type_id_2__18_&t=7')];records.append(e)
# Historical indirect presidential ballots, transcribed separately so rounds are never added together.
manual=json.loads((P/'indirect-presidential.json').read_text())
for m in manual:
 for ri,votes in enumerate(m['ballots']):
  e=base(m['date'],'President',round=str(ri+1) if len(m['ballots'])>1 else '');e['electionMethod']='indirect';e['seriesId']='PT-president-indirect';e['voteBasis']='Votes cast by parliamentarians or electoral-college members; shares include blank/invalid ballots';e['sources']=[src('Historical presidential ballot results',m['source'])]+[src('Parliament / Presidency historical archive',u) for u in m.get('primary',[])]
  for (name,party),v in zip(m['candidates'],votes):
   if v is not None:
    r=result(e,name,party,v,round(v/m['totals'][ri]*100,2),None)
    if ri==len(m['ballots'])-1 and name==m['winner']:r['winner']=True
  e['summary']='Presidential ballot in '+('Congress.' if m['date']<'1930' else 'the electoral college.')
  e['notes']='Indirect election: candidate votes are parliamentary or electoral-college ballots, not public votes. Public turnout and previous seat counts do not apply. '+str(m['totals'][ri])+' ballots were cast in this round, including '+str(m['totals'][ri]-sum(v or 0 for v in votes))+' blank or invalid ballots. '+m.get('note','')
  if m['date']>'1930':e['notes']+=' Held under Estado Novo with a regime-controlled electoral college and a sole candidate.'
  records.append(e);audit.append(dict(id=e['id'],source=m['source'],expectedSeats=None,recordedSeats=0,expectedVotes=sum(v or 0 for v in votes),recordedVotes=sum(v or 0 for v in votes),ballotsCast=m['totals'][ri]))
# Preserve known winners even where no trustworthy numeric tally survives in the cited table.
for y,n,p in [(1949,'Óscar Carmona','National Union'),(1951,'Francisco Craveiro Lopes','National Union')]:
 e=next(e for e in records if e['body']=='President' and e['startDate'].startswith(str(y)));result(e,n,p,None,None,None)['winner']=True;e['resultStatus']='final';e['summary']='Unopposed election following opposition withdrawal or exclusion; candidate vote totals are unavailable.'
 e['notes']+='The result identifies the elected candidate without inventing a vote count or a 100% share.'
for e in records:
 if e['startDate']=='1905-02-12':e['sources'].append(src('Parliament: 1905 election records','https://ahpweb.parlamento.pt/Detalhe/?id=39739&pesq=pa&q=AND__topic_type_id_2__45515_%3B&t=4'));e['notes']+='The polling date follows the parliamentary archive (12 February), resolving the secondary article’s conflicting December date.'
 if e['startDate']=='1822-08-18':e['sources'].append(src('Parliament: the electoral law and election of 1822','https://www.parlamento.pt/Parlamento/Paginas/A-lei-eleitoral-de-1822.aspx'));e['notes']+='Parliament dates the election to 18 August; November dates refer to the assembly of the new Cortes.'
 if e['body']=='National Assembly' and e['startDate'][:4] in ['1949','1965']:
  result(e,'National Union','National Union',None,None,e['totalSeats']);e['resultStatus']='final';e['summary']='National Union won all '+str(e['totalSeats'])+' seats; party vote totals are not assigned.';e['sources'].append(src('National Union: parliamentary seat history','https://en.wikipedia.org/wiki/National_Union_(Portugal)'));a=next(a for a in audit if a['id']==e['id']);a['recordedSeats']=e['totalSeats'];a['expectedSeats']=e['totalSeats']
 if e['body']=='Senate' and e['startDate'].startswith('1925'):e['totalSeats']=70;e['notes']+='The source lists 65 mandates against a 70-seat chamber; the five-seat shortfall is not assigned to a party.'
 if e['body']=='President' and e['startDate'].startswith('2026'):
  rd='2' if e['round']=='2' else '1';e['sources'].append(src('CNE: certified presidential result map','https://www.cne.pt/sites/default/files/dl/eleicoes/2026_pr/docs_geral/2026_pr_'+rd+'-sufragio_mapa_oficial_dr.pdf'))
  if rd=='2':e['notes']+='Counts reproduce the published national certification. CNE flags omissions of 5,347 candidate votes, 68 blank/invalid ballots and registration discrepancies in the underlying general tabulation; those observations are not silently added to the certified figures.'
# Previous mandates refer to the immediately preceding comparable ballot in the same chamber.
for series in sorted(set(e['seriesId'] for e in records if e['type']=='parliamentary')):
 prev=None
 for e in sorted((e for e in records if e['seriesId']==series),key=lambda e:e['startDate']):
  if prev and e['startDate'][:4]!='1913' and prev['startDate'][:4]!='1913' and e['body'] not in ['Constituent Assembly','Constituent Cortes']:
   for r in e['results']:
    old=next((o for o in prev['results'] if o.get('partyId') and o.get('partyId')==r.get('partyId')),None)
    if old:r['previousSeats']=old['seats']
  prev=e
old=next(x['data'] for x in json.loads((P/'pre-import-backup.json').read_text()) if x['kind']=='world_election')
e=next(e for e in records if e['body']=='Assembly of the Republic' and e['startDate'].startswith('2025'));oldid=e['id'];e['id']=old['id'];e['version']=old['version']+1;e['seriesId']='PT-AR'
for r in e['results']:r['id']=r['id'].replace(oldid,e['id'])
for a in audit:
 if a['id']==oldid:a['id']=e['id']
e['sources'].append(src('CNE: certified 2025 national result map','https://www.cne.pt/sites/default/files/dl/eleicoes/2025_ar/2025_ar_mapa_oficial_dr.pdf'))
for e in records:
 if e['body']=='Assembly of the Republic':e['seriesId']='PT-AR'
 y=e['startDate'][:4];same=[o for o in records if o['body']==e['body'] and o['startDate'].startswith(y)]
 detail=(datetime.datetime.strptime(e['startDate'],'%Y-%m-%d').strftime('%B') if len(same)>1 else '')+(', round '+e['round'] if e['round'] else '')
 e['title']='Portugal '+('presidential' if e['body']=='President' else e['body'])+' election'+(' ('+detail.strip(', ')+')' if detail else '')+' '+y
for filename,value in [('records',sorted(records,key=lambda e:(e['startDate'],e['body'],e['round']))),('parties',list(profiles.values())),('reconciliation',audit)]: (P/(filename+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(len(records),'records',sum(len(e['results']) for e in records),'result rows',len(profiles),'party profiles')
