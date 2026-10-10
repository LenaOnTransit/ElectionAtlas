"""Assign official candidate affiliations to existing CountryParty profiles.

PSTRANA identifies personal membership; VSTRANA identifies the electoral list.
For non-members, a sponsoring list is linked and explicitly labelled nomination.
New profile colours are an editorial palette, not claims about official branding.
"""
import colorsys
import json
import uuid
from pathlib import Path

cache = Path('.cache/czech-2026')
out = Path('scripts/czech-senate-2026-update')
saved = json.loads((cache / 'saved-parties.json').read_text())
by_name = {p['name']: p for p in saved}
known = {1:'KDU-ČSL',53:'Civic Democratic Party',166:'Mayors and Independents',703:'Mayors for the Liberec Region',720:'Czech Pirate Party',721:'TOP 09',768:'ANO 2011',1187:'SEN 21'}
profiles = {code: by_name[name] for code, name in known.items()}
official = {p['VSTRANA']:p for p in json.loads((cache / 'parties.json').read_text())['položky']}
for code, p in official.items():
    if code not in profiles and p['NAZEVCELK'] in by_name:
        profiles[code] = by_name[p['NAZEVCELK']]
register = {(r['OBVOD'],r['CKAND']):r for r in json.loads((cache / 'register.json').read_text())['polozky'] if r['PLATNOST']=='A'}
records = json.loads((out / 'records.json').read_text())
new = []
assignments = []
for e in records[2:]:
    if any(r['winner'] for r in e['results']):
        e['resultStatus'] = 'final'
        e['resultCoverage'] = 'complete'
    for row in e['results']:
        _,_,_,district,candidate = row['id'].split('-')
        r = register[(int(district),int(candidate))]
        membership = r['PSTRANA']
        code = membership if membership != 99 else r['VSTRANA']
        if code == 80:
            row.update(party='Independent',color='#808080',ideologyIds=[])
            row.pop('partyId',None)
            profile = None
        else:
            if code not in profiles:
                p = official[code]
                hue = (code * 0.61803398875) % 1
                color = '#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(hue,.40,.62))
                profile = {'id':str(uuid.uuid5(uuid.NAMESPACE_URL,f'https://volby.gov.cz/czech-electoral-party/{code}')),'country_id':'cz','name':p['NAZEVCELK'],'short_name':p['ZKRATKAV30'],'color':color,'ideology_ids':[],'archived':False,'notes':f"Official Czech electoral-party code {code}; type {p['TYPVS']} (S: party/movement; K: electoral coalition). Source: https://volby.gov.cz/opendata/se2026/json/cvs.json . Added for the 2026 Senate candidate register: https://volby.gov.cz/opendata/se2026/json/serk.json . Colour is a stable editorial display palette, not verified official branding. No ideology has been inferred."}
                profiles[code] = profile
                new.append(profile)
            profile = profiles[code]
            label = profile['name'] if code in known else official[code]['ZKRATKAV30']
            if membership == 99:
                label = 'Independent · '+label+' nomination'
            elif membership != r['VSTRANA']:
                label += ' · nominated by '+official[r['VSTRANA']]['ZKRATKAV30']
            assert len(label) <= 200
            row.update(partyId=profile['id'],party=label,color=profile['color'],ideologyIds=list(profile['ideology_ids']))
        assignments.append({'resultId':row['id'],'membershipCode':membership,'electoralListCode':r['VSTRANA'],'linkedCode':code if profile else None,'partyId':profile['id'] if profile else None})
    e['notes'] += ' Candidate profile links and colours use official registered party membership (PSTRANA). Non-members are explicitly labelled Independent and linked to their nominating electoral list (VSTRANA), where present. Coalition nominations remain named separately from personal party membership. Existing profile colours are preserved; colours for newly added profiles are an editorial display palette. No personal ideology is inferred.'
records[0]['notes'] += ' Linked district candidate colours now use saved party profiles. Official membership and coalition nomination are distinguished in each candidate label. New profile colours are editorial display choices.'
records[1] = next(r['data'] for r in json.loads((cache/'baseline.json').read_text()) if r['id']==records[1]['id'])
(out/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(out/'party-assignments.json').write_text(json.dumps(assignments,ensure_ascii=False,indent=2)+'\n')
(out/'parties.json').write_text(json.dumps(saved+new,ensure_ascii=False,indent=2)+'\n')
(cache/'new-parties.json').write_text(json.dumps(new,ensure_ascii=False)+'\n')
print(f'{len(assignments)} candidate affiliations verified; {len(new)} new party/coalition profiles; existing colours preserved.')
