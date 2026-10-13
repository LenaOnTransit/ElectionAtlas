"""Extract cached Ministry final returns without combining different ballot rounds."""
from pathlib import Path
from bs4 import BeautifulSoup
import re,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/austrian-election-import';CACHE=ROOT/'.cache/austria'
def n(x):
 return int(re.sub(r'[.,\s]','',x)) if re.fullmatch(r'[\d.,\s]+',x) else None
out=[]
for p in sorted(CACHE.glob('nationalratswahl*.html')):
 s=BeautifulSoup(p.read_text(),'html.parser')
 t=next((t for t in s.select('main table') if 'Stimmen' in t.get_text() and ('Partei' in t.get_text() or 'Parteibezeichnung' in t.get_text()) and ('Mandate' in t.get_text() or 'Prozente' in t.get_text())),None)
 if not t:continue
 rows=[];has_seats='Mandate' in t.get_text()
 for r in t.select('tr'):
  td=[x.get_text(' ',strip=True) for x in r.select('td')]
  if len(td)<4:continue
  vi=len(td)-(3 if has_seats else 2);votes=n(td[vi]);seats=(n(td[-1]) if td[-1] not in ('','-','–') else 0) if has_seats else None
  if votes is None:continue
  assert not has_seats or seats is not None,(p.name,td)
  rows.append({'name':td[0],'short':td[1] if vi>1 else '', 'votes':votes,'seats':seats})
 year=int(re.search(r'\d{4}',p.name)[0]);out.append({'year':year,'key':p.stem,'source':'https://www.bmi.gv.at/412/nationalratswahlen/'+p.stem+'/start.html','rows':rows,'validVotes':sum(r['votes'] for r in rows),'seats':sum(r['seats'] for r in rows) if has_seats else None})
 assert not has_seats or out[-1]['seats']==(165 if year<1971 else 183),(p.name,out[-1])
 print(p.stem,len(rows),out[-1]['validVotes'],out[-1]['seats'])
# 1920 Ministry grouped returns include the delayed regional polls through1922.
rows=[{'name':name,'short':'','votes':v,'seats':ss} for name,v,ss in [('Christian Social Party',1245531,85),("Social Democratic Workers' Party",1072709,69),('German-national parties',514127,28),('Democratic parties',42826,1),('Other parties',105135,0)]]
out.append(dict(year=1920,key='nrw_1920_ergebnisse',source='https://www.bmi.gv.at/412/nationalratswahlen/files/nrw_1920_ergebnisse.pdf',rows=rows,validVotes=2980328,seats=183))
(OUT/'parliament-primary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
s=BeautifulSoup((CACHE/'official-pres-history.html').read_text(),'html.parser')
dates={1951:['05-06','05-27'],1957:['05-05'],1963:['04-28'],1965:['05-23'],1971:['04-25'],1974:['06-23'],1980:['05-18'],1986:['05-04','06-08'],1992:['04-26','05-24'],1998:['04-19'],2004:['04-25'],2010:['04-25'],2016:['04-24','05-22','12-04'],2022:['10-09']};counts={};out=[]
for t in s.select('table'):
 year=int(re.search(r'\d{4}',t.find_previous('h3').get_text())[0]);ri=counts.get(year,0);counts[year]=ri+1;c={}
 for row in t.select('tbody tr'):
  td=row.select('td')
  if len(td)>=2:c[td[0].get_text(' ',strip=True)]=n(td[1].get_text(strip=True))
 assert c and all(isinstance(v,int) for v in c.values())
 out.append({'id':f'world-austria-president-{year}-{dates[year][ri]}','candidates':c,'validVotes':sum(c.values()),'source':'https://www.bmi.gv.at/412/bundespraesidentenwahlen/historischer_rueckblick.html','caption':t.caption.get_text(' ',strip=True) if t.caption else ''})
assert len(out)==19
(OUT/'primary-reconciliation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
