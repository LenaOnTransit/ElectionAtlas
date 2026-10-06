"""Build Montenegro parliamentary records from checked source extracts; never publishes."""
import json, math, re, uuid, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'scripts/montenegro-election-import'
CHECKED = '2026-10-06'
DATASET = 'https://electionsinmontenegro.com/wp-content/uploads/2025/12/mnee_dataset1.zip'
NAMES = 'https://electionsinmontenegro.com/wp-content/uploads/2025/12/mnee_alldatasets_partynamesabbreviations.pdf'
DATES = 'https://electionsinmontenegro.com/wp-content/uploads/2025/12/mnee_datesofelections.pdf'
SYSTEM = 'https://electionsinmontenegro.com/wp-content/uploads/2025/12/mnee_alldatasets_electoralsystem.pdf'
UNDP = 'https://www.undp.org/sites/g/files/zskgke326/files/2024-01/undp_-_80_godina_politicke_istorije_zena_crne_gore.pdf'
PARLIAMENT = 'https://api.skupstina.me/media/files/1606741748-zenska-strana-parlamenta-brosura.pdf'
HISTORY = 'https://api.skupstina.me/media/files/1678362554-1616422259-vodic-kroz-skupstinu-crne-gore.pdf'
OFFICIAL = {
    2006: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2006/Izvjestaj-o-rezultatima-izbora-za-poslanike-u-Skupstinu-CG.pdf',
    2009: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2009/Postupak-i-podaci-na-osnovu-kojih-su-utvrdjeni-konacni-rez.-za-izbor-poslanika-u-Skupstini-CG.pdf',
    2012: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2012/post.utvr_.kon_.rez_.pdf',
    2016: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2016/Konacni-rezultati.pdf',
    2020: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2020/konacni_2020.pdf',
    2023: 'https://dik.co.me/images/DIK-media/izbori/parlamentarni/2023/KONACNI-REZULTATI-2023.pdf',
}
records, parties, audit = [], {}, []
def source(label, url): return {'label': label, 'url': url}
def election(date, slug, title, body, seats, method='direct', series='montenegro-parliament', end=''):
    e = dict(id=f'world-montenegro-{date}-{slug}', countryId='me', title=title,
             type='parliamentary', body=body, startDate=date, endDate=end, precision='day',
             dateStatus='confirmed', status='held', publication='published', round='General',
             seriesId=series, snap=False, summary='', government='', turnout=None,
             totalSeats=seats, majorityThreshold=seats//2+1 if seats else None,
             resultStatus='final', resultCoverage='partial', voteBasis='Vote totals unavailable',
             results=[], sources=[], checked=CHECKED, notes='', articleId='', version=1)
    if method: e['electionMethod'] = method
    records.append(e)
    return e
def result(e, name, party, votes=None, share=None, seats=None, color='#808080', pid=None, previous=None):
    r = dict(id=e['id']+'-r'+str(len(e['results'])+1), name=name, party=party,
             color=color, votes=votes, share=share, seats=seats, previousSeats=previous,
             electoralVotes=None, winner=False, advanced=False, ideologyIds=[])
    if pid: r['partyId'] = pid
    e['results'].append(r)
    return r

