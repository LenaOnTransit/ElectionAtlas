"""Build a reviewed calendar patch; never publishes or overwrites records."""
from pathlib import Path
import json,re,hashlib
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/calendar';OUT=ROOT/'scripts/calendar-2027-import';OUT.mkdir(exist_ok=True)
inv=json.loads((CACHE/'inventory.json').read_text());existing=inv['upcoming'];patches={};audit=[]
COUNTRIES={c['name']:c['id'] for c in inv['countries']}
COUNTRIES.update({'Czech Republic':'cz','United States of America':'us','Gambia, The':'gm','Palestinian Territories':'ps','Virgin Islands, U.S.':'vi','Guam':'gu','American Samoa':'as','Northern Mariana Islands':'mp'})
def base(cid,title,typ,date,url,notes='',round='General',method='direct',id=None,end=''):
 return dict(id=id or f'world-calendar-{cid}-{re.sub("[^a-z0-9]+","-",title.lower()).strip("-")}-{date[:4]}',countryId=cid,title=title,type=typ,body=title,startDate=date,endDate=end,precision='day',dateStatus='confirmed',status='scheduled',publication='published',round=round,seriesId=f'{cid}-{date[:4]}-{typ}',snap=False,summary='Scheduled national election.' if typ!='gubernatorial' else 'Scheduled territorial executive election.',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='National vote share' if method=='direct' else 'Electoral college votes',results=[],sources=[dict(label='Election schedule / announcement',url=url)],checked='2026-10-08',notes=notes,articleId='',version=0,electionMethod=method)
def add(e):
 matches=[r for r in existing if r['countryId']==e['countryId'] and r['title']==e['title'] and r['startDate'][:4]==e['startDate'][:4]]
 if matches:
  assert len(matches)==1,matches
  old=matches[0]
  if old['startDate']==e['startDate'] and old['precision']=='day' and old['dateStatus']=='confirmed':return
  nxt=old.copy();nxt.update(startDate=e['startDate'],endDate=e['endDate'],precision='day',dateStatus='confirmed',checked=e['checked'],version=old['version']+1)
  nxt['sources']=old['sources']+[s for s in e['sources'] if s not in old['sources']];nxt['notes']=old['notes']+'\n'+e['notes'];patches[old['id']]=dict(action='update',before=old,after=nxt)
 else:patches[e['id']]=dict(action='insert',after=e)
# Every confirmed executive/legislative election in IFES' full 2027 search and upcoming list.
for file in ['ifes-upcoming.html','ifes2027.html']:
 s=BeautifulSoup((CACHE/file).read_text(),'html.parser')
 for tr in s.select('table tr'):
  c=tr.select('td')
  if len(c)<7 or c[5].get_text(strip=True)!='Confirmed':continue
  a=c[2].select_one('a');name=a.get_text(' ',strip=True)
  if name=='Referendum':continue
  date=c[3].get_text(strip=True)[:10];end=c[4].get_text(strip=True)[:10]
  if not '2026-10-08'<=date<='2027-12-31':continue
  country=c[1].get_text(' ',strip=True);cid=COUNTRIES[country]
  typ='gubernatorial' if 'Governor' in name else 'presidential' if 'Presidency' in name else 'parliamentary'
  title='Governor' if typ=='gubernatorial' else 'President' if typ=='presidential' else next((t for t in ['House of Representatives','Congress of Deputies','Legislative Council','Senate','Legislature'] if t in name), 'Riigikogu' if cid=='ee' else 'Knesset' if cid=='il' else 'House of Representatives' if cid=='nz' else 'National Assembly' if cid=='rs' else 'Chamber of Deputies' if cid=='ht' else 'President')
  url='https://www.electionguide.org'+a['href'].split('?')[0]
  e=base(cid,title,typ,date,url,'IFES lists this contest as confirmed. The declared schedule was checked on 8 October 2026; future changes remain possible.',end=end if end!=date else '')
  e['snap']=c[6].get_text(strip=True)=='Yes';add(e);audit.append(dict(countryId=cid,title=title,date=date,url=url,decision='already confirmed' if not any(p['after']['countryId']==cid and p['after']['title']==title for p in patches.values()) else 'include'))
