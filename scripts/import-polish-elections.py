"""Build Poland's national general-election archive; database writes are separate.

Uses existing WorldElection/CountryParty models. Source cells retain identities
so coalition rowspans are counted once. No ideology or missing votes are inferred.
"""
from pathlib import Path
import json, re, uuid, colorsys, hashlib, csv, io, zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scripts/polish-election-import'; CACHE=ROOT/'.cache/poland'
DATA=json.loads((OUT/'source-tables.json').read_text())
LINKS=json.loads((OUT/'links.json').read_text())
CHECKED='2026-10-12'
PKW_BOOK='https://pkw.gov.pl/uploaded_files/1463404861_Ksiega_popr_.pdf'
PKW_ARCHIVE='https://danewyborcze.kbw.gov.pl/indexc4fa.html?title=Strona_g%C5%82%C3%B3wna'
SENATE_HISTORY='https://www.senat.gov.pl/gfx/senat/userfiles/_public/k8/statystyki/senat_1922-1939/01_kadencje_1922-1939.pdf'
IPN='https://ipn.gov.pl/pl/aktualnosci/38408,Demokracja-na-sowiecka-modle-wybory-do-Sejmu-z-19-stycznia-1947-roku.html'
SEJM_HISTORY='https://www.sejm.gov.pl/sejm9.nsf/komunikat.xsp?documentId=88302293D566A47CC12585BA00290B74'
SEJM_DATES={1919:'01-26',1922:'11-05',1928:'03-04',1930:'11-16',1935:'09-08',1938:'11-06',1947:'01-19',1952:'10-26',1957:'01-20',1961:'04-16',1965:'05-30',1969:'06-01',1972:'03-19',1976:'03-21',1980:'03-23',1985:'10-13',1989:'06-04',1991:'10-27',1993:'09-19',1997:'09-21',2001:'09-23',2005:'09-25',2007:'10-21',2011:'10-09',2015:'10-25',2019:'10-13',2023:'10-15'}
SENATE_DATES={1922:'11-12',1928:'03-11',1930:'11-23',1935:'09-15',1938:'11-13'}
PRES_DATES={1990:['11-25','12-09'],1995:['11-05','11-19'],2000:['10-08'],2005:['10-09','10-23'],2010:['06-20','07-04'],2015:['05-10','05-24'],2020:['06-28','07-12'],2025:['05-18','06-01']}
records=[]; audit=[]; profiles={}
PALETTE={'Law and Justice':'#073a76','United Right':'#073a76','Civic Platform':'#f28a19','Civic Coalition':'#f28a19',"Polish People's Party":'#16863f','Polish Coalition':'#16863f','Third Way':'#71a939','The Left':'#d83056','New Left':'#d83056','Democratic Left Alliance':'#d92b35','Solidarity':'#c81923',"Solidarity Citizens' Committee":'#c81923',"Polish United Workers' Party":'#b91c28','Together':'#913e92','Partia Razem':'#913e92','Modern':'#167ac0','Confederation Liberty and Independence':'#162d54'}
def num(s):
    s=s.replace(',','').replace('\xa0','').strip()
    return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
    n=num(s);return int(n) if n is not None and n.is_integer() else None