# Reusable parties only; multi-party ballot lists retain their own election-era labels.
PROFILES = {
    'SKCG': ('League of Communists of Montenegro', '#c62828'),
    'DPS': ('Democratic Party of Socialists of Montenegro', '#e52b39'),
    'NSCG': ("People’s Party (founded 1990)", '#315b96'),
    'LSCG': ('Liberal Alliance of Montenegro', '#25a6aa'),
    'SDPR': ('Social Democratic Party of Reformists', '#b84343'),
    'SDP': ('Social Democratic Party of Montenegro', '#c8242a'),
    'SNP': ('Socialist People’s Party of Montenegro', '#315b96'),
    'SNS': ('Serb People’s Party', '#4169a1'),
    'DUA': ('Democratic Union of Albanians', '#227947'),
    'DSCG': ('Democratic Alliance in Montenegro', '#247052'),
    'PDP': ('Party of Democratic Prosperity', '#468766'),
    'PZP': ('Movement for Changes', '#ef9a23'),
    'BS': ('Bosniak Party', '#248748'),
    'HGI': ('Croatian Civic Initiative', '#cf3f43'),
    'FORCA': ('New Democratic Power – FORCA', '#e2942b'),
    'AA': ('Albanian Alternative', '#e34c38'),
    'PCG': ('Positive Montenegro', '#ed7e29'),
    'Demokrate': ('Democratic Montenegro', '#e23b3b'),
    'SD': ('Social Democrats of Montenegro', '#d84648'),
    'PES': ('Europe Now Movement', '#efb724'),
}
for key, (name, color) in PROFILES.items():
    pid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://worldofelections.com/parties/me/'+key))
    note = 'Archive profile. Names and colours on results are election-era snapshots. Colour is an editorial display convention, not evidence of ideology. No ideology classification has been inferred.'
    if key == 'SKCG': note += ' Historical name used in 1990; renamed DPS in 1991. Kept as a historical-name profile rather than relabelling the 1990 ballot.'
    if key == 'NSCG': note += ' The party founded in 1990 is distinct from the royal-era People’s Party.'
    parties[key] = dict(id=pid, country_id='me', name=name, short_name='DCG' if key=='Demokrate' else key,
                        color=color, ideology_ids=[], notes=note, archived=key in ['SKCG','LSCG','SDPR','SNS','NSCG'])

name_rows = json.loads((OUT/'party-name-reference.json').read_text())
def party_name(key, year):
    corrections = {'UR9192': 'Udruženje ratnika ’91–’92',
                   'DHPS': 'Orthodox Christian Democratic Party',
                   'DSSPCG': 'Democratic Alliance of Independent Entrepreneurs of Montenegro',
                   'EPCG': 'Environmental Movement of Montenegro',
                   'SOPCG': 'Serb Motherland Movement'}
    if key in corrections: return corrections[key]
    if key in PROFILES: return PROFILES[key][0]
    matches = [r for r in name_rows if r['year'] <= year and
               (r['abbreviation'] == key or r['abbreviation'].startswith(key+' ('))]
    if matches:
        r = max(matches, key=lambda r:r['year'])
        return r['englishName'] if r['englishName'] and 'Unsure' not in r['englishName'] else r['originalName']
    return {'SKJ-KCG':'Alliance of Communists of Yugoslavia – Communists of Montenegro',
            'JUL':'Yugoslav Left in Montenegro', 'Demokrate':'Democratic Montenegro',
            'SSS-SSJCG':'Serb Alliance', 'SKJCG-JKCG':'Montenegrin Communists',
            'SPICG-JKPCG':'Together – pensioners and Yugoslav communists',
            'DSS-SRS-GG':'Serb National Alliance', 'SSR-SSN-GG':'Serb National List',
            'DSCG-PDP':'Democratic Alliance – Party of Democratic Prosperity',
            'Pravda za sve':'Justice for All', 'Preokret':'Preokret (Turnaround)',
            'GBMM-GCG':'Yes We Can', 'NSS-SRS-JUL-SDSCG':'Patriotic Coalition for Yugoslavia',
            'DPS-SD-DUA-LPCG':'Together! – DPS, SD, DUA and Liberal Party',
            'DP-NODS-DSCG-GBPT':'Albanian Alliance', 'AA-DSA-NAU':'Albanian Forum – BESA for European Development',
            'NOVA-DNP-RP':'For the Future of Montenegro',
            'NOVA-PZP-DNP-SNP-PRAVA-UCG-RP-PUPICG-JKPCG-SRS-SPISPCG':'For the Future of Montenegro',
            'DP-GI-DSCG-GPP':'Albanian Coalition – With One Goal',
            'FORCA-DUA-AA':'Albanians Determined', 'BDP-DZM':'Bosniaks and Muslims Together, One',
            'SNP-NSCG-DSS':'SNP–People’s Party–Democratic Serb Party coalition',
            'DS-DSSP-NDS-SDS':'Democratic Opposition',
            'SDA-DSCG-SR':'Democratic Coalition – SDA, Democratic Alliance and Party of Equality',
            'SPCG-LSCG-PSCG-NOK-SNR-SDSCG-DACG':'Alliance of Reformist Forces of Yugoslavia for Montenegro',
            'NSCG-SL-OSS-SRSCG-DCB':'Serb Unity', 'BDZ':'Bosniak Democratic Community',
            'SRS':'Serb Radical Party – Vojislav Šešelj', 'SRSCG':'Serb Radical Party of Montenegro',
            'SPISP':'Party of Pensioners, Disabled People and Social Justice',
            'SSMZ':'Serb Party – Milovan Živković', 'LDSA':'List of the Democratic Alliance of Albanians',
            'GL':'Citizens’ List'}.get(key,key)