# Primary / official sources take precedence over a tentative listing.
add(base('kg','President','presidential','2027-01-27','https://www.aa.com.tr/en/eurasia/kyrgyz-parliament-adopts-draft-resolution-on-holding-presidential-vote-on-jan-27/4067521','Parliament set 27 January 2027 in its 24 September 2026 resolution. This supersedes earlier references to 24 January.'))
add(base('sv','Legislative Assembly','parliamentary','2027-02-28','https://tse.gob.sv/docs/calendarios/CALENDARIO-TSE-NACIONAL.pdf','TSE national calendar, activity 163, sets presidential and legislative election day to 28 February 2027.'))
add(base('sv','President','presidential','2027-02-28','https://tse.gob.sv/docs/calendarios/CALENDARIO-TSE-NACIONAL.pdf','TSE national calendar, activity 163, sets presidential and legislative election day to 28 February 2027.'))
add(base('fm','Congress','parliamentary','2027-03-02','https://www.cfsm.gov.fm/24th-resolutions/','Congress resolution CR 24-175 (21 September 2026) identifies the 2 March 2027 national election.'))
add(base('gm','National Assembly','parliamentary','2027-04-10','https://iec.gm/electoral-calendar-2026-2027/','IEC electoral calendar, section III, specifies election day on 10 April 2027.'))
add(base('fi','Parliament','parliamentary','2027-04-18','https://vaalit.fi/en/schedule-in-the-parliamentary-elections','The Ministry of Justice schedule specifies Sunday 18 April 2027 as election day.'))
add(base('de','Federal President','presidential','2027-01-30','https://www.bundestag.de/presse/pressemitteilungen/2026/pm-260226-bundesversammlung-1150358','The Bundestag President convened the Federal Convention for 30 January 2027. This is an indirect election, not a popular presidential ballot.',method='indirect'))
add(base('gd','House of Representatives','parliamentary','2026-11-05','https://nowgrenada.com/2026/10/grenadians-vote-for-a-new-government-on-5-november/','The prime minister announced polling for 5 November 2026 following dissolution and issue of writs in October.',round='General'))
add(base('bi','President','presidential','2027-05-03','https://abpinfo.bi/2026/05/11/la-ceni-fixe-au-3-mai-2027-la-date-du-scrutin-de-lelection-presidentielle/','The public press agency records the CENI announcement of 3 May 2027. Only the announced first round is entered.',round='First round'))
add(base('mx','Chamber of Deputies','parliamentary','2027-06-06','https://portal.ine.mx/','INE identifies 6 June as the next election day. This record covers the federal Chamber of Deputies election.'))
for title,typ in [('President','presidential'),('National Assembly','parliamentary'),('Senate','parliamentary')]:add(base('ke',title,typ,'2027-08-10','https://www.iebc.or.ke/uploads/resources/tpFfOlBLRh.pdf','IEBC Election Operations Plan 2025–2027 sets the general election for 10 August 2027.'))
for title in ['National Council','Council of States']:add(base('ch',title,'parliamentary','2027-10-24','https://ch-info.swiss/fr/direkte-demokratie/wahlen','The official Confederation guide sets 24 October 2027. Council of States dates are governed by canton; almost all vote on this day, with exceptions and possible runoffs. This is a national calendar overview.'))
add(base('ch','President of the Confederation','presidential','2026-12-09','https://www.ch-info.swiss/fr/die-regierung/mitglieder-des-bundesrats','The annual presidential and vice-presidential selection is by the United Federal Assembly, not a popular ballot.',method='indirect'))
add(base('cz','Senate','parliamentary','2026-10-16','https://www.velkepritocno.cz/urad-2/volby/','Second-round voting takes place only in constituencies where no candidate wins a majority in the first round. Dates are announced; whether a constituency requires a runoff is conditional.',round='Runoff, if required',id='world-calendar-cz-senate-2026-runoff',end='2026-10-17'))
# The first-round Senate entry already exists; add() normally matches by office/year,
# so the explicitly separate runoff must be inserted without altering its first round.
patches.pop('world-czech-senate-2026',None)
e=base('cz','Senate','parliamentary','2026-10-16','https://www.velkepritocno.cz/urad-2/volby/','Second round only where no first-round majority is reached. Announced dates are conditional on a runoff being required.',round='Runoff, if required',id='world-calendar-cz-senate-2026-runoff',end='2026-10-17');patches[e['id']]=dict(action='insert',after=e)
# Add stronger official evidence to the two Spanish entries just discovered.
for p in patches.values():
 e=p['after']
 if e['countryId']=='es':e['sources'].append(dict(label='Official decree: Real Decreto 806/2026',url='https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-20742'));e['notes']+=' Official decree calls both chambers for 29 November 2026.'
