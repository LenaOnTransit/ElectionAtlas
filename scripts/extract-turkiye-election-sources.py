"""Extract cached public result tables without publishing or modifying the database."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,subprocess,xml.etree.ElementTree as ET,hashlib
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/turkiye';OUT=ROOT/'scripts/turkiye-election-import'
def grid(table):
 rows=[];pending={}
 for ri,tr in enumerate(table.find_all('tr')):
  row=[];ci=0
  def carried():
   nonlocal ci
   while ci in pending:
    cell,left=pending[ci];row.append(cell);left-=1
    if left:pending[ci]=(cell,left)
    else:del pending[ci]
    ci+=1
  for td in tr.find_all(['td','th'],recursive=False):
   carried();text=re.sub(r'\[[^]]*\]','',td.get_text(' ',strip=True)).strip()
   cell={'text':text,'cell':f'{ri}-{ci}','links':[{'text':a.get_text(' ',strip=True),'href':a.get('href')} for a in td.find_all('a')],'style':td.get('style','')}
   for _ in range(int(td.get('colspan',1))):
    row.append(cell)
    if int(td.get('rowspan',1))>1:pending[ci]=(cell,int(td.get('rowspan',1))-1)
    ci+=1
  carried()
  if row:rows.append(row)
 return {'rows':rows}
tables={}
for p in sorted(CACHE.glob('*.html')):
 if not p.name.startswith(('parliament-','senate-','president-','parliament2023')):continue
 key='parliament-2023' if p.stem=='parliament2023' else p.stem
 soup=BeautifulSoup(p.read_text(),'html.parser');ts=[]
 for t in soup.find_all('table'):
  txt=t.get_text(' ',strip=True)
  if 'Votes' in txt and ('Seats' in txt or 'Candidate' in txt) and ('Registered voters' in txt or 'Total MP' in txt):ts.append(grid(t))
 if ts:tables[key]=ts
(OUT/'source-tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2)+'\n')
# Poppler coordinates preserve empty historical cells: whitespace splitting cannot.
primary={}
for name,years in [('historical',[1977,1973,1969,1965,1961,1957,1954,1950]),('post1983',[2007,2002,1999,1995,1991,1987,1983])]:
 xml=subprocess.check_output(['pdftotext','-bbox',str(CACHE/(name+'.pdf')),'-'],text=True)
 words=[dict(text=w.text or '',x=float(w.attrib['xMin']),right=float(w.attrib['xMax']),y=float(w.attrib['yMin'])+pi*1000) for pi,page in enumerate([p for p in ET.fromstring(xml).iter() if p.tag.endswith('page')]) for w in page if w.tag.endswith('word')]
 headers=[w for w in words if w['text']==str(years[0]) and w['y']>50]
 hy=headers[0]['y'];heads=sorted([w for w in words if abs(w['y']-hy)<1 and w['text'] in map(str,years)],key=lambda w:w['x'])
 assert len(heads)==len(years),(name,heads)
 centers=[w['right'] for w in heads];cutoff=heads[0]['right']-40;name_cutoff=min(w['x'] for w in words if w['text']=='Alınan')-2
 lines=[]
 for w in sorted(words,key=lambda w:(w['y'],w['x'])):
  if not lines or abs(w['y']-lines[-1][0]['y'])>1:lines.append([w])
  else:lines[-1].append(w)
 result={str(y):{'rows':[],'sourceFile':name+'.pdf'} for y in years};groups=[];group=None
 for line in lines:
  label=' '.join(w['text'] for w in line if w['x']<cutoff)
  cells={str(years[min(range(len(centers)),key=lambda i:abs(w['right']-centers[i]))]):w['text'] for w in line if w['x']>=cutoff and re.fullmatch(r'\d[\d.,]*',w['text'])}
  if 'Alınan oy sayısı' in label:
   group={'top':line[0]['y'],'votes':cells};groups.append(group)
  elif 'Kazandığı MV sayısı' in label and group is not None:group.update(seats=cells,bottom=line[0]['y'])
  elif 'Oy oranı' in label and group is not None:group['share']=cells
  elif cells:
   for y,v in cells.items():result[y][label]=v
 for g in groups:
  names=[w for w in words if w['x']<name_cutoff and g['top']-1<=w['y']<=g['bottom']+1]
  pname=' '.join(w['text'] for w in sorted(names,key=lambda w:(w['y'],w['x'])))
  for y,v in g['votes'].items():result[y]['rows'].append({'name':pname,'votes':int(v.replace('.','')),'share':float(g['share'].get(y,'0').replace(',','.')),'seats':int(g['seats'].get(y,'0'))})
 primary.update(result)
(OUT/'historical-primary-extract.json').write_text(json.dumps(primary,ensure_ascii=False,indent=2)+'\n')
manifest=json.loads((OUT/'download-manifest.json').read_text()) if (OUT/'download-manifest.json').exists() else {}
audit=[{'file':p.name,'source':manifest.get(p.stem,''),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(CACHE.iterdir()) if p.suffix in ['.html','.pdf'] and p.stat().st_size>1000]
(OUT/'source-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(f'{len(tables)} source-table sets; {len(primary)} official historical parliamentary tables')

party_sources=[]
for key,url in json.loads((OUT/'party-source-links.json').read_text()).items():
 p=CACHE/(key+'.html')
 if not p.exists():continue
 soup=BeautifulSoup(p.read_text(),'html.parser');box=soup.find('table',class_='infobox');rows=[]
 if box:
  for tr in box.find_all('tr'):
   h=tr.find('th');d=tr.find('td')
   if h and d and h.get_text(' ',strip=True) in ['Ideology','Founded','Political position','Preceded by']:
    rows.append({'label':h.get_text(' ',strip=True),'value':re.sub(r'\[[^]]*\]','',d.get_text(' ',strip=True)).strip()})
 party_sources.append({'source':url,'rows':rows})
(OUT/'party-source-extract.json').write_text(json.dumps(party_sources,ensure_ascii=False,indent=2)+'\n')
