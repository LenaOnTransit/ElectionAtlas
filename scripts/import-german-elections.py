"""Rebuild sourced German Reichstag/Bundestag archive records; does not publish."""
from pathlib import Path
import json,re,csv,subprocess,concurrent.futures,hashlib,uuid
from us_presidential_html import read,expand
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/germany';CACHE.mkdir(parents=True,exist_ok=True)
SOURCES={
 'bundestag.csv':'https://www.bundeswahlleiterin.de/dam/jcr/24d8e745-920d-431a-893a-12805bc7ef40/btw_ab49_datenbank_ergebnisse.csv',
 'bundestag.pdf':'https://www.bundeswahlleiterin.de/dam/jcr/397735e3-0585-46f6-a0b5-2c60c5b83de6/btw_ab49_gesamt.pdf',
 'imperial.html':'https://germanhistorydocs.org/en/forging-an-empire-bismarckian-germany-1866-1890/elections-to-the-german-reichstag-1871-1890-a-statistical-overview',
 'imperial-late.html':'https://germanhistorydocs.org/en/wilhelmine-germany-and-the-first-world-war-1890-1918/elections-to-the-reichstag-1890-1912',
 'imperial-detail.html':'https://www.wahlen-in-deutschland.de/krtw.htm',
 'weimar.html':'https://www.wahlen-in-deutschland.de/wrtw.htm',
 'weimar-kas.html':'https://www.kas.de/de/web/geschichte-der-cdu/wahlen-zum-reichtag-in-der-weimarer-republik-1919-1933-',
}
def fetch(pair):
 name,url=pair;p=CACHE/name
 if not p.exists():subprocess.run(['curl','-fsSL','--retry','1','--max-time','60',url,'-o',str(p)],check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:list(pool.map(fetch,SOURCES.items()))
if not (CACHE/'bundestag.txt').exists():subprocess.run(['pdftotext','-layout',str(CACHE/'bundestag.pdf'),str(CACHE/'bundestag.txt')],check=True)

CHECKED='2026-10-06'
OUT=ROOT/'scripts/german-election-import';OUT.mkdir(parents=True,exist_ok=True)
records=[];parties={}
def table(file):return [[[c['text'].replace('\xad','') for c in r] for r in expand(t)] for t in read(CACHE/file)]
def integer(s):
 s=s.strip().replace('.','').replace(' ','')
 return int(s) if s.isdigit() else 0
def source(label,url):return {'label':label,'url':url}
COLORS={'Social Democratic parties':'#e3000f','Other liberals':'#d3b94a','German-Hanoverian Party':'#e0b431','Catholic clerical groups':'#333333','SPD':'#e3000f','CDU':'#151518','CSU':'#008ac5','FDP':'#ffcc00','GRÜNE':'#64a12d','BÜNDNIS 90/DIE GRÜNEN':'#64a12d','DIE LINKE':'#be3075','PDS':'#be3075','AfD':'#009ee0','BSW':'#792351','NSDAP':'#b40000','KPD':'#d60000','USPD':'#b52b3a','Zentrum':'#333333','BVP':'#4678a3','National liberals':'#d6b63f','Left liberals':'#e8cc51','Conservatives':'#25456b','DRP / Free Conservatives':'#446084','DNVP':'#25456b','DVP':'#d6b63f','DDP':'#e8cc51','DStP':'#e8cc51'}
def result(e,key,name,votes,share,seats,save=True):
 color=COLORS.get(key,'#808080');pid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/de/'+key))
 ids=[]
 if key in ['NSDAP']:ids=['ideology-national-socialism']
 if key in ['CDU','CSU']:ids=['ideology-christian-democracy']
 if key=='SPD' and int(e['startDate'][:4])>=1961:ids=['ideology-social-democracy']
 if key in ['KPD']:ids=['ideology-marxism-leninism']
 if key in ['GRÜNE','BÜNDNIS 90/DIE GRÜNEN']:ids=['ideology-green-politics']
 r={'id':e['id']+'-'+str(len(e['results'])+1),'name':name,'party':key,'color':color,'votes':votes,'share':share,'seats':seats,'electoralVotes':None,'winner':False,'ideologyIds':ids}
 if save:
  r['partyId']=pid
  parties[pid]={'id':pid,'country_id':'de','name':name,'short_name':key[:100],'color':color,'ideology_ids':[], 'notes':'German archive party/list label. Election records retain their period-specific classifications; no present-day ideology is backfilled into historical elections.','archived':False}
 e['results'].append(r)
 return r

def election(date,title,body,seats,turnout,sources,notes='',coverage='complete'):
 e={'id':'world-germany-'+date+'-'+('bundestag' if body=='Bundestag' else 'reichstag'),'countryId':'de','title':title,'type':'parliamentary','body':body,'startDate':date,'endDate':'','precision':'day','dateStatus':'confirmed','status':'held','publication':'published','round':'General','seriesId':'DE-BT' if body=='Bundestag' else 'DE-RT','snap':False,'summary':'','government':'','turnout':turnout,'totalSeats':seats,'resultStatus':'final','resultCoverage':coverage,'voteBasis':'Share of valid votes','results':[],'sources':sources,'checked':CHECKED,'notes':notes,'articleId':'','version':1,'electionMethod':'direct'}
 records.append(e);return e

# National list votes and full chamber composition, including indirectly selected
# West Berlin representatives. 1949 had one ballot, not two votes.
a=list(csv.reader((CACHE/'bundestag.csv').open(encoding='utf-8-sig'),delimiter=';'))
years=sorted({int(r[1]) for r in a if len(r)>1 and r[1].isdigit()})
dates=['1949-08-14','1953-09-06','1957-09-15','1961-09-17','1965-09-19','1969-09-28','1972-11-19','1976-10-03','1980-10-05','1983-03-06','1987-01-25','1990-12-02','1994-10-16','1998-09-27','2002-09-22','2005-09-18','2009-09-27','2013-09-22','2017-09-24','2021-09-26','2025-02-23']
assert len(years)==len(dates)==21
for year,date in zip(years,dates):
 rows=[r for r in a if len(r)>1 and r[1]==str(year)];by={r[0]:r for r in rows}
 total=by['gültige Stimmen/Sitze insgesamt'];valid=integer(total[4]);seats=integer(total[79])
 notes='Final national results from the Federal Returning Officer. '+('West German electoral territory; the Federal Republic continues in the Germany archive. Seat totals include indirectly selected West Berlin representatives, who did not cast national ballots. Saarland first participated in 1957. ' if year<1990 else 'The 1990 election was the first Bundestag election covering reunified Germany; subsequent elections continue the Federal Republic series. ')
 notes+='Shares use '+('the single ballot in 1949. ' if year==1949 else 'second (party-list) votes, not constituency first votes. ')
 notes+='Official abbreviations are retained for small lists. Parties or independent candidates with only first votes have no party-list vote figure. Independent/other constituency nominations are grouped as in the official source. '
 if year==2021:notes+='The source incorporates the repeat election in parts of Berlin held on 11 February 2024. '
 e=election(date,('West Germany — ' if year<1990 else '')+'Bundestag','Bundestag',seats,float(by['Wählende'][6].replace(',','.')), [source('Federal Returning Officer: national votes and seats since 1949 (2026 edition)',SOURCES['bundestag.csv']),source('Federal Returning Officer: historical election dates and explanatory notes',SOURCES['bundestag.pdf'])],notes)
 e['voteBasis']=('Single-ballot votes' if year==1949 else 'Second (party-list) votes')+f'; {valid:,} valid votes'
 e['snap']=year in [1972,1983,2005,2025]
 for r in rows[4:]:
  v=integer(r[4]) if r[4].strip() not in ['–','-',''] else None;s=integer(r[79])
  if v is None and not s and not integer(r[3]):continue
  key=r[0];result(e,key,key,v,round(v/valid*100,4) if v is not None else None,s,save=key!='Andere KWV')
 assert sum(r['votes'] or 0 for r in e['results'])==valid,(year,'votes')
 assert sum(r['seats'] for r in e['results'])==seats,(year,'seats')
 e['summary']=f"{max(e['results'],key=lambda r:r['votes'] or 0)['name']} received the largest share of national votes. The full chamber contained {seats} members."

# Historical series from a consistent published table. Its party groups are
# explicitly retained, rather than assigning all votes to one member of a bloc.
it=table('imperial-detail.html');shares={r[0]:r for r in it[0][1:] if r[0]};seatrows={r[0]:r for r in it[1][1:] if r[0]}
labels=['Social Democratic parties','Left liberals','Other liberals','National liberals','Zentrum','DRP / Free Conservatives','Conservatives','Agrarian parties','German-Hanoverian Party','Other conservatives','Antisemitic parties','Minority parties','Other lists']
for vr in it[2][1:]:
 if not vr[0] or vr[0]=='27.04.1868':continue # Zollparlament, not Reichstag
 d,m,y=vr[0].split('.');date='1878-07-30' if vr[0]=='30.06.1878' else f'{y}-{m}-{d}';sr=seatrows[vr[0]];valid=integer(vr[16]);total=integer(sr[13])
 turnout=round(integer(vr[15])/integer(vr[14])*100,2) if integer(vr[14]) else None
 title=('North German Confederation — '+('Constituent ' if m=='02' else '')+'Reichstag') if y=='1867' else 'German Empire — Reichstag'
 notes='First-round popular votes and seat distribution from the historical source; elections used single-member constituencies with runoff ballots. Party families and minority groups are aggregated exactly as in the source, not presented as individual parties. Historical boundaries differ from present-day Germany. Voting was restricted to eligible men aged 25 and over. The imperial government was appointed by the monarch, rather than elected by parliamentary majority. '
 if y=='1878':notes+='The result table misprints the month as June; the election date is corrected to 30 July 1878 using the German Historical Museum’s dated election artefact. '
 if y=='1867':notes+='This is a North German Confederation precursor, not an election of the German Empire. Turnout is unavailable in the source. '
 e=election(date,title,'Constituent Reichstag' if y=='1867' and m=='02' else 'Reichstag',total,turnout,[source('Wahlen in Deutschland: Reichstag elections, national votes and seat tables',SOURCES['imperial-detail.html']),source('German Bundestag: imperial electoral system and party development','https://www.bundestag.de/parlament/geschichte/parlamentarismus/kaiserreich')],notes)
 if y=='1878':e['sources'].append(source('German Historical Museum: Reichstag election, 30 July 1878','https://www.dhm.de/lemo/bestand/objekt/reichstagswahl-30-juli-1878'))
 for j,name in enumerate(labels,1):
  if y=='1867' and name=='Zentrum':name='Catholic clerical groups'
  v=integer(vr[j]);s=integer(sr[j]) if j<=12 else 0
  if v or s:result(e,name,name,v,round(v/valid*100,4),s,save=name in ['Zentrum','German-Hanoverian Party','DRP / Free Conservatives'])
 assert sum(r['votes'] for r in e['results'])==valid
 assert sum(r['seats'] for r in e['results'])==total
 e['voteBasis']=f'First-round valid votes ({valid:,}); historical party groups'
 e['summary']=f"{title}; {total} seats. Results retain the source’s historical party groupings."

wt=table('weimar.html');ss={r[0]:r for r in wt[1][1:] if r[0]};pp={r[0]:r for r in wt[0][1:] if r[0]}
labels=['KPD','USPD','Other left parties','SPD','DDP','Zentrum','BVP','DVP','DNVP','Agrarian parties','Middle-class parties','Other right parties','NSDAP','National minority lists','Other lists']
# 1920 and May 1924 use completed nationwide results after territorial
# supplementary elections; the record date remains the general election date.
selected=['19.01.1919','19.11.1922','21.09.1924','07.12.1924','20.05.1928','14.09.1930','31.07.1932','06.11.1932','05.03.1933']
for vr in wt[2][1:]:
 if vr[0] not in selected:continue
 key=vr[0];actual={'19.11.1922':'06.06.1920','21.09.1924':'04.05.1924'}.get(key,key);d,m,y=actual.split('.');date=f'{y}-{m}-{d}';sr=ss[key];valid=integer(vr[18]);total=integer(sr[20]);notes='Historical national results use the source’s consistent party allocation, including separately tabulated Bavarian and regional lists; these can differ from tables that assign joint lists to the larger partner. Farmers, middle-class, other right-wing and minority groups remain aggregated as published. '
 if y=='1919':notes+='Turnout is approximately 83% in the historical source. The National Assembly elected a constitution, rather than a regular Reichstag. The final 423-member composition includes the two additional SPD members from the eastern-army supplementary vote; the initial elected chamber had 421 members. '
 if key=='19.11.1922':notes+='Results incorporate territorial supplementary elections of 20 February 1921 and 19 November 1922; this is the completed result of the 6 June 1920 general election, not a separate nationwide election. '
 if key=='21.09.1924':notes+='Results incorporate the supplementary vote of 21 September 1924. '
 if key=='07.12.1924':notes+='The published party totals fall 779 votes short of its valid-vote denominator. Those 779 votes are explicitly retained as an unallocated source discrepancy; they are not assigned to a party. '
 if y=='1933':notes+='Voting took place under Nazi terror, political repression and restrictions on opposition campaigning; this was not a free and fair election. '
 e=election(date,'Weimar National Assembly' if y=='1919' else 'Reichstag', 'National Assembly' if y=='1919' else 'Reichstag',total,83.0 if y=='1919' else float(pp[key][16].replace(',','.')),[source('Wahlen in Deutschland: Weimar party votes, seats and territorial supplements',SOURCES['weimar.html']),source('German Bundestag: Weimar National Assembly and supplementary eastern-army election','https://www.bundestag.de/dokumente/textarchiv/1919-02-06-weimarer-nationalversammlung-590072')],notes)
 seatmap={1:[1],2:[2],3:[],4:[3],5:[4],6:[5],7:[6],8:[7],9:[8],10:[9,10,11],11:[12,13],12:[14,15,16,17,18],13:[19],14:[],15:[]}
 for j,name in enumerate(labels,1):
  v=integer(vr[j]);s=sum(integer(sr[k]) for k in seatmap[j]);name='DStP' if name=='DDP' and int(y)>=1930 else name
  if name=='NSDAP' and int(y)==1924:name='National Socialist–völkisch alliance'
  if v or s:result(e,name,name,v,round(v/valid*100,4),s,save=j not in [3,10,11,12,14,15] and 'alliance' not in name)
 missing=valid-sum(r['votes'] for r in e['results'])
 if missing:assert missing==779;result(e,'Unallocated source discrepancy','Unallocated source discrepancy',missing,round(missing/valid*100,4),0,False)
 assert sum(r['votes'] for r in e['results'])==valid
 assert sum(r['seats'] for r in e['results'])==total,(date,total)
 e['voteBasis']=f'Share of {valid:,} valid votes; territorial supplements included where noted'
 e['summary']=f"{e['title']}: {total} seats.";e['snap']=y!='1919'
 if y=='1933':e['legitimacy']={'level':'uncompetitive','summary':'The Nazi government used terror and suppressed opposition campaigning. The presence of several parties on the ballot did not make this a free election.','reviewed':CHECKED,'sources':[source('German Bundestag: National Socialism and parliamentary destruction','https://www.bundestag.de/parlament/geschichte/parlamentarismus/drittes_reich')]}

# Coerced single-list votes: approval is not a competitive party vote share.
for date,seats,turnout,votes,share,url in [
 ('1933-11-12',661,95.30,39655224,92.11,'https://en.wikipedia.org/wiki/November_1933_German_parliamentary_election'),
 ('1936-03-29',741,99.00,44462458,98.80,'https://en.wikipedia.org/wiki/1936_German_parliamentary_election_and_referendum'),
 ('1938-04-10',814,99.59,44451092,99.01,'https://sudd.ch/event.php?id=de011938&lang=de'),
 ('1938-12-04',41,98.61,2464681,98.90,'https://sudd.ch/event.php?id=cz011938&lang=de')]:
 supplement=date=='1938-12-04';notes='Coerced single-list ballot under the Nazi dictatorship. The only approved list consisted of NSDAP members and approved non-party guests; seats are list seats, not an assertion that every member belonged to the NSDAP. Published approval figures do not demonstrate democratic legitimacy. '
 if date=='1933-11-12':notes+='The Reichstag ballot is distinct from the simultaneous League of Nations referendum. 3,398,249 ballots were against the list; approval share uses all 43,053,473 ballots in this published table. '
 if date=='1936-03-29':notes+='The published table records 44,462,458 approvals and 540,244 ballots against out of 45,002,702 ballots; it does not separately tabulate invalid ballots. The approved list occupied 741 seats, including 19 non-party guests. Approval also covered the remilitarization of the Rhineland. '
 if date=='1938-04-10':notes+='The recorded vote and turnout figures cover the German Reich excluding Austria; 44,894,115 valid votes included 443,023 No votes. The 814-seat chamber included Austrian representatives, so this record has partial vote coverage. This ballot also asked approval of the annexation of Austria. '
 if supplement:notes+='Supplementary election in the annexed Sudeten territory, not a new nationwide election: 41 additional mandates enlarged the 814-member chamber to 855. Of 2,492,108 valid ballots, 27,427 were No votes. '
 e=election(date,'Reichstag — '+('Sudeten supplementary single-list vote' if supplement else 'single-list approval vote'),'Reichstag',seats,turnout,[source('Published historical ballot totals and composition',url),source('German Bundestag: Nazi-era sham parliament','https://www.bundestag.de/parlament/geschichte/parlamentarismus/drittes_reich')],notes,'partial')
 result(e,'NSDAP-led single list','NSDAP and approved guests — single list',votes,share,seats,False)
 e['results'][0]['color']='#b40000';e['voteBasis']='Published approval of the sole permitted list; not competitive party vote share'
 e['summary']='Only one approved list was permitted; this was an uncompetitive ballot under the Nazi dictatorship.'
 e['legitimacy']={'level':'uncompetitive','summary':e['summary'],'reviewed':CHECKED,'sources':[e['sources'][1]]}
 if supplement:e['geography']={'id':'sudeten-annexed-1938','name':'Annexed Sudeten territory','type':'province'};e['round']='Territorial supplementary election'

records.sort(key=lambda e:e['startDate'])
assert len(records)==49
for e in records:
 assert sum(r['seats'] or 0 for r in e['results'])==e['totalSeats'],e['id']
 assert len(e['results'])==len({r['id'] for r in e['results']})
 for r in e['results']:
  if r.get('partyId'):assert r['partyId'] in parties
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'parties.json').write_text(json.dumps(list(parties.values()),ensure_ascii=False,indent=2)+'\n')
(OUT/'source-audit.json').write_text(json.dumps({'checked':CHECKED,'recordCount':len(records),'partyCount':len(parties),'sources':[{'url':url,'cacheFile':name,'sha256':hashlib.sha256((CACHE/name).read_bytes()).hexdigest()} for name,url in SOURCES.items()]},indent=2)+'\n')
print(f'Built {len(records)} records and {len(parties)} saved party/list labels; all seat totals reconciled.')
