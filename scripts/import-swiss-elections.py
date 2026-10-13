"""Reproduce the Swiss archive using existing election and party models; no database writes."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/swiss-election-import'
DATA=json.loads((OUT/'source-tables.json').read_text());LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-13'
records=[];profiles={};audit=[]
PRIMARY=json.loads((OUT/'primary-reconciliation.json').read_text())
PALETTE={"Swiss People's Party":"#4b8b3b","Social Democratic Party":"#e30613","FDP.The Liberals":"#0077b8","Free Democratic Party":"#0077b8","The Centre":"#f39325","Christian Democratic People's Party":"#f39325","Green Party":"#65a83d","Green Liberal Party":"#a6bb39","Swiss Party of Labour":"#b5262d","Evangelical People's Party":"#edc331","Conservative Democratic Party":"#dda02b","Radical Left":"#0077b8","Liberal Centre":"#638fbd","Catholic Right":"#e89b3a"}
def num(s):
 s=s.replace(',','').replace('\xa0','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def clean(s):return re.sub(r'\s*\[(?:ro|de|hu|en|pl)\]','',s).strip()
def profile(name,year,url):
 name=clean(name)
 if not name or name in ('Independent','Independents','Independent groups','Affiliation not verified','Unattributed ballots') or name.lower().startswith(('other','against','disputed','institutional','rightful','unknown','split','independent','vacant')):return None
 key=('historical:' if year<1945 else 'modern:')+name
 if key not in profiles:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff
  color=PALETTE.get(name,'#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.42,.58)))
  profiles[key]={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/ch/'+key)),'country_id':'ch','name':name if year>=1945 else name+' — historical','short_name':name[:100],'color':color,'ideology_ids':[],'archived':False,'notes':'Election-era party, front or alliance label. No continuity with a similarly named organisation is inferred. Source: '+url+'. Display colour is an editorial palette; no official-branding or ideological assessment is implied.'}
 return profiles[key]
def result(e,name,votes=None,share=None,seats=None,party=None):
 name=clean(name);pname=name if party is None else clean(party);p=profile(pname,int(e['startDate'][:4]),e['sources'][0]['url'])
 r=dict(id=e['id']+'-row-'+str(len(e['results'])+1),name=name,party=pname,color=p['color'] if p else '#808080',votes=votes,share=share,seats=seats,electoralVotes=None,winner=False,advanced=False,ideologyIds=[])
 if p:r['partyId']=p['id']
 e['results'].append(r);return r
def base(date,office,url,precision='day',end=''):
 body={'national-council':'National Council','states':'Council of States','federal-council':'Federal Council — collective executive','president':'President of the Confederation'}[office]
 return dict(id=f'world-switzerland-{office}-{date}',countryId='ch',title=body,type='presidential' if office in ('president','federal-council') else 'parliamentary',body=body,startDate=date,endDate=end,precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='General',seriesId='ch-'+office,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='No verified national result table entered',results=[],sources=[dict(label='Election results and historical bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=2,electionMethod='direct',live=dict(enabled=False,reporting=None,unit='precincts',bulletin='',updated=''))
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

PARLIAMENT_DATES='https://www.parlament.ch/de/%C3%BCber-das-parlament/Seiten/nr-wahltermine-seit-1848.aspx'
STATES_METHOD='https://www.parlament.ch/de/%C3%BCber-das-parlament/Seiten/faktenblatt-staenderat.aspx'
COUNCIL_METHOD='https://www.parlament.ch/de/%C3%BCber-das-parlament/Seiten/Bundesratswahlen.aspx'
CALENDAR='https://www.parlament.ch/en/ratsbetrieb/sessions/schedule'
ALIASES={'The Liberals':'FDP.The Liberals',"Swiss Conservative People's Party":"Conservative People's Party",'Green Party of Switzerland':'Green Party','Green Liberal Party of Switzerland':'Green Liberal Party','Social Democratic Party of Switzerland':'Social Democratic Party',"Christian Democratic People's Party of Switzerland":"Christian Democratic People's Party",'Swiss Labour Party':'Swiss Party of Labour','Labour Party':'Swiss Party of Labour'}
def canonical(name):return ALIASES.get(clean(name),clean(name))
def abbreviation(code,year):
 return {'FDP':'Free Democratic Party' if year<2009 else 'FDP.The Liberals','Mitte':'The Centre','M-E':'The Centre','DM':'The Centre','SP':'Social Democratic Party','SPS':'Social Democratic Party','SVP':"Swiss People's Party",'CVP':"Christian Democratic People's Party",'KVP':"Conservative People's Party",'KCV':'Conservative-Christian Social People’s Party','BGB':'Party of Farmers, Traders and Independents','BB':'Party of Farmers, Traders and Independents','LPS':'Liberal Democratic Party' if year<1977 else 'Liberal Party','LDP':'Liberal Democratic Party','DP':'Democratic Group','Dem':'Democratic Group','Grüne':'Green Party','GPS':'Green Party','Greens':'Green Party','GLP':'Green Liberal Party','BDP':'Conservative Democratic Party','EVP':"Evangelical People's Party",'CSP':'Christian Social Party','PdA':'Swiss Party of Labour','Sol.':'Solidarity','FGA':'Feminist and Green Alternative Groups','SD':'Swiss Democrats','EDU':'Federal Democratic Union','Lega':'Ticino League','MCR':'Geneva Citizens Movement','MCG':'Geneva Citizens Movement','LdU':'Alliance of Independents','POCH':'Progressive Organisations of Switzerland','Rep.':'Republican Movement','PSA':'Autonomous Socialist Party','FPS':'Freedom Party of Switzerland','Sep.':'Jurassian separatists','Übrige':'Other lists','parteilos':'Independent','None':'Independent','Independent':'Independent'}.get(code,code)
def allocation(e,t,year,states=False):
 hi,h=header(t);si=h.index('Seats')
 if states and h.count('Seats')>1:
  totals=t['rows'][hi+1];si=next(i for i,c in enumerate(totals) if c['text']=='Total');hi+=1
 vi=h.index('Votes') if 'Votes' in h else None
 control=next((r for r in t['rows'][hi+1:] if r and r[0]['text']=='Total'),None)
 e['totalSeats']=integer(control[si]['text']) if control and len(control)>si else 46 if states and year>=1979 else 44 if states else None
 shared={};seat_cells=set()
 for row in t['rows'][hi+1:]:
  tx=[c['text'] for c in row]
  if len(tx)<=si:continue
  if tx[0]=='Total':break
  names=list(dict.fromkeys(x for x in tx[:si if vi is None else vi] if x))
  if not names or names[0].startswith(('Source:','Registered','Valid','Invalid','Total votes')):continue
  seat=integer(tx[si]);seat=0 if tx[si] in ('–','—','-') else seat
  if seat is None:continue
  # Rounded voter equivalents and historical multi-vote figures are not ballots.
  share=num(tx[vi+1]) if vi is not None and not states and year>=1919 else None
  name=canonical(names[0]);seat_key=row[si]['cell']
  if seat_key in seat_cells:seat=0
  else:seat_cells.add(seat_key)
  share_key=row[vi+1]['cell'] if share is not None else None
  if share_key is not None and share_key in shared:
   r=shared[share_key];r['seats']+=seat;r['name']+=' / '+name;r['party']=r['name'];p=profile(r['party'],year,e['sources'][0]['url']);r.update(color=p['color'],partyId=p['id'])
  else:
   r=result(e,name,share=share,seats=seat)
   if share_key is not None:shared[share_key]=r
 ss=sum(r['seats'] or 0 for r in e['results'])
 e.update(resultStatus='final',resultCoverage='complete' if ss==e['totalSeats'] else 'partial',voteBasis='Party seat composition; no nationwide Council of States popular-vote denominator' if states else 'Normalised party strength / voter equivalents; rounded proxy counts are not entered as ballots' if year>=1919 else 'Reported historical group/party seats; no comparable national popular-vote denominator entered')
 e['summary']='Final reported chamber allocation; historical membership and ballot scope are documented in the notes.'
 e['notes']='Party and group labels reflect the referenced election-era table. Display colours are editorial; no legal continuity or ideology is inferred. '
 if states:
  e['notes']+='Council of States members follow cantonal election law, varying dates and historically varying terms, indirect parliamentary selection or Landsgemeinde elections. This is the source’s election-year composition snapshot, not a claim that every seat was simultaneously contested nationwide. Votes, shares and nationwide turnout remain null; cantonal runoffs and earlier selections are not naively added. Year precision identifies the snapshot year; January 1 is only a sorting anchor. The chamber had 44 seats before Jura joined and 46 thereafter. '
  e.pop('electionMethod',None);e['sources'].append(dict(label='Parliament: cantonal selection and absence of national general renewal',url=STATES_METHOD))
 else:
  e['notes']+='Before 1919 majority voting and multiple ballots/selections prevent treating historical aggregate candidate figures as one comparable national popular denominator. From 1919, quoted national party strength is based on canton-size-normalised voter equivalents rather than summed candidate/list vote marks. Rounded voter-equivalent counts are deliberately not entered as exact ballot counts. Seats use this election’s historical capacity, not today’s 200. '
  e['sources'].append(dict(label='Parliament: historical national polling dates',url=PARLIAMENT_DATES))
  if vi is not None:e['turnout']=meta(t,vi,si).get('Registered voters/turnout',{}).get('share')
 if ss!=e['totalSeats']:e['notes']+=f'The entered allocations total {ss} of {e["totalSeats"]} source-scoped seats. Unaccounted mandates remain unassigned. '
 e['_valid']=None

SUPPLEMENT=json.loads((OUT/'states-supplement.json').read_text())
for key,item in DATA.items():
 year=int(key[:4]);date=PRIMARY['nationalDates'].get(str(year),'1848-10-01');e=base(date,'national-council',LINKS[key],'month' if year==1848 else 'day')
 t=next(t for t in item['tables'] if t['heading'] in ('National Council','Results') and any(c['text']=='Party' for r in t['rows'] for c in r) and any(c['text']=='Seats' for r in t['rows'] for c in r))
 allocation(e,t,year)
 if year==1848:e['notes']+='The first election had no uniform national polling day; October precision is intentional. '
 p=next((p for p in PRIMARY['nationalCouncil'] if p['year']==year),None)
 if p:
  e['results']=[]
  for r in p['rows']:result(e,abbreviation(r['label'],year),share=r['share'],seats=r['seats'])
  e.update(totalSeats=200,resultCoverage='complete');e['sources'].insert(0,dict(label='Federal Statistical Office: final normalised party strength',url=p['shareSource']));e['sources'].insert(1,dict(label='Federal Statistical Office: elected mandates',url=p['seatSource']))
  e['notes']+='Modern percentages and every party’s mandates are independently checked against the FSO PX-Web final national series. '
 records.append(e)

 ts=[t for t in item['tables'] if t['heading']=='Council of States' and any(c['text']=='Party' for r in t['rows'] for c in r)]
 if ts:
  s=base(f'{year}-01-01','states',LINKS[key],'year');s['title']='Council of States — election-year composition';allocation(s,ts[0],year,True);records.append(s)
 elif str(year) in SUPPLEMENT:
  p=SUPPLEMENT[str(year)];s=base(f'{year}-01-01','states',p['source'],'year');s['title']='Council of States — election-year composition';s['totalSeats']=46 if year>=1979 else 44
  for r in p['rows']:result(s,abbreviation(r['label'],year),seats=r['seats'])
  s.update(resultStatus='final',resultCoverage='complete' if sum(r['seats'] for r in s['results'])==s['totalSeats'] else 'partial',voteBasis='Source-scoped chamber composition; no national popular-vote denominator',summary='Reported Council of States composition after the cantonal selection cycle.',notes='Council of States terms and election dates are governed by canton; there is no nationwide general renewal. This record is the referenced election-year composition, not a simultaneous nationwide ballot. Votes, shares and national turnout remain null. Year precision is intentional and January 1 is only a sorting anchor. Historical group classifications follow this source rather than later party affiliation. Any mandates not accounted for by its table remain unassigned.',_valid=None)
  s.pop('electionMethod',None);s['sources'].append(dict(label='Parliament: historical cantonal electoral systems',url=STATES_METHOD));records.append(s)

# Annual presidency: a chair among seven equals, not a separately elected head of state.
for p in PRIMARY['presidents']:
 term=int(p['term'][:4]);selection_year=1848 if term==1848 else term if term in (1870,1881) else term-1
 date=f'{selection_year}-01-01';precision='year'
 if term==2026:date='2025-12-10';precision='day'
 if term in (2000,2004,2008,2012,2016,2020,2024):
  dates={2000:'1999-12-15',2004:'2003-12-10',2008:'2007-12-12',2012:'2011-12-14',2016:'2015-12-09',2020:'2019-12-11',2024:'2023-12-13'};date=dates[term];precision='day'
 e=base(date,'president',p['source'],precision);e['id']=f'world-switzerland-president-for-{str(p["term"]).replace("/","-")}';e['title']='President of the Confederation — '+p['term']
 e.update(electionMethod='indirect',round='Annual Federal Assembly selection',resultStatus='final',voteBasis='Votes received by the elected president; other ballots/denominator not fully entered',summary=p['name']+' was selected to chair the Federal Council for '+p['term']+'.',notes='The United Federal Assembly selects the president annually from the seven Federal Councillors. The Federal Council collectively performs head-of-state functions; this presidency is a one-year chairmanship, not a popular election of a separate head of state. Only the documented elected candidate’s vote count is entered. Other ballots, blanks, turnout and vote share remain null, so numerical coverage is partial. The scholarly table’s percentage of assembly membership is not reused as a percentage of valid ballots. Historical selections normally occurred in the preceding year; where the exact day is unverified only year precision is used, with January 1 a sorting anchor. ',_valid=None)
 if term<=1903:
  party='Historical '+p['party']+' group (initial Federal Council affiliation)';e['notes']+='For these early entries the historical source labels affiliation at the initial Federal Council election, not necessarily at the later presidential selection; the label’s scope is retained explicitly. '
 else:party=abbreviation(p['party'],selection_year)
 result(e,p['name'],p['votes'],party=party)['winner']=True
 if term in (1870,1881):e.update(startDate='',precision='unknown',dateStatus='tba');e['notes']+='This is the replacement selection after the originally elected president died before assuming the presidential office. Its exact selection date is not verified and remains unknown; the title identifies the presidential term, not the polling date. '
 if term==2026:e['sources'].append(dict(label='Parliament: election on 10 December 2025 for the 2026 presidency',url='https://www.parlament.ch/fr/services/news/Pages/2025/20251210125032947194158159026_bsf112.aspx'))
 records.append(e)
for term,name,votes in [(1870,'Victor Ruffy',121),(1881,'Fridolin Anderwert',101)]:
 e=base(f'{term-1}-01-01','president','https://www.parlament.ch/centers/documents/_layouts/15/DocIdRedir.aspx?ID=DOCID-1-10236','year');e['id']=f'world-switzerland-president-for-{term}-original'
 e.update(title=f'President of the Confederation — {term}, elected but did not take office',electionMethod='indirect',round='Original selection',resultStatus='final',voteBasis='Documented votes for the elected candidate; remaining ballots not entered',summary=name+' was elected but died before assuming the presidential office.',notes='The historical source explicitly records this original selection separately from the replacement shown in its main presidency table. The candidate was elected, but did not serve the upcoming presidential term. Only the documented vote count is entered; exact polling day, other ballots, turnout and percentages remain unverified. Year precision is intentional; January 1 is only a sorting anchor.',_valid=None)
 result(e,name,votes,party='Historical radical group (initial Federal Council affiliation)')['winner']=True;records.append(e)

# Federal Council renewals: collective executive elections, with independent
# seat ballots kept separately and never summed into a popular vote share.
COUNCIL=json.loads((OUT/'council-ballots.json').read_text())
WINNER_PARTY={'Adolf Ogi':'SVP','Kaspar Villiger':'FDP','Ruth Dreifuss':'SP','Moritz Leuenberger':'SP','Pascal Couchepin':'FDP','Ruth Metzler':'CVP','Joseph Deiss':'CVP','Christoph Blocher':'SVP','Samuel Schmid':'SVP','Micheline Calmy-Rey':'SP','Hans-Rudolf Merz':'FDP','Doris Leuthard':'CVP','Didier Burkhalter':'FDP','Simonetta Sommaruga':'SP','Johann Schneider-Ammann':'FDP','Alain Berset':'SP','Guy Parmelin':'SVP','Ueli Maurer':'SVP','Ignazio Cassis':'FDP','Viola Amherd':'CVP','Karin Keller-Sutter':'FDP','Albert Rösti':'SVP','Élisabeth Baume-Schneider':'SP','Beat Jans':'SP','Martin Pfister':'Mitte','Markus Ritter':'Mitte'}
def council_party(c,year):
 if c['party']:return canonical(abbreviation(c['party'],year))
 if c['name']=='Eveline Widmer-Schlumpf':return abbreviation('SVP' if year==2007 else 'BDP',year)
 return abbreviation(WINNER_PARTY[c['name']],year) if c['name'] in WINNER_PARTY else 'Affiliation not verified'
for e in list(records):
 if e['seriesId']!='ch-national-council':continue
 year=int(e['startDate'][:4]);source=next((x for x in COUNCIL if x['year']==year),None)
 date=source['date'] if source else f'{year}-01-01';p=base(date,'federal-council',source['source'] if source else COUNCIL_METHOD,'day' if source else 'year')
 p.update(electionMethod='indirect',round='General renewal',title='Federal Council — general renewal',summary='The Federal Assembly selected the seven-member collective executive after the National Council renewal.',notes='The Federal Council is Switzerland’s seven-member government and collective head of state. The United Federal Assembly elects each seat separately; this is not a nationwide popular presidential ballot. General renewals follow the National Council renewal. Historic polling days, all candidates and individual ballot counts are not inferred where unverified. ',_valid=None)
 if source:
  p.update(totalSeats=7,resultStatus='final',resultCoverage='partial',voteBasis='Seven elected members; winning counts from separate seat ballots, not a shared denominator')
  for slot,co in enumerate(source['contests'],1):
   winner=next(c for c in co['candidates'] if c['party']!='Unattributed ballots' and (c['votes'][-1] or 0)>co['validVotes'][-1]/2)
   result(p,winner['name'],winner['votes'][-1],seats=1,party=council_party(winner,year))['winner']=True
   for ri,valid in enumerate(co['validVotes']):
    b=base(date,'federal-council',source['source']);b['id']=p['id']+f'-seat-{slot}-ballot-{ri+1}';b['seriesId']='ch-federal-council-ballots';b.update(title='Federal Council — '+co['label'],body='Federal Council — seat '+str(slot),round=f'Ballot {ri+1}',electionMethod='indirect',totalSeats=None,resultStatus='final',resultCoverage='complete',voteBasis=f'Candidate votes / {valid} valid ballots for this seat and this ballot',summary='Separate Federal Assembly ballot for one Federal Council seat.',notes='This is one seat ballot, not a popular presidential election or a national party vote. The absolute-majority threshold is calculated from valid ballots. No winner is marked until a named candidate obtains more than half; votes for unspecified others are retained as an unattributed aggregate and cannot be treated as an elected individual. Candidate affiliations are entered where the source identifies them; otherwise they remain explicitly unverified. Different seats and rounds have separate denominators.',_valid=valid,overviewId=p['id'])
    for c in co['candidates']:
     if c['votes'][ri] is None:continue
     r=result(b,c['name'],c['votes'][ri],round(c['votes'][ri]/valid*100,6),party=council_party(c,year))
     if c['party']!='Unattributed ballots' and c['votes'][ri]>valid/2:r.update(winner=True)
    records.append(b)
  p['notes']+='The seven winning candidate counts are a partial numerical summary across separate seat elections. Full candidate rows for every source ballot are linked as separate records, including ballots without a majority. '
 records.append(p)

# Latest replacement election, with both rounds and the winning seat distinct.
source=next(x for x in COUNCIL if x['year']==2025);p=base(source['date'],'federal-council',source['source']);p.update(title='Federal Council — replacement of Viola Amherd',round='Replacement election',electionMethod='indirect',totalSeats=1,resultStatus='final',voteBasis='Winning candidate count; full separate ballots linked',summary='Martin Pfister was elected to replace Viola Amherd.',notes='This election selected one member of the seven-member collective executive, not a president or a nationwide government renewal. The linked first and second ballots have separate valid-ballot denominators.',_valid=None)
co=source['contests'][0];winner=next(c for c in co['candidates'] if (c['votes'][-1] or 0)>co['validVotes'][-1]/2);result(p,winner['name'],winner['votes'][-1],seats=1,party=council_party(winner,2025))['winner']=True
for ri,valid in enumerate(co['validVotes']):
 b=base(source['date'],'federal-council',source['source']);b['id']=p['id']+f'-ballot-{ri+1}';b['seriesId']='ch-federal-council-ballots';b.update(title='Federal Council — replacement of Viola Amherd',round=f'Ballot {ri+1}',electionMethod='indirect',totalSeats=None,resultStatus='final',resultCoverage='complete',voteBasis=f'Candidate votes / {valid} valid ballots in this seat ballot',summary='Separate ballot for the Federal Council vacancy.',notes='The first ballot produced no absolute majority. Martin Pfister was elected in the second. Candidate vote shares use each ballot’s 245 valid ballots; unattributed other votes remain a separate aggregate.',overviewId=p['id'],_valid=valid)
 for c in co['candidates']:
  v=c['votes'][ri]
  if v is None:continue
  r=result(b,c['name'],v,round(v/valid*100,6),party=council_party(c,2025))
  if c['party']!='Unattributed ballots' and v>valid/2:r.update(winner=True)
 records.append(b)
records.append(p)

# Preserve already published Calendar IDs; no duplicate upcoming contests.
e=base('2026-12-09','federal-council','https://svp-sh.ch/artikel/guy-parmelin-tritt-zurueck-die-svp-kanton-schaffhausen-dankt/')
e.update(status='scheduled',dateStatus='expected',title='Federal Council — planned replacement of Guy Parmelin',round='Replacement election',electionMethod='indirect',totalSeats=1,summary='A replacement election is planned following Guy Parmelin’s announced retirement at the end of 2026.',notes='The cantonal SVP announcement reports the replacement election as planned for 9 December 2026. This is retained as an expected date, not promoted to an officially confirmed polling announcement. Guy Parmelin announced his retirement effective 31 December 2026; his election to the presidency for 2026 remains historical and valid. No successor or election results are invented.',_valid=None)
e['sources'].append(dict(label='SVP: Parmelin’s retirement and intended candidacy in the replacement election',url='https://www.svp.ch/aktuell/publikationen/medienmitteilungen/ein-bundesrat-fuer-die-schweiz-die-svp-dankt-guy-parmelin-fuer-seinen-grossartigen-einsatz-zum-wohl-unseres-landes/'));records.append(e)
BACKUP=json.loads((OUT/'pre-import-backup.json').read_text())
for row in BACKUP:
 if row['kind']=='world_election':e=row['data'];e['_valid']=None;records.append(e)
for office in ('federal-council','president'):
 e=base('2027-12-15',office,CALENDAR);e.update(status='scheduled',summary='Confirmed indirect national election on 15 December 2027.',round='General renewal' if office=='federal-council' else 'Annual selection for 2028',electionMethod='indirect',voteBasis='Separate United Federal Assembly ballots; results not yet available',notes='The official Parliament calendar confirms 15 December 2027 for the full Federal Council renewal and selection of the President and Vice President. This record has no invented candidates, results or winner.',_valid=None)
 if office=='federal-council':e['totalSeats']=7
 else:e['title']='President of the Confederation — selection for 2028'
 records.append(e)

for e in records:
 if e['id'] in ('world-switzerland-president-for-1870','world-switzerland-president-for-1881','world-switzerland-president-for-1870-original','world-switzerland-president-for-1881-original'):
  peer=e['id'].removesuffix('-original') if e['id'].endswith('-original') else e['id']+'-original';e['linkedElectionIds']=[peer]
 if e.get('overviewId'):
  peers=[x['id'] for x in records if x.get('overviewId')==e['overviewId'] and x['id']!=e['id'] and x['body']==e['body']];e['linkedElectionIds']=[e['overviewId'],*peers]
 elif e['seriesId']=='ch-federal-council':
  peers=[x['id'] for x in records if x.get('overviewId')==e['id']]
  if peers:e['linkedElectionIds']=peers
 elif e['seriesId'] in ('ch-national-council','ch-states'):
  peers=[x['id'] for x in records if x['seriesId'] in ('ch-national-council','ch-states') and x['id']!=e['id'] and x['startDate'][:4]==e['startDate'][:4]]
  if peers:e['linkedElectionIds']=peers
 reconcile(e,e.pop('_valid'))
 assert sum(r['share'] or 0 for r in e['results'])<=100.2,e['id']
 if e['totalSeats'] is not None:assert sum(r['seats'] or 0 for r in e['results'])<=e['totalSeats'],e['id']
records.sort(key=lambda e:(e['startDate'],e['body'],e['id']))
used={r['partyId'] for e in records for r in e['results'] if 'partyId' in r};profiles={k:p for k,p in profiles.items() if p['id'] in used}
for name,obj in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('Built',len(records),'records;',len(profiles),'profiles. Series:',{s:len([e for e in records if e['seriesId']==s]) for s in sorted({e['seriesId'] for e in records})});print('Partial results:',len([e for e in records if e['results'] and e['resultCoverage']=='partial']));print('Missing results:',len([e for e in records if e['status']=='held' and not e['results']]))
