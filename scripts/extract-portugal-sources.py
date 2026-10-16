"""Extract cached public historical result tables with row/column span handling."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/portugal-election-import';CACHE=ROOT/'.cache/portugal'
links=json.loads((OUT/'links.json').read_text());out=[]
def clean(c):
 s=BeautifulSoup(str(c),'html.parser')
 for x in s.select('sup'):x.decompose()
 return re.sub(r'\s+',' ',s.get_text(' ',strip=True)).strip()
def grid(t):
 rows=[];pending={}
 for tr in t.find_all('tr'):
  if tr.find_parent('table')!=t:continue
  cells={i:v[0] for i,v in pending.items()};pending={i:(v[0],v[1]-1) for i,v in pending.items() if v[1]>1};i=0
  for c in tr.find_all(['th','td'],recursive=False):
   while i in cells:i+=1
   text=clean(c);cs=int(c.get('colspan',1));rs=int(c.get('rowspan',1))
   for j in range(i,i+cs):
    cells[j]=text
    if rs>1:pending[j]=(text,rs-1)
   i+=cs
  rows.append([cells.get(j,'') for j in range(max(cells,default=-1)+1)])
 return rows
for name,url in links.items():
 p=CACHE/(name+'.html')
 if not p.exists():continue
 raw=p.read_bytes();s=BeautifulSoup(raw,'html.parser');tables=[]
 for t in s.select('table.wikitable'):
  text=t.get_text(' ',strip=True)
  if not ('Party' in text or 'Candidate' in text) or 'Total' not in text or not ('Votes' in text or 'Seats' in text):continue
  if len(text)>16000 or 'Constituency' in text[:200] or 'Municipality' in text[:200]:continue
  tables.append(grid(t))
 prose=' '.join(clean(p) for p in s.select('p')[:7]);info=s.select_one('table.infobox');infotext=clean(info) if info else ''
 out.append(dict(name=name,url=url,sha256=hashlib.sha256(raw).hexdigest(),prose=prose,infobox=infotext,tables=tables))
(OUT/'source-extract.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(len(out),'pages;',sum(bool(x['tables']) for x in out),'with selected tables')
for x in out:
 if not x['tables']:print('NO TABLE',x['name'],x['prose'][:140])