# CEP says campaigning is postponed and a revised calendar is forthcoming; polling dates cannot be reconfirmed.
patches={id:p for id,p in patches.items() if p['after']['countryId']!='ht'}
for row in audit:
 if row['countryId']=='ht':row['decision']='excluded pending revised CEP calendar'
for old in existing:
 if old['countryId']!='ht':continue
 nxt=old.copy();nxt.update(startDate='',endDate='',precision='unknown',dateStatus='tba',status='scheduled',checked='2026-10-08',version=old['version']+1)
 nxt['sources']=old['sources']+[dict(label='CEP: campaign postponed; revised calendar forthcoming (5 October 2026)',url='https://cephaiti.ht/notes-communiques/')];nxt['notes']=old['notes']+'\nThe CEP notice of 5 October postpones the campaign, extends candidate registration and says a revised electoral calendar will be published. Reports describe a wider electoral delay, while the primary notice specifically postpones campaigning. The former 13 December polling date cannot be reconfirmed against a revised calendar and is not displayed as a confirmed polling day.';patches[old['id']]=dict(action='update',before=old,after=nxt)
# Territories need country directory records so their calendar labels and filters resolve.
newcountries=[dict(id=cid,name=name,region=region,aliases='',coverageNote='Territorial legislature and executive elections; this entry does not imply sovereign statehood.') for cid,name,region in [('gu','Guam','Oceania'),('as','American Samoa','Oceania'),('mp','Northern Mariana Islands','Oceania'),('vi','U.S. Virgin Islands','Americas')] if cid not in {c['id'] for c in inv['countries']}]
patch=list(patches.values());patch.sort(key=lambda p:(p['after']['startDate'],p['after']['id']))
(OUT/'patch.json').write_text(json.dumps(dict(checked='2026-10-08',cutoff='2027-12-31',countries=newcountries,elections=patch),ensure_ascii=False,indent=2)+'\n')
(OUT/'coverage-audit.json').write_text(json.dumps(dict(checked='2026-10-08',ifesConfirmed=audit,sourceHashes={f:hashlib.sha256((CACHE/f).read_bytes()).hexdigest() for f in ['ifes-upcoming.html','ifes2027.html']},excluded=[dict(contest='Guatemala 2027 presidency and Congress',reason='TSE describes 27 June as a preliminary timetable; not upgraded to confirmed.'),dict(contest='Angola, Slovakia and other year-only / deadline entries',reason='A constitutional deadline or expected year does not establish an announced polling day.'),dict(contest='Argentina 2027 presidency and parliament',reason='24 October follows the statutory fourth-Sunday rule; no reviewed 2027 official call or published timetable. Not marked as an announced confirmed date.'),dict(contest='Referendums and local elections',reason='Outside the national legislative/executive calendar scope; existing model has no referendum type.')]),ensure_ascii=False,indent=2)+'\n')
print('Patch:',sum(p['action']=='insert' for p in patch),'new elections;',sum(p['action']=='update' for p in patch),'date confirmations;',len(newcountries),'territorial directory entries')
