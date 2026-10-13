"""Build reviewed archive-gap patches from cached sources; never writes to Supabase."""
from pathlib import Path
import copy, hashlib, json, re
from us_midterm_html import read

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/result-coverage'
OUT=ROOT/'scripts/result-coverage-import'
baseline=json.loads((OUT/'pre-import-backup.json').read_text())
links=json.loads((OUT/'primary-links.json').read_text())
records=[]
audit=[]
known_colors={r['name']:r['color'] for e in baseline for r in e['data']['results']}
totals={1999:15977142,2004:15612671,2009:17680729,2014:18402497,2019:17437379}
for year in totals:
    file=CACHE/f'za-{year}.html'
    table=next(t for t in read(file) if any([c['text'] for c in row][:3]==['Party','Votes','%'] for row in t['rows']) and any(c['text']=='African National Congress' for row in t['rows'] for c in row))
    e=copy.deepcopy(next(x['data'] for x in baseline if x['id']==f'world-south-africa-{year}'))
    pdf=(CACHE/f'za-{year}-votes.txt').read_text()
    # The national column is first through 2009, last from 2014 onward.
    national=[]
    for line in pdf.splitlines():
        matches=re.findall(r'([\d,]+)\s+(\d+\.\d+)\s*%',line)
        if matches:
            n,p=matches[0 if year<=2009 else -1]
            national.append((int(n.replace(',','')),float(p)))
    results=[]
    for row in table['rows']:
        cells=[c['text'] for c in row]
        if len(cells)<5 or cells[0]!='' or not re.fullmatch(r'[\d,]+',cells[2]): continue
        name=cells[1];votes=int(cells[2].replace(',',''));share=float(cells[3]);seats=int(cells[5 if year==2019 else 4])
        assert (votes,share) in national,(year,name,votes,share)
        color=re.search(r'background-color:(#[a-fA-F0-9]{6})',row[0].get('style',''))
        results.append(dict(id=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-'),name=name,party='',color=known_colors.get(name,color[1] if color else '#385b82'),votes=votes,share=share,seats=seats,electoralVotes=None,winner=False,ideologyIds=[]))
    assert sum(r['votes'] for r in results)==totals[year]
    assert sum(r['seats'] for r in results)==400
    assert len(results)==len(national)-1,(year,len(results),len(national)) # Includes the report's total-valid row.
    e.update(results=results,totalSeats=400,resultStatus='final',resultCoverage='complete',checked='2026-10-13',version=e['version']+1,
             voteBasis='Valid national National Assembly ballots; provincial ballots excluded',
             notes='Complete national party table, including parties awarded zero seats. Percentages are source-rounded shares of valid national ballots, not provincial ballots or seat shares. Seats are the election allocation; later floor crossings, vacancies and office-holder changes are excluded. '+('The 2004 IEC calculation report distinguishes allocated seats (S) from seats assigned to members (A); this table records the 400 allocated seats, including seven allocated to ACDP.' if year==2004 else ''))
    for x in links:
        if x['year']==year and x.get('error')==0:
            e['sources'].append(dict(label='Electoral Commission of South Africa — national '+x['category']+' report',url=x['url']))
    e['sources'].append(dict(label='Reviewed national party allocation and historical bibliography',url=f'https://en.wikipedia.org/wiki/{year}_South_African_general_election'))
    if year==1999:
        e['sources'].append(dict(label='IFES ElectionGuide — 1999 elected party allocation',url='https://electionguide.org/elections/id/240/'))
    records.append(e)
    audit.append(dict(id=e['id'],rows=len(results),votes=totals[year],seats=400,officialVoteRowsChecked=len(results),htmlSha256=hashlib.sha256(file.read_bytes()).hexdigest()))
def slug(name): return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
def result(name,party='',color='#385b82',**values):
    return dict(id=slug(name),name=name,party=party,color=color,votes=None,share=None,seats=None,electoralVotes=None,winner=False,ideologyIds=[],**values)

# India: all seat-winning groups, not an invented full popular-vote table.
# IPU omits a faction qualifier and mislabels Kerala Congress as KC(M).
# Use the explicitly differentiated reviewed election table for those labels.
file=CACHE/'india-wiki.html'
table=next(t for t in read(file) if any([c['text'] for c in row][:4]==['Party or alliance','Votes','%','Seats'] for row in t['rows']))
e=copy.deepcopy(next(x['data'] for x in baseline if x['id']=='world-india-2024'))
results=[]
for row in table['rows']:
    cells=[c['text'] for c in row]
    if not cells or cells[0]!='' or len(cells)<6: continue
    tail=cells[-5:]
    if not re.fullmatch(r'[\d,]+',tail[1]) or not tail[3].isdigit() or int(tail[3])==0: continue
    name=tail[0]
    color=next((re.search(r'background(?:-color)?:\s*(#[a-fA-F0-9]{6})',c.get('style','')) for c in row if re.search(r'background(?:-color)?:\s*(#[a-fA-F0-9]{6})',c.get('style',''))),None)
    r=result(name,color=color[1] if color else '#385b82');r['seats']=int(tail[3]);results.append(r)
assert len(results)==42 and sum(r['seats'] for r in results)==543
e.update(results=results,resultStatus='final',resultCoverage='partial',checked='2026-10-13',version=e['version']+1,
         voteBasis='Elected Lok Sabha seats by party; popular-vote counts and shares not transcribed',
         notes='All 543 elected seats are shown, including seven independent winners. Voting took place in seven phases. The two Shiv Sena factions are distinguished by their election labels; Kerala Congress and Kerala Congress (Mani) are different parties. IPU’s abbreviated party labels are reconciled against the reviewed election table. Popular-vote counts and shares remain blank, so overall result coverage is partial. Seat ranks do not represent government formation.')
e['sources'] += [dict(label='IPU Parline — 2024 election and party seat allocation',url='https://data.ipu.org/parliament/IN/IN-LC01/election/IN-LC01-E20240419/'),dict(label='Reviewed party and faction results; ECI bibliography',url='https://en.wikipedia.org/wiki/2024_Indian_general_election')]
records.append(e);audit.append(dict(id=e['id'],rows=42,seats=543,coverage='partial',htmlSha256=hashlib.sha256(file.read_bytes()).hexdigest()))

file=CACHE/'brazil-2022.html'
table=next(t for t in read(file) if any(c['text']=='57,259,504' for row in t['rows'] for c in row))
e=copy.deepcopy(next(x['data'] for x in baseline if x['id']=='world-brazil-president-2022-first'))
runoff=next(x['data'] for x in baseline if x['id']=='world-brazil-president-2022-runoff')
results=[]
for row in table['rows']:
    cells=[c['text'] for c in row]
    if len(cells)<6 or cells[0]!='' or not re.fullmatch(r'[\d,]+',cells[4]):continue
    name=cells[1];r=result(name,party=cells[3]);r.update(votes=int(cells[4].replace(',','')),share=float(cells[5]),advanced=len(results)<2)
    previous=next((r for r in runoff['results'] if r['name']==name),None)
    if previous:r.update(color=previous['color'],party=previous['party'],ideologyIds=previous.get('ideologyIds',[]))
    results.append(r)
assert len(results)==11 and sum(r['votes'] for r in results)==118229719
assert results[0]['votes']==57259504 and results[1]['votes']==51072345
e.update(results=results,resultStatus='final',resultCoverage='complete',checked='2026-10-13',version=e['version']+1,
         voteBasis='Valid first-round presidential votes; blank and invalid ballots excluded',
         notes='All eleven first-round presidential candidates. TSE’s completed count on 4 October supersedes its earlier election-night totals. Lula and Bolsonaro advanced to the runoff; neither was elected in the first round. Shares are source-rounded percentages of valid first-round votes.',linkedElectionIds=['world-brazil-president-2022-runoff'])
e['sources'] += [dict(label='TSE — completed first-round count, 4 October 2022',url='https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/100-das-secoes-totalizadas-confira-como-ficou-o-quadro-eleitoral-apos-o-1o-turno'),dict(label='Reviewed full first-round table and TSE bibliography',url='https://en.wikipedia.org/wiki/2022_Brazilian_general_election')]
records.append(e);audit.append(dict(id=e['id'],rows=11,votes=118229719,htmlSha256=hashlib.sha256(file.read_bytes()).hexdigest()))
modern=json.loads((OUT/'modern-source-extract.json').read_text())
control=modern['sweden'];e=copy.deepcopy(next(x['data'] for x in baseline if x['id']=='world-sweden-2026'))
e['results']=[]
for name,share,seats,color in control['rows']:
    r=result(name,color=color);r.update(share=share,seats=seats);e['results'].append(r)
assert sum(r['seats'] for r in e['results'])==349
e.update(totalSeats=349,resultStatus='final',resultCoverage='complete',turnout=control['turnout'],checked='2026-10-13',version=e['version']+1,
         voteBasis='Valid Riksdag vote shares from Valmyndigheten; source groups other participating parties',
         notes='Official final Riksdag summary: all 349 seats and all vote-share categories. Other participating parties remain a source aggregate, not a single political party. Raw party vote totals are not transcribed from rounded percentages. Municipal and regional council results are excluded.')
e['sources'].append(dict(label='Swedish Election Authority — final 2026 Riksdag results',url=control['url']));records.append(e)
audit.append(dict(id=e['id'],rows=9,seats=349,shareTotal=sum(r['share'] for r in e['results']),source=control['url']))

file=CACHE/'denmark-2026.html'
table=next(t for t in read(file) if any([c['text'] for c in row][:3]==['Parti','Antal','Pct.'] for row in t['rows']))
e=copy.deepcopy(next(x['data'] for x in baseline if x['id']=='world-denmark-2026'));results=[]
for row in table['rows']:
    cells=[c['text'] for c in row]
    if len(cells)!=6 or not cells[2].endswith('%'):continue
    r=result(cells[0]);r.update(votes=int(cells[1].replace('.','')),share=float(cells[2].rstrip('%').replace(',','.')),seats=int(cells[3]) if cells[3].isdigit() else 0);results.append(r)
assert len(results)==13 and sum(r['votes'] for r in results)==3567625 and sum(r['seats'] for r in results)==175
url='https://www.dst.dk/valg/Valg2546527/valgopg/valgopgHL.htm'
e.update(results=results,totalSeats=179,resultStatus='final',resultCoverage='partial',turnout=None,checked='2026-10-13',version=e['version']+1,
         voteBasis='Valid mainland Denmark ballots; Greenland and Faroe Islands excluded',
         notes='Statistics Denmark’s final mainland count covers 175 of the Folketing’s 179 seats. The two Greenland and two Faroe Islands seats are not included in this table and remain untranscribed. Mainland turnout was 83.99%; it is not entered as turnout for the entire realm. Percentages retain the source’s one-decimal rounding. Uden for partierne groups unaffiliated candidates, not a political party.')
e['sources'].append(dict(label='Statistics Denmark — final mainland count, 26 March 2026',url=url));records.append(e);audit.append(dict(id=e['id'],rows=13,votes=3567625,seats=175,expectedChamberSeats=179,coverage='partial',htmlSha256=hashlib.sha256(file.read_bytes()).hexdigest()))

control=modern['morocco'];e=copy.deepcopy(next(x['data'] for x in baseline if x['id']=='world-morocco-2026'))
results=[]
for name,party,seats in control['rows']:
    r=result(name,party=party);r['seats']=seats;results.append(r)
assert sum(r['seats'] for r in results)==395
e.update(results=results,totalSeats=395,resultStatus='provisional',resultCoverage='partial',turnout=control['turnout'],checked='2026-10-13',version=e['version']+1,
         voteBasis='Provisional elected House seats; local and regional ballot shares not combined',
         notes='All 395 seats in the Interior Minister’s preliminary allocation announced 24 September 2026. The official source labels this allocation provisional; no final certification is inferred. Votes and shares remain blank. Local and regional list ballots have separate denominators and are not summed into a national popular-vote percentage. Government formation is distinct from seat rankings.')
e['sources'].append(dict(label='Morocco government portal / MAP — preliminary Interior Ministry allocation',url=control['url']));records.append(e);audit.append(dict(id=e['id'],rows=14,seats=395,status='provisional',coverage='partial',source=control['url']))
for control in json.loads((OUT/'nepal-source-extract.json').read_text()):
    year=control['year'];e=copy.deepcopy(next(x['data'] for x in baseline if x['id']==f'world-nepal-national-assembly-{year}'))
    e['results']=[]
    for name,seats in control['rows']:
        r=result(name);r['seats']=seats;e['results'].append(r)
    assert sum(r['seats'] for r in e['results'])==control['electedSeats']
    e.update(totalSeats=59,resultStatus='final',resultCoverage='partial',electionMethod='indirect',checked='2026-10-13',version=e['version']+1,
             voteBasis=f"{control['electedSeats']} indirectly elected seats in this renewal; appointed and continuing seats excluded",
             notes=f"The chamber has 59 members: 56 indirectly elected and three appointed. This table records the {control['electedSeats']} seats elected in this election, including any unopposed winners. It is not the complete chamber composition. Appointed members and continuing terms are excluded. Candidate vote totals, weighted elector ballots and percentages are not inferred, so coverage remains partial. Historical party names at this election are retained; later mergers and splits are not applied retrospectively. "+('The January 2022 and 2024 renewals each elected 19 members, separately from the appointed seat retiring in the same cohort. ' if year in [2022,2024] else '')+('Mahanta Thakur’s seat is recorded under JSP-N, as reported by Radio Nepal after the documented 11 January 2026 merger of LSP-N into JSP-N; older LSP-N labels are not carried forward.' if year==2026 else ''))
    e['sources'].append(dict(label='Contemporary National Assembly election results',url=control['url']))
    if control.get('mergerSource'):e['sources'].append(dict(label='Kathmandu Post — documented pre-election JSP-N / LSP-N merger',url=control['mergerSource']))
    records.append(e);audit.append(dict(id=e['id'],rows=len(e['results']),seats=control['electedSeats'],expectedChamberSeats=59,coverage='partial',source=control['url']))
for year,control in json.loads((OUT/'tunisia-final-controls.json').read_text()).items():
    year=int(year);file=CACHE/f'tunisia-{year}.html'
    table=next(t for t in read(file) if any([c['text'] for c in row][:2]==['Candidate','Party'] for row in t['rows']))
    e=copy.deepcopy(next(x['data'] for x in baseline if x['id']==f'world-tunisia-{year}-'+('11-23' if year==2014 else '09-15')+'-presidential-election'))
    controls=control.get('votesAndShares')
    if year==2014:
        pdf=(CACHE/'tunisia-carter-2014.txt').read_text()
        section=pdf[pdf.index('Candidates',pdf.index('3,267,569')):]
        controls=[[int(v.replace(',','')),float(p)] for v,p in re.findall(r'\s+([\d,]+)\s+(\d+\.\d+)\s*$',section.split('Total')[0],re.M)]
    results=[]
    for row in table['rows']:
        cells=[c['text'] for c in row]
        if len(cells)<5 or cells[0]!='' or not re.fullmatch(r'[\d,]+',cells[3]):continue
        name=re.sub(r'\s*\[(?:fr|ar)\]','',cells[1]);r=result(name,party=cells[2]);r.update(votes=int(cells[3].replace(',','')),share=float(cells[4]),advanced=len(results)<2)
        assert [r['votes'],r['share']] in controls,(year,name,r['votes'],r['share'])
        results.append(r)
    assert len(results)==control['rows'] and sum(r['votes'] for r in results)==control['validVotes']
    e.update(results=results,resultStatus='final',resultCoverage='complete',checked='2026-10-13',version=e['version']+1,
             voteBasis='Valid first-round presidential ballots; blank and invalid ballots excluded',
             notes=f"All {len(results)} first-round candidate results, including ballot entries for withdrawn candidates where recorded. The leading two advanced to the runoff; no first-round winner is declared. Final reported counts and source-rounded percentages are retained. "+('Final ISIE decision 2019-27 records 3,372,973 valid votes, superseding earlier preliminary reports. Candidate counts are checked against its published JORT transcription.' if year==2019 else 'All candidate counts and percentages are checked against the Carter Center final observation report’s reproduction of ISIE results.'))
    e['sources'] += [dict(label='Final presidential first-round results — '+('Carter Center / ISIE' if year==2014 else 'ISIE decision 2019-27, JORT transcription'),url=control['url']),dict(label='Reviewed first-round candidate names and party labels',url=f'https://en.wikipedia.org/wiki/{year}_Tunisian_presidential_election')]
    records.append(e);audit.append(dict(id=e['id'],rows=len(results),votes=control['validVotes'],verifiedCandidatePairs=len(results),source=control['url'],htmlSha256=hashlib.sha256(file.read_bytes()).hexdigest()))
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'reconciliation.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
