"""Extract cached Swiss official facts; keep voter equivalents and ballot denominators distinct."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'.cache/switzerland';OUT=ROOT/'scripts/swiss-election-import'
def txt(x):return re.sub(r'\s+',' ',x.get_text(' ',strip=True).replace('\u200b','')).strip()
dates={}
s=BeautifulSoup((C/'official-dates.html').read_text(),'html.parser')
for tr in s.select('table tr'):
 cells=[txt(x) for x in tr.select('th,td')]
 for i in range(0,len(cells)-1,2):
  year=re.match(r'\d{4}',cells[i]);date=re.match(r'(\d{1,2})\.(\d{1,2})\.?',cells[i+1])
  if year and date:dates[year[0]]=f'{year[0]}-{int(date[2]):02}-{int(date[1]):02}'
assert len(dates)==51
pres=[]
for line in (C/'presidents-history.txt').read_text().splitlines():
 m=re.search(r'\s+(\d+)\s+(\d+,\d+)\s+(\d{4}(?:/49)?)$',line)
 if not m:continue
 cols=re.split(r'\s{2,}',line[:m.start()].strip())
 if cols[0]=='Schneider-Ammann, Johann FDP':cols=['Schneider-Ammann, Johann','FDP',*cols[1:]]
 assert len(cols)>=4,cols
 name,party,canton=cols[:3]
 if name=='Hertenstein, Wilhelm':name='Hertenstein, Wilhelm Friedrich';party='Zentrum (Dem.)'
 name=name.split(', ',1)[1]+' '+name.split(', ',1)[0]
 pres.append({'term':m[3],'name':name,'party':party,'canton':canton,'votes':int(m[1]),'source':'https://www.parlament.ch/centers/documents/_layouts/15/DocIdRedir.aspx?ID=DOCID-1-10236','affiliationScope':'Initial Federal Council affiliation' if int(m[3][:4])<=1903 else 'Presidential election-era affiliation'})
assert len(pres)==172
s=BeautifulSoup((C/'official-presidents.html').read_text(),'html.parser')
for tr in s.select('table tr'):
 c=[txt(x) for x in tr.select('th,td')]
 if len(c)!=7 or not re.fullmatch(r'\d{4}',c[0]) or not c[1].startswith('Bundespräsident'):continue
 year=int(c[0]);entry=dict(term=c[0],name=c[2],party=c[3],canton=c[4],votes=int(c[6]),source='https://www.parlament.ch/de/%C3%BCber-das-parlament/archiv/wahlen-im-rueckblick/praesidentenwahlen',affiliationScope='Presidential election-era affiliation')
 prior=next((p for p in pres if p['term']==c[0]),None)
 if prior:assert prior['votes']==entry['votes'],entry;pres.remove(prior)
 pres.append(entry)
assert len(pres)==178
nr=json.loads((C/'px-nr-results.json').read_text());seats=json.loads((C/'px-nr-seats-results.json').read_text());facts=[]
for year,yi in nr['dimension']['Jahr']['category']['index'].items():
 rows=[];si=seats['dimension']['Jahr']['category']['index'][year];np=len(nr['dimension']['Partei']['category']['index']);sp=len(seats['dimension']['Partei']['category']['index'])
 for party,pi in nr['dimension']['Partei']['category']['index'].items():
  share=nr['value'][(yi*np+pi)*3+2];voter_equivalent=nr['value'][(yi*np+pi)*3+1];sj=seats['dimension']['Partei']['category']['index'][party];seat=seats['value'][si*sp+sj]
  if share is None and seat is None:continue
  rows.append({'code':party,'label':nr['dimension']['Partei']['category']['label'][party],'share':share,'roundedVoterEquivalents':voter_equivalent,'seats':seat or 0})
 total=seats['value'][si*sp+seats['dimension']['Partei']['category']['index']['0']]
 assert sum(r['seats'] for r in rows)==total==200,year
 facts.append({'year':int(year),'totalSeats':total,'rows':rows,'shareSource':'https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-1702020000_104/px-x-1702020000_104/px-x-1702020000_104.px','seatSource':'https://www.pxweb.bfs.admin.ch/pxweb/de/px-x-1702020000_103/px-x-1702020000_103/px-x-1702020000_103.px'})
import xlrd
xls=xlrd.open_workbook(str(C/'presidents-1920.xls')).sheet_by_name('Bundespräsidenten');checked=[]
for i in range(2,xls.nrows):
 r=xls.row_values(i);year=str(r[3]).removesuffix('.0');votes=str(r[2]).removesuffix('.0')
 if not year.isdigit() or not votes.isdigit():continue
 year=int(year);votes=int(votes);entry=next((p for p in pres if p['term']==str(year)),None)
 if entry:assert entry['votes']==votes,(year,entry['votes'],votes)
 checked.append({'term':year,'sourceName':r[0],'votes':votes})
(OUT/'primary-reconciliation.json').write_text(json.dumps({'nationalDates':dates,'presidents':pres,'nationalCouncil':facts,'presidentialXlsVerification':{'source':'https://www.parlament.ch/centers/documents/_layouts/15/DocIdRedir.aspx?ID=DOCID-1-6765','rows':checked}},ensure_ascii=False,indent=2)+'\n')
print('Primary facts:',len(dates),'National Council polling dates;',len(pres),'presidential selections;',len(facts),'modern National Council allocations.')