dates = {1990:'1990-12-09',1992:'1992-12-20',1996:'1996-11-03',1998:'1998-05-31',
         2001:'2001-04-22',2002:'2002-10-20',2006:'2006-09-10',2009:'2009-03-29',
         2012:'2012-10-14',2016:'2016-10-16',2020:'2020-08-30',2023:'2023-06-11'}
raw = json.loads((OUT/'national-results.json').read_text())
previous = {}
for year, date in dates.items():
    rows = [r for r in raw if r['election_year']==year]
    valid, electorate, cast, total = (rows[0][k] for k in ['votes_valid','electorate_total','votes_cast','seats_total'])
    e = election(date,'parliament','Parliament — '+('first postwar multiparty election' if year==1990 else 'early election' if year in [1998,2001,2002,2009,2012,2023] else 'general election'), 'Parliament of Montenegro',total)
    e['snap'] = year in [1998,2001,2002,2009,2012,2023]
    e['turnout'] = round(cast/electorate*100,4)
    e['voteBasis'] = f'National party/list votes; {valid:,} valid votes'
    e['resultCoverage'] = 'complete'
    e['sources'] = ([source('Electoral commission: final votes and mandates',OFFICIAL[year])] if year in OFFICIAL else []) + [
        source('MNEE Dataset 1: national totals and commission source references',DATASET),
        source('MNEE: election dates',DATES), source('MNEE: period party names and coalition members',NAMES),
        source('MNEE: electoral systems, 1990–2020',SYSTEM)]
    if year==2023: e['sources'].pop()  # The 1990–2020 system reference does not cover 2023.
    notes = [f'Turnout: {cast:,} voters / {electorate:,} registered electors. Shares are recalculated from the stated valid-vote denominator, not all registered voters or all ballots cast.',
             'Coalitions remain single result rows; coalition votes are not distributed among component parties. All lists in the checked national table, including zero-seat lists, are included. Blank government information and unassessed ideology do not imply a conclusion about either.',
             'Previous seats are shown only for the same standalone party in the immediately preceding election or an unchanged coalition membership. A missing comparison is null, not zero. Chamber size and electoral boundaries changed across some elections.']
    if year<=2002:
        notes.append('Montenegro was a constituent republic of Yugoslavia at the time; this is its republic parliament, not a Yugoslav federal election. Results are the MNEE transcription of the commission reports cited in the source audit; the original reports were published in Pobjeda / the Official Gazette.')
    if year in [1990,1992]: notes.append('The valid-vote denominator is the sum of party/list votes reconstructed by MNEE because the archival commission report did not separately report it. No independently reported rejected-ballot count is inferred from the turnout difference.')
    elif year not in [2016,2020,2023]: notes.append(f'The checked source records {cast-valid:,} invalid ballots (votes cast less valid votes).')
    if year==1990:
        system = 'Direct closed-list proportional representation in 20 constituencies, using D’Hondt and a 4% threshold.'
        notes.append('The League of Communists (SKCG) is retained under its 1990 name; it became DPS in 1991. The commission transcription assigns 13 seats to the Democratic Coalition and 12 to the People’s Party; some secondary accounts reverse these figures.')
    elif year==1992: system = 'Direct closed-list proportional representation in one nationwide constituency, using D’Hondt and a 4% threshold.'
    elif year==1996:
        system = 'Direct modified closed-list proportional representation in 14 constituencies, using D’Hondt and a 4% threshold.'
        notes.append('The official-source transcription and electoral-system archive report 71 seats, not the 75 sometimes used in secondary party histories.')
    elif year<=2009:
        sub = {1998:5,2001:5,2002:4,2006:5,2009:5}[year]
        system = f'Direct modified closed-list proportional representation using D’Hondt and a 3% threshold: {total-sub} nationwide mandates and {sub} mandates allocated through the designated Albanian-majority polling stations.'
        notes.append('National list vote totals include the designated minority polling stations once. Their separate mandate-allocation calculations are not added as a second national vote table. Half of the mandates were assigned in submitted list order and the remainder at the list submitter’s discretion.')
    else:
        system = 'Direct closed-list proportional representation in a single nationwide constituency, using D’Hondt, a 3% general threshold, and reduced qualification rules for recognised minority lists (0.7%; special 0.35% Croatian rule).'
    if year==2001: notes.append('The date is 22 April, not 23 April as misprinted in the 2002 OSCE comparison. MNEE’s commission transcription records 153,946 votes for DPS–SDP; the OSCE comparison gives 153,496 and aggregates Albanian lists inconsistently. The commission transcription is used throughout; no mixed-source denominator is constructed.')
    if year==2002: notes.append('The commission transcription gives 353,102 voters and 348,398 valid votes. The 2002 OSCE comparison has several different list totals and an internally inconsistent overall voting total; it is not substituted for the commission transcription.')
    if year==2006:
        e['resultCoverage']='partial'
        notes.append('The final commission list figures sum to 338,833 votes, two fewer than the 338,835 valid votes recorded in MNEE. All 12 final list totals are retained unchanged, shares use 338,835, and the two unallocated votes are documented rather than invented as an “Other” party. Seats reconcile to 81.')
    if year==2009: notes.append('The official 3% qualifying quotas used votes cast: 9,895 nationwide and 573 in the minority polling-station group. These legal quotas differ from the valid-vote basis used for descriptive shares in this record.')
    if year==2016: notes.append('Final certification: 29 October 2016. The commission reports 5,513 invalid ballots and one missing ballot, explaining why 382,706 valid plus invalid ballots is one below 388,220 voters. The formally submitted DPS list included Liberal Party cooperation; coalition component mandates are not split into separate vote rows. The 693-vote list is Stranka srpskih radikala (SSR), as named in the final commission return; MNEE’s reused SRS code/name is corrected and is not linked to the earlier Šešelj party.')
    if year==2020: notes.append('Final certification: 14 September 2020. DPS received 143,515 votes, not the preliminary 143,548 often repeated elsewhere. The commission reports 4,500 invalid ballots and one used ballot carried away in Kolašin (not counted valid or invalid); a separate ballot carried away in Herceg Novi explains the received/used/unused difference.')
    if year==2023: notes.append('Final certification: 14 July 2023, after complaints and a repeat poll; this record retains the original general-election date. There were 305,324 voters but 305,326 used ballots: two wrongly stamped ballots in Krašići, Tivat, were cancelled and replaced. Valid ballots: 302,436; invalid: 2,890. Early provisional totals are not used.')
    current = {}
    for row in rows:
        key, v, s = row['party_coalition'], row['votes_won'], row['seats_won']
        name = row['coalition_name_english'] or party_name(key,year)
        overrides = {(1998,'DPS-NSCG-SDP'):'For a Better Life – Milo Đukanović',
                     (2001,'DPS-SDP'):'Victory is Montenegro – DPS–SDP',
                     (2002,'DPS-SDP'):'Democratic List for European Montenegro – DPS–SDP',
                     (2020,'DPS'):'Decisively for Montenegro! – DPS',
                     (2023,'DPS-SD-DUA-LPCG'):'Together! – DPS, SD, DUA and Liberal Party',
                     (2023,'PES'):'Europe Now – Milojko Spajić',
                     (2023,'Preokret'):'Preokret – For a Secure Montenegro',
                     (2023,'Pravda za sve'):'Justice for All – Vladimir Leposavić'}
        name = overrides.get((year,key),name)
        if year==2016 and key=='SRS': name='Party of Serb Radicals – Montenegro in Safe Hands'
        # Long coalition descriptions belong in the notes, not truncation of a party name.
        if key=='NSCG-LSCG': name='People’s Unity – People’s Party and Liberal Alliance'
        if len(name)>200: name=party_name(key,year)
        if len(name)>200: raise ValueError((year,key,name))
        profile=parties.get(key)
        color=profile['color'] if profile else '#808080'
        if 'DPS' in key.split('-'): color='#e52b39'
        if key in ['DF','NOVA-DNP-RP'] or key.startswith('NOVA-PZP-DNP'): color='#315b96'
        if key in ['Demokrate-URA','DEM-DEMOS-PPIR-GPNL']: color='#e23b3b'
        if key=='URA-SPP-CIVIS-NI': color='#42a58b'
        comparison_key='-'.join(sorted(key.split('-')))
        prev=previous.get(comparison_key)
        if year==1992 and key=='DPS': prev=83
        if year==2016 and key=='DPS': prev=None  # previous ballot was a multi-party coalition
        if year==2023 and key in ['SDP','BS','HGI','PZP']: prev=previous.get(comparison_key)
        result(e,name,'SSR' if year==2016 and key=='SRS' else profile['short_name'] if profile else key,v,round(v/valid*100,6),s,
               color,profile['id'] if profile else None,prev)
        current[comparison_key]=s
    previous=current
    e['summary']=system+' '+max(e['results'],key=lambda r:r['votes'])['name']+f' received the largest number of list votes. The chamber had {total} seats.'
    e['notes']='\n\n'.join(notes)
    assert sum(r['seats'] for r in e['results'])==total
    gap=valid-sum(r['votes'] for r in e['results'])
    assert gap==(2 if year==2006 else 0)
    audit.append(dict(id=e['id'],validVotes=valid,recordedVotes=valid-gap,unallocatedVotes=gap,
                      electorate=electorate,voters=cast,seats=total,recordedSeats=total,
                      primarySourceReference=rows[0]['source'],sourceNotes=sorted({r['notes'] for r in rows if r['notes']})))

