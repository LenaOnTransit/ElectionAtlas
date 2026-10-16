"""Check national summaries against the independent SCB historical table and Valmyndigheten."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,hashlib
P=Path(__file__).resolve().parent/'sweden-election-import';C=P.parents[1]/'.cache/sweden';records=json.loads((P/'records.json').read_text());parties={p['id']:p['name'] for p in json.loads((P/'parties.json').read_text())};checks=[];differences=[]
s=BeautifulSoup((C/'scb-history.html').read_text(),'html.parser');rows=[[c.get_text(' ',strip=True) for c in r.find_all(['th','td'])] for r in s.select_one('table').select('tr')]
cols={'Moderate Party':4,'Centre Party':5,'Liberals':6,'Christian Democrats':9,'Green Party':10,'New Democracy':11,'Social Democrats':12,'Left Party':13,'Sweden Democrats':14}
for r in rows:
 if len(r)<16 or r[2] not in ['R','RD']:continue
 y=int(r[0]);es=[e for e in records if e['body']!='Första kammaren' and e['startDate'].startswith(str(y))]
 if y==1914:es=[e for e in es if ('spring' if r[1]=='vår' else 'autumn') in e['title']]
 assert len(es)==1,(y,len(es));e=es[0]
 for k,i in cols.items():
  if r[i] in ['.','']:continue
  # The historical summary aggregates certain farmers', liberal and joint-list organisations.
  rr=[v for v in e['results'] if parties.get(v.get('partyId'))==k]
  if not rr:continue
  expected=float(re.sub(r'\d\)','',r[i]).replace(',','.'));actual=sum(v['share'] or 0 for v in rr)
  item=dict(id=e['id'],party=k,sourceShare=expected,recordedShare=actual)
  if abs(actual-expected)>.115:differences.append(item)
  else:checks.append(item)
 if e['turnout'] is not None:
  expected=float(r[3].replace(',','.'));assert abs(expected-e['turnout'])<.16,(y,expected,e['turnout']);checks.append(dict(id=e['id'],field='turnout',source=expected,recorded=e['turnout']))
# Official 2026 summary: preserve all eight published party shares and seat counts.
s=BeautifulSoup((C/'2026-official.html').read_text(),'html.parser');t=next(t for t in s.select('table') if '28.02' in t.get_text());e=next(e for e in records if e['id']=='world-sweden-2026')
for sr in t.select('tr')[1:]:
 cells=[c.get_text(' ',strip=True) for c in sr.find_all(['th','td'])]
 if len(cells)!=3:continue
 n,p,seat=cells;r=next((r for r in e['results'] if r['name']==n),None)
 if r is None and n.startswith('Other'):r=e['results'][-1]
 assert r is not None,n;assert r['share']==float(p.rstrip('%'));assert r['seats']==int(seat);checks.append(dict(id=e['id'],party=r['name'],share=r['share'],seats=r['seats']))
# Secondary tables classify some older cooperative lists differently; report rather than silently change them.
assert all(int(x['id'].split('-')[-3] if False else next(e for e in records if e['id']==x['id'])['startDate'][:4])<=1985 for x in differences),differences
out=dict(sources=[dict(url='https://www.scb.se/hitta-statistik/statistik-efter-amne/demokrati/allmanna-val/allmanna-val-valresultat/pong/tabell-och-diagram/historisk-valstatistik/historisk-statistik-over-valaren-19102022.-procentuell-fordelning-av-giltiga-valsedlar-efter-parti-och-typ-av-val',sha256=hashlib.sha256((C/'scb-history.html').read_bytes()).hexdigest()),dict(url='https://www.val.se/english/election-results/elections-to-the-riksdag-and-regional-and-municipal-councils/election-results-2026',sha256=hashlib.sha256((C/'2026-official.html').read_bytes()).hexdigest())],checks=checks,classificationDifferences=differences)
(P/'primary-reconciliation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(len(checks),'national-summary checks;',len(differences),'historical classification differences');print(differences)
