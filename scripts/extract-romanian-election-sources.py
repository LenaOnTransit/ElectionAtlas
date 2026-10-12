from pathlib import Path
from bs4 import BeautifulSoup
import json,sys,re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from us_presidential_html import Tables,expand
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'scripts/romanian-election-import';data={}
for k,u in json.loads((out/'links.json').read_text()).items():
 p=ROOT/'.cache/romania'/(k+'.html')
 if not p.exists():continue
 s=BeautifulSoup(p.read_text(),'html.parser')
 inf=s.select_one('table.infobox');meta=inf.get_text(' ',strip=True) if inf else ''
 ts=[]
 for t in s.select('table.wikitable'):
  h=t.find_previous(['h2','h3','h4']);heading=h.get_text(' ',strip=True).replace('[ edit ]','').strip() if h else ''
  text=t.get_text(' ',strip=True)
  if not ('Votes' in text or 'Seats' in text) or heading.lower() not in ['results','chamber of deputies','assembly of deputies','senate','president','presidential election','chamber of deputies results','senate results','national results','first round','second round']:continue
  for x in t.select('sup,script,style'):x.decompose()
  for x in t.select('[rowspan],[colspan]'):
   for attr in ['rowspan','colspan']:
    if x.has_attr(attr):x[attr]=re.match(r'\d+',str(x[attr])).group()
  parser=Tables();parser.feed(str(t));rows=expand(parser.tables[0]['rows']);cells={}
  rows=[[{'text':c['text'],'cell':cells.setdefault(id(c),len(cells))} for c in row] for row in rows]
  ts.append({'heading':heading,'rows':rows})
 data[k]={'infobox':meta,'tables':ts}
(out/'source-tables.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
for k,item in data.items():
 print(k,item['infobox'][0:130],[(t['heading'],len(t['rows']),[c['text'] for c in t['rows'][0]]) for t in item['tables']])