# Constitutional and monarchical elections: preserve uncertain denominators instead
# of turning post-election political affiliations into popular-vote figures.
for date, slug, title in [
    ('1905-11-27','constitutional-assembly','Constitutional Assembly'),
    ('1906-09-27','parliament','National Assembly — first legislative election'),
    ('1907-10-31','parliament','National Assembly — opposition boycott'),
    ('1911-09-27','parliament','National Assembly — royalist and opposition groups'),
    ('1914-01-11','parliament','National Assembly — final kingdom election')]:
    year=int(date[:4]); url=f'https://en.wikipedia.org/wiki/{year}_Montenegrin_'+('Constitutional_Assembly_election' if year==1905 else 'parliamentary_election')
    e=election(date,slug,title,'Constitutional Assembly' if year==1905 else 'National Assembly',None,series='montenegro-monarchy-parliament')
    e['sources']=[source('Parliament of Montenegro: historical development',HISTORY),source('Historical election account and seat grouping (secondary)',url)]
    e['voteBasis']='Historical seat groups; popular votes and denominator unavailable'
    e['summary']='Election under the Montenegrin monarchy. No verified national popular-vote table or turnout denominator is available in the checked sources.'
    e['notes']='Partial historical coverage. Date retained as published; historical dates may be expressed in old/new style in original documents. No present-day party profile or ideology is assigned to historical political groups. Seats describe the source’s grouping and may include appointed or ex-officio members; they must not be interpreted as exact party-list mandates. Chamber-wide majority threshold is left null where chamber size cannot be established consistently.'
    if year==1905:
        result(e,'Elected representatives — non-party assembly','Non-party representatives',seats=60)
        e['notes']+=' The source text describes 56 district representatives and four town representatives, totalling 60; its infobox instead refers to 76. The conflicting chamber total is left null. The assembly accepted the constitution rather than electing a party government.'
    if year==1906:
        result(e,'Club members / People’s Party and aligned independents','Club members and aligned independents',seats=51,color='#63c3d0')
        e['notes']+=' The historical account records 51 seats for the Club / People’s Party grouping and a prescribed 62 elected plus 14 appointed members. Other accounts distinguish 59 actually elected deputies. The full realised chamber size and remaining affiliation breakdown are unresolved; no 25-seat “Other” party is invented. Candidates initially stood as individuals; later parliamentary alignment is not a party-vote result.'
    if year==1907:
        result(e,'True People’s Party and aligned independents','Royalist group and aligned independents',seats=76,color='#6495ed')
        e['notes']+=' The secondary account groups all 76 members with the royalists, including aligned independents and appointees, without an elected/appointed breakdown. The People’s Party boycotted after intimidation; the aggregate is retained, and turnout, votes and a confirmed realised chamber total remain unassessed.'
    if year==1911:
        result(e,'True People’s Party and aligned independents','Royalist group and aligned independents',seats=53,color='#6495ed')
        result(e,'Opposition independents (including banned People’s Party members)','Opposition independents',seats=9)
        e['notes']+=' The secondary table allocates 53 and nine seats (62 total), but does not reconcile this with earlier accounts of appointed/ex-officio members. Chamber size is left null rather than assuming the table covers all members.'
    if year==1914:
        e['totalSeats']=62;e['majorityThreshold']=32
        for name,key,s,c in [('People’s Party','Historical NS',25,'#63c3d0'),('Mijušković group','Mijušković group',17,'#99b3ff'),('True People’s Party','Historical PNS',6,'#6495ed'),('United Serb Youth','United Serb Youth',2,'#809ac7'),('Independent appointed members','Appointed independents',12,'#808080')]:result(e,name,key,seats=s,color=c)
        e['notes']+=' The source’s composition table totals 48 elected and 14 appointed members: the True People’s Party grouping contains four elected and two appointed members. The remaining 12 appointees are independent in that table. This 62-member composition is preserved without extrapolating a different constitutional seat total.'

