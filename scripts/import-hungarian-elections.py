"""Reproduce Hungary's national archive using existing models; no database writes.

Keep different ballots/rounds apart; never invent missing votes or modern ideology.
"""
from pathlib import Path
import json,re,uuid,hashlib,colorsys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/hungarian-election-import'
DATA=json.loads((OUT/'source-tables.json').read_text());LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-13';records=[];profiles={};audit=[]
NVI='https://www.valasztas.hu/orszaggyulesi-valasztasok'
PARLIAMENT='https://www.parlament.hu/web/house-of-the-national-assembly/key-dates-from-setting-the-parliamentary-election-to-forming-a-government'
PALETTE={'Fidesz':'#f47721','Fidesz–KDNP':'#f47721','Tisza Party':'#277c51','Hungarian Socialist Party':'#c72d35','Hungarian Democratic Forum':'#317947','Alliance of Free Democrats':'#257bbe','Jobbik':'#278f74','Our Homeland Movement':'#387645','Democratic Coalition':'#2477b8','Hungarian Two-Tailed Dog Party':'#cf454f','Hungarian Communist Party':'#c3262e'}
def num(s):
 s=s.replace(',','').replace('\xa0','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def clean(s):return re.sub(r'\s*\[(?:ro|de|hu|en|pl)\]','',s).strip()
def profile(name,year,url):
 name=clean(name)
 name={'Fidesz – Hungarian Civic Alliance':'Fidesz','Fidesz–Hungarian Civic Alliance':'Fidesz','Hungarian Two Tailed Dog Party':'Hungarian Two-Tailed Dog Party'}.get(name,name)
 if name.startswith('Independent ') and name not in ('Independent Smallholders Party','Independent Hungarian Democratic Party'):return None
 if not name or name in ('Independent','Independents','Independent groups','Vacant') or name.lower().startswith(('other','against','disputed','institutional','rightful')):return None
 key=('historical:' if year<1990 else 'modern:')+name
 if key not in profiles:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff
  color=PALETTE.get(name,'#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.42,.58)))
  profiles[key]={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/hu/'+key)),'country_id':'hu','name':name if year>=1990 else name+' — historical','short_name':name[:100],'color':color,'ideology_ids':[],'archived':False,'notes':'Election-era party, front or alliance label. No continuity with a similarly named organisation is inferred. Source: '+url+'. Display colour is an editorial palette; no official-branding or ideological assessment is implied.'}
 return profiles[key]
def result(e,name,votes=None,share=None,seats=None,party=None):
 name=clean(name);pname=name if party is None else clean(party);p=profile(pname,int(e['startDate'][:4]),e['sources'][0]['url'])
 r=dict(id=e['id']+'-row-'+str(len(e['results'])+1),name=name,party=pname,color=p['color'] if p else '#808080',votes=votes,share=share,seats=seats,electoralVotes=None,winner=False,advanced=False,ideologyIds=[])
 if p:r['partyId']=p['id']
 e['results'].append(r);return r
def base(date,office,url,precision='day',end=''):
 year=int(date[:4]);body='President of Hungary' if office=='president' else 'Diet — representative chamber' if year<1920 else 'Provisional National Assembly' if year==1944 else 'National Assembly'
 return dict(id=f'world-hungary-{office}-{date}',countryId='hu',title=body,type='presidential' if office=='president' else 'parliamentary',body=body,startDate=date,endDate=end,precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='hu-'+office,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='No verified national result table entered',results=[],sources=[dict(label='Election history and source bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=2,electionMethod='indirect' if office=='president' else 'direct',live=dict(enabled=False,reporting=None,unit='precincts',bulletin='',updated=''))
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

DATES={1848:('06-02','07-09'),1861:('03-01','04-07'),1865:('11-10','12-11'),1869:('03-09','04-13'),1872:('06-12','07-09'),1875:('07-01','08-18'),1878:('08-05','08-14'),1881:('06-24','07-03'),1884:('06-13','06-22'),1887:('07-17','07-26'),1892:('01-29','02-03'),1896:('10-29','11-04'),1901:('10-02','10-09'),1905:('01-26','02-04'),1906:('04-29','05-08'),1910:('06-01','06-10'),1922:('05-28','06-02'),1926:('12-08','12-15'),1931:('06-28','06-30'),1935:('03-31','04-07'),1939:('05-28','05-29'),1945:('11-04',''),1947:('08-31',''),1949:('05-15',''),1953:('05-17',''),1958:('11-16',''),1963:('02-24',''),1967:('03-19',''),1971:('04-25',''),1975:('06-15',''),1980:('06-08',''),1985:('06-08','06-22'),1990:('03-25','04-08'),1994:('05-08','05-29'),1998:('05-10','05-24'),2002:('04-07','04-21'),2006:('04-09','04-23'),2010:('04-11','04-25'),2014:('04-06',''),2018:('04-08',''),2022:('04-03',''),2026:('04-12','')}
MONTHS={1825:8,1830:8,1832:11,1839:5,1843:4,1847:8}
def parliamentary(key,t,e,year):
 # Select the most detailed header and the final allocation, never a component
 # seat subtotal such as list seats or first-round constituency mandates.
 candidates=[(i,[c['text'] for c in row]) for i,row in enumerate(t['rows']) if 'Votes' in [c['text'] for c in row] or ('Total' in [c['text'] for c in row] and 'Party' in [c['text'] for c in row]) or 'Seats' in [c['text'] for c in row]]
 hi,h=candidates[-1] if year==1944 else next((i,h) for i,h in candidates if 'Votes' in h) if any('Votes' in h for _,h in candidates) else candidates[0]
 si=h.index('Total seats') if 'Total seats' in h else h.index('Total') if 'Total' in h else h.index('Seats')
 vi=h.index('Votes') if 'Votes' in h else si
 omit_votes=year<=1847 or year in (1920,1944,1985)
 m=meta(t,vi,si);control=m.get('Total',{});valid=control.get('votes') if vi!=si and not omit_votes else None
 groups={};vseen=set();sseen=set()
 for row in t['rows'][hi+1:]:
  tx=[c['text'] for c in row]
  if len(tx)<=si:continue
  names=list(dict.fromkeys(x for x in tx[:min(vi,si)] if x))
  if not names:continue
  if names==['Total']:break
  if 'Total' in names or any(x.startswith(('Source:','Registered','Valid votes','Invalid','Total votes')) for x in names):continue
  name=names[0];v=integer(tx[vi]) if vi!=si and not omit_votes else None;seat=integer(tx[si]);seat=0 if seat is None and tx[si] in ('–','—','-') else seat
  if v is None and seat is None:continue
  x=groups.setdefault(name,dict(votes=None,seats=0,seatKnown=True))
  if v is not None and row[vi]['cell'] not in vseen:x['votes']=(x['votes'] or 0)+v;vseen.add(row[vi]['cell'])
  if seat is not None and row[si]['cell'] not in sseen:x['seats']+=seat;sseen.add(row[si]['cell'])
  elif seat is None:x['seatKnown']=False
 e['totalSeats']=control.get('seats')
 for name,x in groups.items():result(e,name,x['votes'],round(x['votes']/valid*100,6) if valid and x['votes'] is not None else None,x['seats'] if x['seatKnown'] else None)
 vs=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results'])
 e['resultStatus']='final';e['resultCoverage']='complete' if e['totalSeats'] is not None and ss==e['totalSeats'] and (valid is None or vs==valid) else 'partial'
 e['turnout']=m.get('Registered voters/turnout',{}).get('share') if valid else None
 e['voteBasis']=f'Reported source-scoped vote marks / {valid:,}; see electoral-system notes' if valid else 'Source-scoped seat allocation; no comparable popular-vote denominator entered'
 e['notes']='Election-era party/front/group labels are retained; no ideology or legal continuity is inferred. Shared coalition cells are counted once. Missing data is not filled with guessed residual votes or seats. '
 if year<=1847:
  e.pop('electionMethod',None);e['notes']+='This was an estates-based Diet election under restricted noble/municipal representation. The small vote column refers to territorial/representative alignments, not national popular ballots, and is omitted. Seat totals describe the source’s grouped representatives, not a modern equal-vote chamber. '
 elif year<1920:e['notes']+='Restricted franchise applied. These are representative-chamber mandates; the hereditary/appointed House of Magnates is not invented as a second general election. Croatian representation or co-opted members outside the reported allocation are not assigned invented party seats. '
 if year==1920:e['notes']+='Territorial elections occurred in January 1920, June–July 1920 and October 1921 as occupation and borders changed. This record contains the final 219-seat allocation; the three electoral cohorts and their turnout/votes are not naively added. The year-precision date is a sorting anchor, not an exact national polling day. '
 if year==1944:
  e['electionMethod']='indirect';e['notes']+='The Provisional National Assembly was selected through local assemblies in liberated areas, with additional representatives selected in April and June 1945. This is the final 498-member composition, not a nationwide popular election or an initial 230-member snapshot. '
 if 1922<=year<=1939:e['notes']+='Historical restricted suffrage, uncontested mandates and differing open/secret electoral procedures applied. Reported vote marks need not represent one nationwide party ballot per elector. '
 if year==1947:e['notes']+='Declared historical returns are retained in the context of the blue-ballot fraud and Communist consolidation; no reconstructed genuine voter preference is invented. '
 if 1949<=year<=1985:
  e['round']='Noncompetitive front election';e['notes']+='A Communist-era noncompetitive front election. A common front vote is not attributed to constituent parties or independents, and declared official totals do not establish freely expressed voter preference. '
 if year==1985:e['notes']+='The constituency and national-list ballots had separate denominators and shared front totals. Only the source’s political membership seat allocation is entered; its rows account for 386 filled seats plus one explicitly reported vacancy, within the 387-seat chamber. No popular party vote is assigned to those membership groups. '
 if year>=1990:
  e['sources'].insert(0,dict(label='NVI: official parliamentary election archive',url=NVI))
  e['voteBasis']=f'Valid proportional/list ballots ({valid:,}); full final seat allocation across electoral components' if valid else e['voteBasis']
  e['notes']+='Displayed shares use proportional/list ballots only. Constituency ballots, later constituency rounds and compensation/fractional votes are different components and are not added to that denominator. The seat total is the full chamber after all components/rounds. Non-voting minority spokespeople are not counted as parliamentary seats. '
  if year<=2010:e['round']='Final allocation after two rounds'
 if e['totalSeats'] is not None and ss!=e['totalSeats']:e['notes']+=f'Entered rows account for {ss} of {e["totalSeats"]} source-scoped seats. '
 if valid is not None and vs!=valid:e['notes']+=f'Entered vote rows sum to {vs:,}, while the source denominator is {valid:,}; coverage remains partial. '
 e['summary']='Declared results and final source-scoped seat allocation; historical and ballot-system limits are explained in the notes.'
 reconcile(e,valid)

for key,item in DATA.items():
 if 'parliamentary' not in key:continue
 year=int(key[:4]);md,end=DATES.get(year,(f'{MONTHS.get(year,1):02}-01',''))
 precision='day' if year in DATES else 'month' if year in MONTHS else 'year'
 e=base(f'{year}-{md}','parliament',LINKS[key],precision,end=f'{year}-{end}' if end else '')
 if item['tables']:parliamentary(key,item['tables'][0],e,year)
 else:
  e['summary']='Documented election; a verified national result table is not yet available.';e['notes']='The event remains in the timeline. Party allocations, votes and turnout are not inferred from later composition. The historical source does not establish a reliable complete result table.'
  if year==1848:e['notes']+='This first modern representative election followed the April Laws; source accounts conflict on elected/transitional territorial membership, so no chamber capacity is invented.'
  reconcile(e)
 records.append(e)

PDATES={1990:['08-03'],1995:['06-19'],2000:['06-05','06-06','06-06'],2005:['06-06','06-07','06-07'],2010:['06-29'],2012:['05-02'],2017:['03-13','03-13'],2022:['03-10'],2024:['02-26'],2026:['08-11']}
for year,dates in PDATES.items():
 key=f'{year}_Hungarian_presidential_election';t=DATA[key]['tables'][0];hi,h=header(t);vis=[i for i,x in enumerate(h) if x=='Votes'];ci=max(i for i,x in enumerate(h) if x=='Candidate')
 pi=h.index('Party') if 'Party' in h else max(i for i,x in enumerate(h) if x=='Party or alliance') # formal label in the last subcolumn
 for ballot,md in enumerate(dates):
  e=base(f'{year}-{md}','president',LINKS[key]);e['round']=f'Assembly ballot {ballot+1}' if len(dates)>1 else 'Assembly election'
  if len(dates)>1:e['id']+=f'-ballot-{ballot+1}'
  vi=vis[ballot];m=meta(t,vi);valid=m['Total']['votes']
  for row in t['rows'][hi+1:]:
   tx=[c['text'] for c in row]
   if len(tx)<=vi:continue
   if tx[ci]=='Total':break
   v=integer(tx[vi])
   if v is not None and tx[ci] not in ('','Candidate'):result(e,tx[ci],v,round(v/valid*100,6),party='' if tx[ci].startswith('Against') else tx[pi])
  e.update(resultStatus='final',resultCoverage='complete' if sum(r['votes'] for r in e['results'])==valid else 'partial',turnout=None,voteBasis=f'Valid assembly ballot outcomes ({valid}); not popular presidential votes')
  e['notes']='The President was elected indirectly by the legislature. Vote percentages use valid assembly ballot outcomes, including recorded votes against a sole candidate; these are not shares of national voters. Public turnout remains null. Candidate affiliation is distinct from parliamentary nomination/support. Each ballot has its own denominator; failed ballots are not marked as elected outcomes. '
  if year in (2000,2005):e['notes']+='The first two ballots required two-thirds of all assembly members; the decisive third ballot used the applicable lower threshold. A majority of votes cast in an earlier ballot did not itself elect the candidate. '
  if year==2017:e['notes']+='Áder’s 131 votes fell short of two-thirds of the 199-member Assembly in the first ballot; he won only on the second ballot under its majority rule. '
  candidates=[r for r in e['results'] if not r['name'].startswith('Against')]
  if ballot==len(dates)-1:max(candidates,key=lambda r:r['votes'])['winner']=True
  e['summary']='Decisive assembly election.' if ballot==len(dates)-1 else 'Non-decisive assembly ballot; no candidate was elected in this ballot.'
  if year in (2012,2024,2026):e['snap']=True
  if year==2012:e['notes']+='The early election followed Pál Schmitt’s resignation; it was not a scheduled end-of-term selection. '
  if year==2024:e['notes']+='Tamás Sulyok was an independent nominated by Fidesz–KDNP; nomination is not treated as formal party membership.'
  if year==2026:
   e['sources'].insert(0,dict(label='Government: 11 August presidential election, 140 for and 6 against',url='https://kormany.hu/hirek/koztarsasagi-elnokot-valasztott-az-orszaggyules'))
   e['notes']+='András Baka was an independent nominated by Tisza. The official government announcement confirms 140 votes for and six against. The election date is 11 August, distinct from his 19 August entry into office.'
  records.append(e);reconcile(e,valid)

for date,name,party,url in [('1919-01-11','Mihály Károlyi','Party of Independence and 48–Károlyi','https://hirado.hu/2010/06/29/schmitt-pal-magyarorszag-uj-koztarsasagi-elnoke/'),('1946-02-01','Zoltán Tildy','Independent Smallholders Party','https://mnl.gov.hu/mnl/tml/hirek/tildy_zoltan_koztarsasagi_elnok_a_szekszardi_szureti_mulatsagon?theme=mnl'),('1948-08-03','Árpád Szakasits',"Hungarian Working People's Party",'https://neb.hu/nemzeti-emlekezet-bizottsaga/articles/show/szakasits-arpad')]:
 e=base(date,'president',url);e.update(round='Council selection' if date.startswith('1919') else 'Assembly selection',resultStatus='final',summary=name+' was selected as President.',voteBasis='Indirect selection; exact ballot counts unverified',notes='The selected President is known, but precise ballot counts and participation are unverified and remain null. This is not a nationwide popular presidential ballot. The subsequent collective Presidential Council (1949–1989) and regent/monarch selections are not reclassified as elections to this individual presidential office.')
 result(e,name,party=party)['winner']=True;records.append(e);reconcile(e)

primary=json.loads((OUT/'primary-reconciliation.json').read_text())
latest=next(e for e in records if e['id']=='world-hungary-parliament-2026-04-12')
assert sum(r['votes'] or 0 for r in latest['results'])==primary['validListVotes']
for r in latest['results']:
 if r['name'] in primary['majorParties']:
  p=primary['majorParties'][r['name']];assert r['votes']==p['listVotes'] and r['seats']==p['totalSeats']
latest['sources'].insert(0,dict(label='NVI: final national list protocol and minority ballots',url=primary['listSource']))
latest['sources'].insert(1,dict(label='NVI: final 199-member Parliament composition',url=primary['seatSource']))
latest['turnout']=round(primary['participatingListVoters']/primary['registeredListVoters']*100,6)
latest['notes']+='The 2026 list totals and final major-party allocations were independently checked against NVI’s official national protocol and Parliament composition. List participation is 6,408,362 of 8,112,646 registered voters; counted list ballot papers (6,404,403) are a different quantity.'
for e in records:
 peers=[x['id'] for x in records if x['id']!=e['id'] and x['type']==e['type'] and x['startDate'][:4]==e['startDate'][:4]]
 if peers:e['linkedElectionIds']=peers
 assert sum(r['share'] or 0 for r in e['results'])<=100.2,e['id']
 if e['totalSeats'] is not None:assert sum(r['seats'] or 0 for r in e['results'])<=e['totalSeats'],e['id']
records.sort(key=lambda e:(e['startDate'],e['id']))
for name,obj in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('Built',len(records),'records and',len(profiles),'profiles.')
print('Missing tables',[e['id'] for e in records if not e['results']])
print('Partial tables',[(e['id'],e['totalSeats'],sum(r['seats'] or 0 for r in e['results'])) for e in records if e['results'] and e['resultCoverage']=='partial'])
