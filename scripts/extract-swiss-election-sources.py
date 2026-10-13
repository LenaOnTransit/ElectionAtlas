from pathlib import Path
from bs4 import BeautifulSoup
import json,sys,re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from us_presidential_html import Tables,expand
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'scripts/swiss-election-import';data={}
for k,u in json.loads((out/'links.json').read_text()).items():
 p=ROOT/'.cache/switzerland'/(k+'.html')
 if not p.exists():continue
 s=BeautifulSoup(p.read_text(),'html.parser')
 inf=s.select_one('table.infobox');meta=inf.get_text(' ',strip=True) if inf else ''
 ts=[]
 for t in s.select('table.wikitable'):
  h=t.find_previous(['h2','h3','h4']);heading=h.get_text(' ',strip=True).replace('[ edit ]','').strip() if h else ''
  text=t.get_text(' ',strip=True)
  if not ('Votes' in text or 'Seats' in text or 'For' in text) or heading.lower() not in ['result','results','national results','first round','second round','third round','voting','vote','election results','national council','council of states']:continue
  for x in t.select('sup,script,style'):x.decompose()
  for x in t.select('[rowspan],[colspan]'):
   for attr in ['rowspan','colspan']:
    if x.has_attr(attr):x[attr]=re.match(r'\d+',str(x[attr])).group()
  parser=Tables();parser.feed(str(t));rows=expand(parser.tables[0]['rows']);cells={}
  rows=[[{'text':c['text'],'cell':cells.setdefault(id(c),len(cells))} for c in row] for row in rows]
  ts.append({'heading':heading,'rows':rows})
 data[k]={'infobox':meta,'tables':ts}
(out/'source-tables.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
states={}
for p in sorted((ROOT/'.cache/switzerland').glob('*_Swiss_states_german.html')):
 s=BeautifulSoup(p.read_text(),'html.parser');year=int(p.name[:4])
 for t in s.select('table'):
  h=t.find_previous(['h2','h3','h4']);heading=h.get_text(' ',strip=True) if h else ''
  if not heading.startswith('Sitzverteil'):continue
  for sup in t.select('sup'):sup.decompose()
  rows=[[c.get_text(' ',strip=True) for c in tr.select('th,td')] for tr in t.select('tr')]
  if not rows or not rows[0] or rows[0][0]!='Partei':continue
  rows=[r for r in rows[1:] if len(r)>=2]
  allocation=[]
  for r in rows:
   if r[0].lower() in ('total','gesamt','insgesamt','summe'):continue
   v=r[1].replace('−','-').strip()
   if v in ('–','—','-',''):v='0'
   if not v.isdigit():continue
   allocation.append({'label':r[0],'seats':int(v)})
  if allocation:
   assert sum(r['seats'] for r in allocation)<=(46 if year>=1979 else 44),(year,allocation)
   states[str(year)]={'rows':allocation,'source':'https://de.wikipedia.org/wiki/Schweizer_Parlamentswahlen_'+str(year)}
(out/'states-supplement.json').write_text(json.dumps(states,ensure_ascii=False,indent=2)+'\n')
for k,item in data.items():
 print(k,item['infobox'][0:130],[(t['heading'],len(t['rows']),[c['text'] for c in t['rows'][0]]) for t in item['tables']])
