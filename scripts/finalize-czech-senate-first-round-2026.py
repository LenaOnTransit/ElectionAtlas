"""Close the official first-round count without declaring future runoffs finished."""
import json
from pathlib import Path

out = Path('scripts/czech-senate-2026-update')
records = json.loads((out/'records.json').read_text())
parent, runoff, *districts = records
audit = json.loads((out/'audit.json').read_text())
assert audit['reportedPrecincts'] == audit['totalPrecincts']
assert all(e['live']['reporting'] == 100 for e in districts)
pending = [e for e in districts if not any(r['winner'] for r in e['results'])]
assert all(sum(r['advanced'] for r in e['results']) == 2 for e in pending)
assert len(pending) + audit['officialFirstRoundWinners'] == 27
reviewed = '2026-10-12'
for e in districts:
    won = any(r['winner'] for r in e['results'])
    e.update(resultStatus='final',resultCoverage='complete' if won else 'partial',checked=reviewed,
             summary='Final first-round results. '+('The seat was decided in the first round.' if won else 'The two officially advancing candidates contest the second round on 16–17 October.'),
             notes=e['notes']+' All first-round votes and signed district outcomes are now final. '+('The single district seat is allocated.' if won else 'Partial coverage refers only to the unresolved seat allocation; the first-round candidate vote table is complete. A second-round result must be recorded separately.'))
    e['live'].update(enabled=False,reporting=100,bulletin='First-round counting complete. '+('Senator elected in round one.' if won else 'Runoff candidates confirmed for 16–17 October.'))
parent.update(resultStatus='final',resultCoverage='partial',turnout=43.31,checked=reviewed,
              summary='First-round counting complete: five senators elected and 22 district runoffs scheduled for 16–17 October 2026.',
              notes='The overview retains the full 81-member Senate. The 2026 cycle renews 27 seats; 54 seats continue without election. First-round votes and district outcomes are final: five seats were decided and 22 require a runoff on 16–17 October. Overall allocation is partial because the runoff has not taken place. Existing overview party rows and historical metadata are preserved; full-chamber party composition is not inferred from the contested cohort. Each district vote share has its own denominator. All first-round live entries are disabled. Official final count: 5,021 precincts; 1,154,407 valid votes; turnout 43.31%. Final XML snapshot: '+audit['timestamp']+'.')
parent['live'].update(enabled=False,reporting=100,bulletin='Final first-round count: 5,021/5,021 precincts; 1,154,407 valid votes. Five seats decided; 22 district runoffs on 16–17 October. Full Senate: 81 seats.')
runoff.update(round='Second round',title='Senate — second round',status='scheduled',resultStatus='not-entered',resultCoverage='partial',checked=reviewed,
              summary='Second-round elections in the 22 districts not decided in round one, scheduled for 16–17 October 2026.',
              sources=parent['sources'],linkedElectionIds=[parent['id']]+[e['id'] for e in pending],
              notes='The first round is final. Five senators were elected in round one; the following 22 districts each elect one senator in the runoff on 16–17 October. This election has not yet taken place; no runoff votes or winners are entered. The 81-member Senate has 54 continuing seats. Confirmed first-round advancement pairs:\n'+'\n'.join(e['title']+': '+' versus '.join(r['name']+' ('+r['party']+')' for r in e['results'] if r['advanced']) for e in pending),
              live={'enabled':False,'reporting':None,'unit':'precincts','bulletin':'Runoff scheduled for 16–17 October; not live yet.','updated':audit['timestamp']})
audit.update(firstRoundFinal=True,runoffDistricts=len(pending),advancedCandidates=sum(r['advanced'] for e in pending for r in e['results']),turnout=43.31,reviewed=reviewed)
(out/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(f'Finalized {len(districts)} first-round district results; {audit["officialFirstRoundWinners"]} winners, {len(pending)} runoffs; live disabled for all {len(records)} records.')
