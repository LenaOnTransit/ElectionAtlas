"""Check certified CNE national counts against the import; requires cached pdftotext output."""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parent/'portugal-election-import';C=P.parents[1]/'.cache/portugal';R=json.loads((P/'records.json').read_text());checks=[]
e=next(e for e in R if e['id']=='world-portugal-2025-assembly');text=(C/'2025-map.txt').read_text()
mapping={'ADN':'National Democratic Alternative','B.E.':'Left Bloc','CH':'Chega','E':'Ergue-te','IL':'Liberal Initiative','JPP':'Together for the People','L':'LIVRE','MPT':'Earth Party','NC':'We, the Citizens!','ND':'Nova Direita','PAN':'People Animals Nature','PCP-PEV':'Unitary Democratic Coalition','PCTP/MRPP':"Portuguese Workers' Communist Party",'PLS':'Liberal Social Party','PPD/PSD.CDS-PP':'AD – PSD/CDS Coalition','PPD/PSD.CDS-PP.PPM':'Coalition PSD/CDS/PPM','PPM':"People's Monarchist Party",'PS':'Socialist Party','PTP':'Portuguese Labour Party','R.I.R.':'React, Include, Recycle','VP':'Volt Portugal'}
lines=text.splitlines()
for code,name in mapping.items():
 i=next(i for i,s in enumerate(lines) if re.match(r'^'+re.escape(code)+r'\s+Número\s',s))
 votes=int(re.split(r'\s{2,}',lines[i].strip())[-1].replace(' ',''));seatline=next(s for s in lines[i+1:i+45] if re.match(r'\s*md\s',s));seats=int(re.split(r'\s{2,}',seatline.strip())[-1]);row=next(r for r in e['results'] if r['name']==name)
 assert (row['votes'],row['seats'])==(votes,seats),(name,row,votes,seats)
 checks.append(dict(election=e['id'],name=name,votes=votes,seats=seats,source='2025_ar_mapa_oficial_dr.pdf'))
for rd in ['1','2']:
 e=next(e for e in R if e['body']=='President' and e['startDate'].startswith('2026') and e['round']==rd);text=(C/('2026-round'+rd+'.txt')).read_text()
 for row in e['results']:
  formatted=f"{row['votes']:,}".replace(',',' ');assert re.search(r'(?<!\d)'+re.escape(formatted)+r'(?!\d)',text),row
  checks.append(dict(election=e['id'],name=row['name'],votes=row['votes'],source='2026 presidential certified map round '+rd))
assert len(checks)==34
(P/'primary-reconciliation.json').write_text(json.dumps(dict(checks=checks,notes='2025 legislative national votes and mandates; both 2026 presidential national tallies. Published certifications retain their stated tabulation discrepancies.'),ensure_ascii=False,indent=2)+'\n')
print(len(checks),'certified national result rows reconciled')
