"""Build an auditable first-round snapshot; never infer winners from live leads.

Input: official XML, candidate register and electoral-party register downloaded
to .cache/czech-2026. Output uses the existing WorldElection model. This script
does not write to the database. Baseline updates require optimistic concurrency.
"""
import copy
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

cache = Path('.cache/czech-2026')
out = Path('scripts/czech-senate-2026-update')
baseline = json.loads((cache / 'baseline.json').read_text())
old = {r['id']: r['data'] for r in baseline}
parent = copy.deepcopy(old['world-czech-senate-2026'])
runoff = copy.deepcopy(old['world-calendar-cz-senate-2026-runoff'])
root = ET.parse(cache / 'results.xml').getroot()
ns = {'n': 'http://www.volby.cz/senat/'}
stamp = datetime.fromisoformat(root.attrib['DATUM_CAS_GENEROVANI']).replace(tzinfo=ZoneInfo('Europe/Prague'))
register = {(r['OBVOD'], r['CKAND']): r for r in json.loads((cache / 'register.json').read_text())['polozky'] if r['PLATNOST'] == 'A'}
parties = {r['VSTRANA']: r for r in json.loads((cache / 'parties.json').read_text())['položky']}
sources = [
    {'label': 'Czech Statistical Office — live official first-round results', 'url': 'https://volby.gov.cz/appdata/senat/20261009/odata/vysledky.xml'},
    {'label': 'Czech Statistical Office — candidate register', 'url': 'https://volby.gov.cz/opendata/se2026/json/serk.json'},
    {'label': 'Czech Statistical Office — live XML methodology', 'url': 'https://volby.gov.cz/opendata/se2026/SENAT_XML.htm'},
]
districts = []
seen = set()
reported = precincts = valid = elected = 0
for district in root.findall('n:OBVOD', ns):
    number = int(district.attrib['CISLO'])
    name = district.attrib['NAZEV']
    u = district.find('n:UCAST', ns).attrib
    count, total, votes = int(u['OKRSKY_ZPRAC']), int(u['OKRSKY_CELKEM']), int(u['PLATNE_HLASY'])
    reported += count
    precincts += total
    valid += votes
    rows = []
    for candidate in district.findall('n:KANDIDAT', ns):
        a = candidate.attrib
        key = (number, int(a['PORADOVE_CISLO']))
        registration = register[key]
        seen.add(key)
        assert registration['JMENO'] == a['JMENO'] and registration['PRIJMENI'] == a['PRIJMENI']
        label = parties[registration['VSTRANA']]['ZKRATKAV30']
        flag = a.get('ZVOLEN_1KOLO', '')
        winner = flag == 'ZVOLEN'
        assert not flag or count == total
        elected += winner
        rows.append({'id': f'cz-senate-2026-{number}-{key[1]}', 'name': a['JMENO'] + ' ' + a['PRIJMENI'], 'party': label, 'color': '#808080', 'votes': int(a['HLASY_1KOLO']) if count else None, 'share': float(a['HLASY_PROC_1KOLO']) if votes else None, 'seats': 1 if winner else 0, 'electoralVotes': None, 'winner': winner, 'advanced': flag == '2.KOLO'})
    assert sum(r['votes'] or 0 for r in rows) == votes
    e = copy.deepcopy(parent)
    for field in ('legitimacy', 'coalitionNotes', 'house', 'majorityThreshold', 'contests', 'geography', 'regionalOverview'):
        e.pop(field, None)
    e.update(id=f'world-cz-senate-2026-district-{number}-round-1', title=f'Senate — {name} (district {number})', body=f'Senate — electoral district {number}', round='First round', seriesId=parent['seriesId'], overviewId=parent['id'], linkedElectionIds=[parent['id']], status='held', publication='published', totalSeats=1, turnout=float(u['UCAST_PROC']) if count == total else None, resultStatus='provisional', resultCoverage='partial', voteBasis='First-round candidate votes within this electoral district', results=rows, sources=sources, checked=stamp.date().isoformat(), version=0, summary=f'Provisional first-round count for the {name} Senate district.', government='', notes='One seat in the 81-member Senate. Candidate percentages use this district’s valid first-round votes only. Zero reported precincts means results are not yet available. Seats/winner/advancement are entered only when the official XML publishes the signed district outcome; a current lead is not a win. A second round on 16–17 October is required if no candidate is officially elected in round one. Turnout is omitted until all district precincts report.', live={'enabled': True, 'reporting': float(u['OKRSKY_ZPRAC_PROC']), 'unit': 'precincts', 'bulletin': f"Official snapshot {stamp.strftime('%H:%M %Z')}: {count}/{total} precincts reported; {votes:,} valid first-round votes. Provisional count.", 'updated': stamp.isoformat()})
    districts.append(e)
control = root.find('n:CELKEM/n:UCAST', ns).attrib
assert len(districts) == 27 and seen == set(register)
assert (reported, precincts, valid) == tuple(int(control[k]) for k in ['OKRSKY_ZPRAC', 'OKRSKY_CELKEM', 'PLATNE_HLASY'])
parent.update(status='held', round='First round', totalSeats=81, resultStatus='provisional', resultCoverage='partial', turnout=None, checked=stamp.date().isoformat(), version=parent['version'] + 1, sources=sources, linkedElectionIds=[runoff['id']] + [e['id'] for e in districts], summary='2026 renewal of 27 seats in the 81-member Senate. Official first-round counting is in progress.', voteBasis='District candidate vote shares are shown in the linked electoral-district results.', notes='The overview retains the full Senate size of 81 seats. This election renews 27 seats; 54 seats are not being elected. Existing party rows and historical metadata are retained. Full chamber composition has not yet been updated from verified incumbent and elected-candidate data. Live district candidate counts are linked below; their percentages must not be added across districts or treated as a national party ballot. First round: 9–10 October 2026. Conditional second round: 16–17 October. No winner is inferred from a partial lead. This is a timestamped snapshot, not a continuously refreshing source. National turnout is omitted while reported precincts form an incomplete electorate.', live={'enabled': True, 'reporting': float(control['OKRSKY_ZPRAC_PROC']), 'unit': 'precincts', 'bulletin': f"Official first-round snapshot {stamp.strftime('%H:%M %Z')} on 10 October: {reported:,}/{precincts:,} precincts reported ({control['OKRSKY_ZPRAC_PROC']}%); {valid:,} valid votes counted. {elected}/27 seats officially decided in round one. Full Senate: 81 seats. Candidate results are available in the linked district pages. Counts are provisional; runoffs where required are scheduled for 16–17 October.", 'updated': stamp.isoformat()})
runoff.update(seriesId=parent['seriesId'], linkedElectionIds=[parent['id']], checked=stamp.date().isoformat(), version=runoff['version'] + 1)
records = [parent, runoff] + districts
(out / 'records.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
(out / 'results.xml').write_bytes((cache / 'results.xml').read_bytes())
audit = {'timestamp': stamp.isoformat(), 'reportedPrecincts': reported, 'totalPrecincts': precincts, 'validVotes': valid, 'districts': len(districts), 'candidates': len(seen), 'officialFirstRoundWinners': elected, 'chamberSize': 81, 'contestedSeats': 27}
(out / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps(audit))
