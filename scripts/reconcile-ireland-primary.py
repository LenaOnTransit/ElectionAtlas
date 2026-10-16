"""Check national counts against official Oireachtas / Presidential Returning Officer PDFs."""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parent/'ireland-election-import';C=P.parents[1]/'.cache/ireland';R=json.loads((P/'records.json').read_text());checks=[];unmatched=[]
for y in [2016,2020,2024]:
 e=next(e for e in R if e['body']=='Dáil Éireann' and e['startDate'].startswith(str(y)));text=(C/('dail-'+str(y)+'.txt')).read_text();national='\n'.join(s for s in text.splitlines() if re.match(r'\s*Totals?\s',s,re.I))
 for r in e['results']:
  token=f"{r['votes']:,}";found=bool(re.search(r'(?<![\d,])'+re.escape(token)+r'(?![\d,])',national))
  (checks if found else unmatched).append(dict(election=e['id'],name=r['name'],votes=r['votes'],source='Oireachtas result handbook '+str(y),scope='national total rows'))
text=(C/'presidential-handbook.txt').read_text()
for e in R:
 if e['body']!='President':continue
 for r in e['results']:
  if r['votes'] is None:continue
  assert re.search(r'(?<![\d,])'+re.escape(f"{r['votes']:,}")+r'(?![\d,])',text),(e['id'],r)
  checks.append(dict(election=e['id'],name=r['name'],votes=r['votes'],source='Presidential Returning Officer: 1938–2025 result handbook',scope='published presidential count'))
assert not unmatched,unmatched
(P/'primary-reconciliation.json').write_text(json.dumps(dict(checks=checks,notes='National first-preference vote values found in official Oireachtas national-total rows for 2016, 2020 and 2024, and every contested presidential candidate tally. Historical discrepancies and unopposed returns are retained explicitly in records.'),ensure_ascii=False,indent=2)+'\n');print(len(checks),'primary-source candidate/party vote checks passed')