e=election('1918-11-21','podgorica-assembly','Podgorica Assembly — indirect delegate selection','Podgorica Assembly',169,'indirect','montenegro-podgorica-assembly-1918')
e['sources']=[source('Parliament of Montenegro: 2018 resolution, selection process and 169 delegates','https://zakoni.skupstina.me/zakoni/web/dokumenta/sjednice-skupstine/179/2523-..pdf')]
e['summary']='Commissioners chosen at public meetings selected delegates to the contested Podgorica Assembly. This was a special assembly, not an ordinary election under Montenegro’s constitution.'
e['voteBasis']='Indirect delegate selection; ballots and denominator unavailable'
result(e,'Selected delegates — affiliations not individually tabulated','Affiliation unallocated',seats=169)
e['notes']='The parliamentary resolution dates final delegate selection to 21 November, after public meetings chose commissioners; 169 were selected and 160 attended. The meeting ran 24–29 November, so the opening date is not used as the election date. The resolution describes the process as lacking electoral registers, identification, polling boards and minutes, and regards the assembly and its decisions as illegitimate. Its retrospective assessment is attributed to that source, not presented as a neutral contemporary certification. No national vote share, turnout or party allocation is inferred.'
e['majorityThreshold']=None

def historical(date,slug,title,body,size,method,year,renewal=False,end=''):
    e=election(date,slug,title,body,size,method,'montenegro-socialist-'+slug,end)
    e['sources']=[source('UNDP: 80 years of women’s political history — election dates, chambers and selection rules',UNDP),source('Parliament of Montenegro: chamber membership, 1946–1990',PARLIAMENT)]
    e['voteBasis']='Seats filled; individual vote counts and electoral denominator unavailable'
    e['summary']=f'{body}: '+(f'half-renewal of {size//2} of {size} seats.' if renewal else f'{size} members selected.')+' The source does not tabulate a competitive party vote.'
    e['notes']='Partial historical results: the authoritative historical accounts give chamber membership and election dates, but not complete ballots, turnout denominators or party affiliations. The aggregate result row counts seats filled, not membership of the Communist Party or League of Communists. Votes, share, electoral votes and previous party seats remain null. “Final” refers only to the sourced historical seat outcome, not a recovered final ballot certification. This was a single-party political system; no modern party label or ideology is backfilled.'
    if not method:e['notes']+=' The occupational-electorate selection is described by the source, but its direct/indirect mechanism is not established sufficiently for the model’s binary method flag; that optional flag is omitted rather than guessed.'
    result(e,'Selected representatives — party affiliation not tabulated','Affiliation unallocated',seats=size//2 if renewal else size)
    if renewal:
        e['round']='Half-renewal'
        e['notes']+=f' Only {size//2} seats were filled at this election; the other {size//2} incumbents were retained. Result seats therefore deliberately fall short of the full {size}-seat chamber; retained mandates are not recorded as newly won seats.'
    return e

historical('1946-11-03','constitutional-assembly','Constitutional Assembly — first postwar election','Constitutional Assembly',107,'direct',1946)['notes']+=' There were 107 single-member electoral units. Women could vote for the first time. The assembly continued as the National Assembly in January 1947; this institutional conversion is not a new election. UNDP contains an isolated introductory 1945 typo; its detailed chronology and the parliamentary archive establish 3 November 1946.'
historical('1950-10-08','national-assembly','National Assembly — single-party election','National Assembly',161,'direct',1950)
for year,rd,pd,rs,ps in [(1953,'1953-11-22','1953-11-26',70,52),(1958,'1958-03-23','1958-03-28',92,58)]:
    historical(rd,'republican-council','National Assembly — Republican Council','Republican Council',rs,'direct',year)['notes']+=' The Republican Council represented citizens; seat ratios were one representative per 6,000 inhabitants in 1953 and per 5,000 in 1958.'
    historical(pd,'producers-council','National Assembly — Council of Producers','Council of Producers',ps,None,year)['notes']+=' The electorate consisted of producers in production, transport and trade, with sector-based representation. This is not the same electorate as the Republican Council.'

chambers=[('republican-council','Republican Council',70,'direct'),('economic-council','Economic Council',46,'indirect'),('education-cultural-council','Education and Cultural Council',46,'indirect'),('social-health-council','Social and Health Council',46,'indirect'),('organisational-political-council','Organisational and Political Council',46,'indirect')]
for year in [1963,1965,1967,1969]:
    for slug,body,size,method in chambers:
        if year==1969 and slug=='organisational-political-council':slug,body='communes-council','Council of Communes'
        if year==1963:date='1963-06-16' if slug=='republican-council' else '1963-07-03' if slug=='organisational-political-council' else '1963-06-03'
        if year==1965:date='1965-04-18' if slug=='republican-council' else '1965-04-04'
        if year==1967:date='1967-04-23'
        if year==1969:date='1969-04-13' if slug=='republican-council' else '1969-04-23'
        e=historical(date,slug,('Assembly — '+body+(' half-renewal' if year in [1965,1967] else '')),body,size,method,year,year in [1965,1967])
        if slug=='republican-council':
            e['notes']+=' Under the 1963 system, municipal assembly selection preceded direct citizen voting: 3 and 16 June 1963; 4 and 18 April 1965. The record uses the final direct-vote date where the source distinguishes it. The 1967 account gives 23 April without separate stage dates. In 1969 the Republican Council was directly elected.'
        else:e['notes']+=' The vocational councils were selected by municipal assemblies; in 1969 the economic, education-cultural and social-health councils were selected by bodies combining municipal councillors and workplace delegates. The Council of Communes was elected by municipal assemblies.'
        if year==1963 and slug=='organisational-political-council':e['notes']+=' UNDP prints 3 July for this council while the other councils were selected on 3 June. That stated council-specific date is retained; the month has not been silently corrected. An original electoral return is still needed to resolve whether it is a typographical error.'
        if year==1969:e['notes']+=' The 1969 constitutional changes ended staggered renewals; all seats were renewed, and the Council of Communes replaced the Organisational and Political Council.'

for year,date in [(1974,'1974-04-25'),(1978,'1978-04-13'),(1982,'1982-04-13'),(1986,'1986-04-21'),(1989,'1989-06-18')]:
    for slug,body,size in [('associated-labour-council','Council of Associated Labour',65 if year==1974 else 75),('municipalities-council','Council of Municipalities',35 if year==1974 else 55),('socio-political-council','Socio-Political Council',35)]:
        d='1989-06-12' if year==1989 and slug=='associated-labour-council' else date
        end='1989-06-13' if year==1989 and slug=='associated-labour-council' else ''
        e=historical(d,slug,'Assembly — '+body,body,size,'indirect',year,end=end)
        e['notes']+=' The 1974 constitutional order used a delegate system: representatives of self-managing labour organisations, municipal communities and socio-political organisations constituted separate councils. The method flag describes selection to the republic-level chamber, not voting for the underlying delegations. No lower-stage ballots are treated as a national popular vote.'
        if year==1978:e['notes']+=' Council sizes 75 + 55 + 35 reconcile to the 165-member assembly in the parliamentary archive. UNDP contains a stray 135-member sentence in this section, followed by the correct 165 total and explanation of the enlargement; the inconsistent sentence is not used.'
        if year==1989:e['snap']=True;e['notes']+=' The 1986–1990 mandate was shortened following the 1988–1989 protests. Labour Council selection ran 12–13 June; the other two councils were selected on 18 June.'

# Cross-chamber links join one election cycle, never merge different electorates.
for e in records:
    year=e['startDate'][:4]
    siblings=[r['id'] for r in records if r['id']!=e['id'] and r['startDate'][:4]==year and 'socialist' in r['seriesId']]
    if 'socialist' in e['seriesId'] and siblings:e['linkedElectionIds']=siblings
records.sort(key=lambda e:(e['startDate'],e['id']))
used={r['partyId'] for e in records for r in e['results'] if r.get('partyId')}
profiles=[p for p in parties.values() if p['id'] in used]
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'parties.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2)+'\n')
(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,countryId='me',recordCount=len(records),partyCount=len(profiles),nationalElections=audit,
    historicalQualifications=['Historical popular-vote and turnout data unavailable; no party affiliation assigned to aggregates.',
    '1905–1911 realised chamber denominators unresolved in checked accounts.',
    '1953/1958 Producers’ Council direct/indirect mechanism not asserted.',
    '1963 Organisational and Political Council month differs from other council dates in UNDP.',
    '1965/1967 records cover half-renewals; retained members are not election wins.'],
    sourceExtractHashes={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['national-results.json','party-name-reference.json']}),ensure_ascii=False,indent=2)+'\n')
print(f'Built {len(records)} records and {len(profiles)} party profiles; 12 modern vote tables checked, 2006 gap retained.')