def clean(s):return re.sub(r'\s*\[(?:pl|uk|be|de|j)\]','',s).strip()
def profile(name,year,source):
    name=clean(name)
    name={'Labor Union':'Labour Union','Self-Defense of the Republic of Poland':'Self-Defence of the Republic of Poland','Liberal-Democratic Congress':'Liberal Democratic Congress'}.get(name,name)
    key=(('historical:' if year<1990 else 'modern:')+name)
    if name in ('','Independent','Independents','Blank ballots','Against','Abstention','Other parties','Others','Local lists and independents') or name.lower().startswith('independent') or 'Independent (' in name:return None
    if key not in profiles:
        h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff
        color=PALETTE.get(name,'#'+''.join(f'{round(x*255):02x}' for x in colorsys.hls_to_rgb(h,.42,.58)))
        profiles[key]={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/pl/'+key)),'country_id':'pl','name':name if year>=1990 else name+' — historical','short_name':name[:100],'color':color,'ideology_ids':[],'archived':False,'notes':'Election-era party, electoral committee or alliance label; no continuity with a similarly named organisation is inferred. Sources: '+source+'. Display colour is an editorial palette; no official-branding or ideological assessment is implied.'}
    return profiles[key]
def result(e,name,votes=None,share=None,seats=None,party=None,winner=False,advanced=False):
    name=clean(name);pname=name if party is None else clean(party)
    support={'Independent (PiS)':'Law and Justice','Independent (PO)':'Civic Platform','Independent (SLD)':'Democratic Left Alliance'}
    p=profile(support.get(pname,pname),int(e['startDate'][:4]),e['sources'][0]['url'])
    if pname in support:pname='Independent — supported by '+support[pname]
    r={'id':e['id']+'-row-'+str(len(e['results'])+1),'name':name,'party':pname,'color':p['color'] if p else '#808080','votes':votes,'share':share,'seats':seats,'electoralVotes':None,'winner':winner,'advanced':advanced,'ideologyIds':[]}
    if p:r['partyId']=p['id']
    e['results'].append(r);return r
def base(date,office,url,round='General',method='direct'):
    body={'sejm':'Sejm','senate':'Senate','president':'President of the Republic'}[office]
    return dict(id=f'world-poland-{office}-{date}',countryId='pl',title=body,type='presidential' if office=='president' else 'parliamentary',body=body,startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round=round,seriesId='pl-'+office,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='partial',voteBasis='Source-scoped votes',results=[],sources=[dict(label='Election result table and source bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=2,electionMethod=method,live=dict(enabled=False,reporting=None,unit='precincts',bulletin='',updated=''))
def header(t):
    return next((i,[c['text'] for c in row]) for i,row in enumerate(t['rows']) if 'Votes' in [c['text'] for c in row] or 'Seats' in [c['text'] for c in row])
def meta(t,vi,si=None):
    answer={}
    for row in t['rows']:
        texts=[c['text'] for c in row];labels={s for s in texts[:vi] if s and num(s) is None and s not in ('–','—','-')}
        for key in ('Total','Valid votes','Total votes','Registered voters/turnout'):
            if labels=={key}:
                answer[key]={'votes':integer(texts[vi]) if len(texts)>vi else None,'seats':integer(texts[si]) if si is not None and len(texts)>si else None,'share':num(texts[vi+1]) if len(texts)>vi+1 else None}
    return answer
def parliamentary(key,year,office,t):
    date=f'{year}-'+(SENATE_DATES.get(year,SEJM_DATES[year]) if office=='senate' else SEJM_DATES[year])
    e=base(date,office,LINKS[key]);hi,h=header(t);si=h.index('Seats');vi=h.index('Votes') if 'Votes' in h else si
    m=meta(t,vi,si);control=m.get('Total',{});valid=control.get('votes') if vi!=si else None
    groups={};vote_cells=set();seat_cells=set()
    for row in t['rows'][hi+1:]:
        texts=[c['text'] for c in row]
        if len(texts)<=si:continue
        names=[]
        for s in texts[:min(vi,si)]:
            if s and s not in names:names.append(s)
        if not names:continue
        if names==['Total']:break
        if 'Total' in names:continue
        if any(s.startswith(('Source:','Registered','Valid votes','Invalid','Total votes','By bloc')) for s in names):continue
        name=names[-1] if year==2023 and office=='senate' else names[0]
        v=integer(texts[vi]) if vi!=si else None
        seat=integer(texts[si]);seat=0 if seat is None and texts[si] in ('–','—','-') else seat
        if v is None and seat is None:continue
        x=groups.setdefault(name,{'votes':None,'seats':0,'seatKnown':True})
        if v is not None and row[vi]['cell'] not in vote_cells:
            x['votes']=(x['votes'] or 0)+v;vote_cells.add(row[vi]['cell'])
        if seat is not None and row[si]['cell'] not in seat_cells:
            x['seats']+=seat;seat_cells.add(row[si]['cell'])
        elif seat is None:x['seatKnown']=False
    cap=control.get('seats')
    if year>=1961 or year==1989:cap=460 if office=='sejm' else 100
    if office=='sejm' and year in (1922,1928,1930,1947):cap=444
    if office=='sejm' and year in (1935,1938):cap=208
    if office=='sejm' and year==1957:cap=460
    e['totalSeats']=cap
    for name,x in groups.items():
        result(e,name,x['votes'],round(x['votes']/valid*100,6) if valid and x['votes'] is not None else None,x['seats'] if x['seatKnown'] else None)
    vote_sum=sum(r['votes'] or 0 for r in e['results']);seat_sum=sum(r['seats'] or 0 for r in e['results'])
    e['turnout']=m.get('Registered voters/turnout',{}).get('share')
    e['voteBasis']=f'Valid list/candidate vote marks in this chamber ({valid:,}); chamber ballots are not combined' if valid else 'Reported seat composition; party vote counts unavailable'
    e['resultCoverage']='complete' if seat_sum==cap and (valid is None or vote_sum==valid) else 'partial'
    e['notes']='Election-era list/committee labels are retained. Shared coalition vote cells are counted once; constituent-party seat allocations are grouped under the common list. No ideology or legal organisational continuity is inferred. '
    if office=='senate' and 1989<year<2011:
        e['voteBasis']=f'Candidate vote marks ({valid:,}); multiple votes per elector, not shares of voters' if valid else 'Seat allocation; multiple-candidate ballot vote counts unavailable'
        e['notes']+='Voters could choose multiple Senate candidates in multi-member districts. Aggregated candidate-vote percentages use vote marks, not the number of voters. Senate vote marks are never added to Sejm ballots. '
    if office=='senate' and year>=2011:e['notes']+='One senator is elected in each of 100 single-member districts. The national grouped shares aggregate candidate votes; there is no nationwide proportional Senate allocation. '
    if year==1919:
        e['title']='Constituent Sejm';e['notes']+='The initial national election was followed by regional elections and co-options as borders changed. The secondary result table groups 394 seats and is not an exact snapshot of the 335-member opening sitting or the eventual 444-member assembly. Capacity is omitted to avoid treating these different scopes as identical. ';e['totalSeats']=None;e['resultCoverage']='partial'
        e['sources'].append(dict(label='Sejm: Constituent Sejm and staggered territorial elections',url='https://www.sejm.gov.pl/KonstytucjaMarcowa.nsf/'))
    if year==1930:e['notes']+='The Brest elections took place amid repression of opposition leaders after the 1926 coup. '
    if year in (1935,1938):e['notes']+='The April Constitution restricted political competition and opposition organisations boycotted the elections. '
    if office=='senate' and year in (1935,1938):
        e['electionMethod']='indirect';e['voteBasis']='Full 96-member Senate composition, including 32 presidential appointees; not a national popular party ballot';e['notes']+='64 senators were selected indirectly under a restricted franchise and 32 were appointed by the President. Seat rows describe the full chamber, not 96 elected mandates. ';e['sources'].append(dict(label='Senate: historical terms and electoral system',url=SENATE_HISTORY))
    if year==1947:e['notes']+='Published official totals are retained as historical declared results, not reconstructed genuine voter preferences. The election was falsified and opposition supporters were repressed. ';e['sources'].append(dict(label='IPN: falsification of the 1947 election',url=IPN))
    if 1952<=year<=1985:
        e['round']='Single-front election';e['voteBasis']='Declared single-front vote totals and allocated seats; not competitive party vote shares';e['notes']+='This was a noncompetitive Communist-era single-front election. The common front vote is not allocated to individual member parties. Published figures do not establish free voter preference. '
        e['sources'].append(dict(label='IPN: single-list elections under Communist rule',url='https://archiwum.ipn.gov.pl/pl/publikacje/ksiazki/12419,Koniec-jaltanskich-zludzen-Sfalszowane-wybory-19-I-1947.html'))
    if 1991<=year<=2005:e['sources'].insert(0,dict(label='PKW: historical election results, calendar section',url=PKW_BOOK))
    elif year>=2007:e['sources'].insert(0,dict(label='KBW: official national election data archive',url=PKW_ARCHIVE))
    if vote_sum!=valid and valid is not None:e['notes']+=f'Recorded vote rows total {vote_sum:,}; source denominator {valid:,}. The gap is not filled by an invented residual row. '
    if cap is not None and seat_sum!=cap:e['notes']+=f'Recorded seat rows total {seat_sum}; chamber capacity {cap}. Missing/unfilled seats are not assigned to an invented party. '
    e['summary']=('Historical declared results of a noncompetitive single-front election.' if 1952<=year<=1985 else 'Final declared results for this chamber; see notes for electoral scope and historical limitations.')
    audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=vote_sum,expectedSeats=e['totalSeats'],recordedSeats=seat_sum,source=LINKS[key],coverage=e['resultCoverage']))
    records.append(e)
def presidential(key,year,t,date,vi=None,method='direct',ballot=''):
    hi,h=header(t);vis=[i for i,s in enumerate(h) if s=='Votes'];vi=vis[0] if vi is None else vi
    ci=max(i for i,s in enumerate(h) if s=='Candidate');pi=next((i for i,s in enumerate(h) if s=='Party'),None)
    e=base(date,'president',LINKS[key],ballot or ('First round' if len(PRES_DATES.get(year,[]))>1 and date.endswith(PRES_DATES[year][0]) else 'Runoff' if len(PRES_DATES.get(year,[]))>1 else 'General'),method)
    m=meta(t,vi);valid=m.get('Total',{}).get('votes')
    for row in t['rows'][hi+1:]:
        texts=[c['text'] for c in row]
        if len(texts)<=vi or len(texts)<=ci:continue
        name=texts[ci]
        if name=='Total':break
        v=integer(texts[vi])
        if v is None or name in ('','Candidate'):continue
        party=texts[pi] if pi is not None and len(texts)>pi else ''
        if name in ('Against','Abstention'):party=''
        if date=='1922-12-20':party='' # secondary nomination label is not treated as verified membership
        result(e,name,v,round(v/valid*100,6) if valid else None,party=party)
    assert e['results'],key
    vote_sum=sum(r['votes'] or 0 for r in e['results'])
    e['turnout']=m.get('Registered voters/turnout',{}).get('share')
    e['voteBasis']=f'{ballot+": " if ballot else ""}candidate/ballot outcomes / {valid:,} valid '+('assembly ballots; not popular votes' if method=='indirect' else 'ballots in this round')
    e['resultCoverage']='complete' if vote_sum==valid else 'partial'
    sorted_candidates=sorted([r for r in e['results'] if r['name'] not in ('Against','Abstention')],key=lambda r:r['votes'],reverse=True)
    final=method=='indirect' or e['round']!='First round'
    if final:sorted_candidates[0]['winner']=True
    else:
        for r in sorted_candidates[:2]:r['advanced']=True
    e['notes']='Each round has a separate valid-ballot denominator; percentages and vote counts are never added across rounds. Candidate party/support labels describe the election-era source, not an ideological assessment or proof of formal membership. '
    if method=='indirect':e['notes']+='The President was chosen by the legislature/National Assembly. This is not a popular presidential election. Only the specified decisive ballot is tabulated; earlier assembly ballots are not combined. ';e['sources'].insert(0,dict(label='Sejm: history of presidential elections and inauguration',url=SEJM_HISTORY))
    elif year<=2005:e['sources'].insert(0,dict(label='PKW: presidential election results, calendar section',url=PKW_BOOK))
    else:e['sources'].insert(0,dict(label='KBW: official presidential election data archive',url=PKW_ARCHIVE))
    if date=='1926-05-31':e['notes']+='Józef Piłsudski won this assembly vote but refused to take office. A new election on 1 June chose Ignacy Mościcki; the two elections are distinct. '
    if year==1947:e['notes']+='The assembly resulted from the falsified 1947 Sejm election; this was a Communist-controlled indirect selection. ';e['sources'].append(dict(label='IPN: context of the 1947 assembly',url=IPN))
    if year==1989:e['notes']+='The table denominator is 537 valid assembly ballot outcomes, including 34 abstentions; seven invalid ballots are excluded. Jaruzelski received 270 affirmative votes, 233 voted against and 34 abstained. Of 559 eligible members, 544 cast ballots. ';e['sources'].append(dict(label='Presidency: 1989 National Assembly election',url='https://www.president.pl/archives/bronislaw-komorowski/freedom-day/1989'))
    if year==2020:e['notes']+='The initially scheduled 10 May election did not take place. These records cover the actual votes on 28 June and 12 July. '
    if year==2025:e['notes']+='Nationwide totals include overseas and maritime voting. Provincial-only sums are not substituted for national results. '
    leader=sorted_candidates[0];e['summary']=leader['name']+(' won the decisive ballot.' if final else ' led the first round; the two leading candidates advanced.')
    audit.append(dict(id=e['id'],expectedVotes=valid,recordedVotes=vote_sum,expectedSeats=None,recordedSeats=0,source=LINKS[key],coverage=e['resultCoverage']))
    records.append(e)
for key,item in DATA.items():
    year=int(key[:4]);tables=item['tables']
    if 'presidential' in key:continue
    if year==1989:continue # incomparable round/component votes handled as seat allocation below
    for office in (['sejm','senate'] if year in SENATE_DATES or year>=1991 else ['sejm']):
        chosen=[t for t in tables if t['heading']==('Sejm' if office=='sejm' else 'Senate')]
        if not chosen and office=='sejm':chosen=[t for t in tables if t['heading']=='Results']
        assert chosen,(key,office)
        parliamentary(key,year,office,chosen[0])

# 1989 reserved/free components and multiple voting rounds have no common
# national popular-vote denominator. Use the final historical seat allocation.
key='1989_Polish_legislative_election'
for office,allocations in [('sejm',[("Polish United Workers' Party",173),("United People's Party",76),('Democratic Party',27),('PAX Association',10),('Christian Social Union',8),('Polish Catholic-Social Association',5),("Solidarity Citizens' Committee",161)]),('senate',[("Solidarity Citizens' Committee",99),('Independent — Henryk Stokłosa',1)])]:
    e=base('1989-06-04',office,LINKS[key],round='Two-round allocation');e.update(endDate='1989-06-18',totalSeats=460 if office=='sejm' else 100,resultCoverage='complete',voteBasis='Final seats after both rounds; incomparable vote components not combined',summary='1989 transition election: partly free Sejm ballot and fully contested restored Senate.')
    for name,seats in allocations:result(e,name,seats=seats)
    e['notes']='Final allocation after the 4 and 18 June ballots. The Sejm reserved 299 of 460 seats for the governing bloc and allowed 161 freely contested seats. All 100 restored Senate seats were freely contested. Multiple candidate votes, the national list and two rounds have different denominators; no aggregate popular vote share is invented. '
    e['sources'].insert(0,dict(label='Senate: 1989 election and restored chamber',url='https://www.senat.gov.pl/aktualnoscilista/art,16240,35-rocznica-pierwszych-wolnych-i-demokratycznych-wyborow-do-senatu-w-1989-r-.html'))
    audit.append(dict(id=e['id'],expectedVotes=None,recordedVotes=0,expectedSeats=e['totalSeats'],recordedSeats=sum(s for _,s in allocations),source=LINKS[key],coverage='complete'));records.append(e)
for year,dates in PRES_DATES.items():
    key=f'{year}_Polish_presidential_election';t=next(t for t in DATA[key]['tables'] if t['heading']=='Results');_,h=header(t);vis=[i for i,s in enumerate(h) if s=='Votes']
    for i,md in enumerate(dates):presidential(key,year,t,f'{year}-{md}',vis[i])
for year,dates in [(1922,['12-09','12-20']),(1926,['05-31','06-01'])]:
    key=f'{year}_Polish_presidential_elections';ts=[t for t in DATA[key]['tables'] if t['heading'] in (['Results'] if year==1922 else ['31 May','Election'])]
    for i,md in enumerate(dates):
        _,h=header(ts[i]);vis=[n for n,s in enumerate(h) if s=='Votes']
        presidential(key,year,ts[i],f'{year}-{md}',vis[-1],method='indirect',ballot='Decisive assembly ballot'+(' (fifth ballot)' if year==1922 and i==0 else ' (second ballot)' if year==1926 and i==1 else ''))
for year,md in [(1933,'05-08'),(1947,'02-05'),(1989,'07-19')]:
    key=f'{year}_Polish_presidential_election';t=next(t for t in DATA[key]['tables'] if t['heading']=='Results');presidential(key,year,t,f'{year}-{md}',method='indirect',ballot='Decisive assembly ballot')

# Compare official nationwide 2023 list totals, including foreign ballots, with
# the independently extracted result rows. Provincial-only 2025 data are excluded.
z=zipfile.ZipFile(CACHE/'2023-sejm-official.zip');rows=list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig')),delimiter=';'))
valid_key=next(k for k in rows[0] if k.startswith('Liczba głosów ważnych oddanych łącznie'))
official_valid=sum(int(r[valid_key] or 0) for r in rows)
e=next(e for e in records if e['id']=='world-poland-sejm-2023-10-15');assert sum(r['votes'] for r in e['results'])==official_valid==21596674
e['sources'].insert(0,dict(label='KBW: official 2023 Sejm district list results',url='https://danewyborcze.kbw.gov.pl/dane/2023/sejmsenat/wyniki_gl_na_listy_po_okregach_sejm_csv.zip'))
e['notes']+='All 41 district list files reconcile with 21,596,674 nationwide valid votes. Coalition slate votes are attributed once to their electoral list, not repeated across constituent parties. '

# Certified nationwide presidential announcements supersede territorial exports
# that exclude ships, and provincial summaries that also omit overseas voting.
primary=[]
for rnd,date in [(1,'2025-05-18'),(2,'2025-06-01')]:
    text=(CACHE/f'2025-president-certified-{rnd}.txt').read_text()
    rows=re.findall(r'\d+\)\s+([A-ZĄĆĘŁŃÓŚŹŻ]+)\s+([^\n]+?)\s+([\d ]+)\s+głos(?:y|ów)',text)
    candidates={surname:int(v.replace(' ','')) for surname,_,v in rows}
    e=next(e for e in records if e['id']=='world-poland-president-'+date)
    assert len(candidates)==len(e['results'])
    for r in e['results']:assert r['votes']==candidates[r['name'].split()[-1].upper()]
    valid=sum(candidates.values())
    assert valid==(19603784 if rnd==1 else 20844163)
    url='https://prezydent2025.pkw.gov.pl/prezydent2025/statics/PKW_OBWIESZCZENIA/uploaded_files/'+('1747706738_obwieszczenie-pkw-wyniki.pdf' if rnd==1 else '1748873119_obwieszczenie-pkw-o-wynikach-ponowne-glosowanie.pdf')
    e['sources'].insert(0,dict(label='PKW: certified nationwide presidential result announcement',url=url))
    e['notes']+='Every candidate vote count was checked against the certified national announcement, including foreign and maritime ballots. '
    primary.append(dict(id=e['id'],validVotes=valid,candidates=candidates,source=url))

# The unheld May 2020 vote is explicitly cancelled, not a zero-vote election.
cancel=base('2020-05-10','president','https://www.pkw.gov.pl/aktualnosci/wyjasnienia-stanowiska-komunikaty/komunikat-panstwowej-komisji-wyborczej-z-dnia-7-maja-2020-roku',round='Original scheduled election — not held')
cancel.update(status='cancelled',resultStatus='not-entered',summary='The election scheduled for 10 May 2020 did not take place.',notes='PKW stated that conducting the vote on 10 May was impossible. No voting took place and no zero-vote result table is invented. The new election was held on 28 June, with a runoff on 12 July.',linkedElectionIds=['world-poland-president-2020-06-28','world-poland-president-2020-07-12'])
records.append(cancel)
upcoming_url='https://pkw.gov.pl/wybory-i-referenda/wybory-do-sejmu-i-do-senatu/wybory-uzupelniajace-do-senatu-rp/kadencja-20232027/wybory-uzupelniajace-do-senatu-rp-okreg-nr-20-22-listopada-2026-r/postanowienie-o-zarzadzeniu-wyborow-i-kalendarz-wyborczy'
upcoming=base('2026-11-22','senate',upcoming_url,round='By-election')
upcoming.update(id='world-poland-senate-district-20-2026-11-22',title='Senate — district 20 by-election',body='Senate — electoral district 20',seriesId='pl-senate-district-20',status='scheduled',totalSeats=1,resultStatus='not-entered',summary='Confirmed Senate by-election in electoral district 20 on 22 November 2026.',notes='One replacement seat in the 100-member Senate, not a national 100-seat general election. The presidential order of 25 September 2026 confirms 22 November as polling day. No result or candidate is invented before official registration and polling.')
records.append(upcoming)
for e in records:
    peers=[x['id'] for x in records if x['seriesId']==e['seriesId'] and x['startDate'][:4]==e['startDate'][:4] and x['id']!=e['id']]
    if peers:e['linkedElectionIds']=peers
    assert all(r['share'] is None or 0<=r['share']<=100 for r in e['results'])
    assert sum(r['share'] or 0 for r in e['results'])<=100.2,(e['id'],sum(r['share'] or 0 for r in e['results']))
    if e['totalSeats'] is not None:assert sum(r['seats'] or 0 for r in e['results'])<=e['totalSeats'],e['id']
records.sort(key=lambda e:(e['startDate'],e['body']))
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'parties.json').write_text(json.dumps(list(profiles.values()),ensure_ascii=False,indent=2)+'\n')
(OUT/'reconciliation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
(OUT/'primary-reconciliation.json').write_text(json.dumps(primary,ensure_ascii=False,indent=2)+'\n')
print('Built',len(records),'records (65 held, one unheld/cancelled and one confirmed future by-election) and',len(profiles),'party/list profiles.')
print('Partial records',[(x['id'],x['recordedVotes'],x['expectedVotes'],x['recordedSeats'],x['expectedSeats']) for x in audit if x['coverage']=='partial'])
