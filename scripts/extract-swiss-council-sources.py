"""Preserve separate Federal Council seat ballots; no national denominator is inferred."""
from pathlib import Path
from bs4 import BeautifulSoup
import sys,json,re,unicodedata
sys.path.insert(0,str(Path(__file__).resolve().parent))
from us_presidential_html import Tables,expand
ROOT=Path(__file__).resolve().parents[1];C=ROOT/'.cache/switzerland';OUT=ROOT/'scripts/swiss-election-import'
MONTHS={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
def rows(t):
 for x in t.select('sup'):x.decompose()
 for x in t.select('[rowspan],[colspan]'):
  for attr in ('rowspan','colspan'):
   if x.has_attr(attr):x[attr]=re.match(r'\d+',str(x[attr]))[0]
 parser=Tables();parser.feed(str(t));return [[re.sub(r'\s+',' ',c['text'].replace('\u200b','')).strip() for c in r] for r in expand(parser.tables[0]['rows'])]
def number(s):return int(s.replace(',','')) if re.fullmatch(r'\d[\d,]*',s) else None
def normal(s):return re.sub(r'[^a-z]','',unicodedata.normalize('NFKD',s.replace('Ueli Maruer','Ueli Maurer')).encode('ascii','ignore').decode().lower())
out=[]
for p in sorted(C.glob('*_Swiss_Federal_Council_election.html')):
 year=int(p.name[:4]);s=BeautifulSoup(p.read_text(),'html.parser');text=s.get_text(' ',strip=True);m=re.search(r'(\d{1,2}) ('+'|'.join(MONTHS)+') '+str(year),text);assert m,year;date=f'{year}-{MONTHS[m[2]]:02}-{int(m[1]):02}'
 contests=[]
 for t in s.select('table.wikitable'):
  h=t.find_previous(['h2','h3']);heading=h.get_text(' ',strip=True) if h else ''
  if year!=2025 and not heading.startswith(('Seat held','Vacant seat','Open seat')):continue
  rr=rows(t);header=rr[0];roundcols=[i for i,c in enumerate(header) if c.startswith('Round ')]
  if not roundcols:continue
  partycol=header.index('Party') if 'Party' in header else None
  ci=max(i for i,x in enumerate(header) if x=='Candidate') if 'Candidate' in header else 0
  validrow=next(r for r in rr if r[0]=='Valid votes');candidates=[]
  for r in rr[1:]:
   if not r:continue
   if r[0] in ('Valid votes','Absolute majority','Votes cast','Invalid votes','Blank votes','Ballot papers distributed','Ballot papers returned','Invalid votes (of which spoiled)'):continue
   vs=[number(r[i]) if i<len(r) else None for i in roundcols]
   if all(v is None for v in vs):continue
   party=r[partycol] if partycol is not None and len(r)>partycol else None
   name=r[ci]
   if name in ('Others','Votes received by other persons'):party='Unattributed ballots'
   assert name,(year,r)
   candidates.append({'name':name,'party':party,'votes':vs})
  valid=[number(validrow[i]) for i in roundcols]
  for j,v in enumerate(valid):assert sum(c['votes'][j] or 0 for c in candidates)==v,(year,heading,j)
  contests.append({'label':heading,'validVotes':valid,'candidates':candidates})
 assert len(contests)==(1 if year==2025 else 7),(year,len(contests))
 out.append({'year':year,'date':date,'source':'https://en.wikipedia.org/wiki/'+p.stem,'contests':contests})
(OUT/'council-ballots.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Council source tables:',len(out),'events;',sum(len(e['contests']) for e in out),'seat contests.')
verified=[]
for e in out:
 if e['year']==2007:continue
 paths=list(C.glob(f'council-{e["year"]}-*.html'))
 if e['year']==2019:paths=[C/'council-2019-fr.html'] # German page contains later-member labels.
 facts=[]
 for path in paths:
  s=BeautifulSoup(path.read_text(),'html.parser')
  for t in s.select('table'):
   for r in rows(t):
    if len(r)<2:continue
    if 'Stimmen' in r[-1] and ',' in r[0]:
     m=re.search(r'(\d+)\s*Stimmen',r[-1])
     if m:
      name=r[0].split(', ',1);name=' '.join(reversed(name));facts.append({'name':name,'votes':[int(m[1])]})
    else:
     nums=[number(x) for x in r[1:] if number(x) is not None]
     if nums and any(normal(c['name'])==normal(r[0]) for co in e['contests'] for c in co['candidates']):facts.append({'name':r[0].replace('Ueli Maruer','Ueli Maurer'),'votes':nums})
 verified.append({'year':e['year'],'sourceFiles':[p.name for p in paths],'candidates':facts})
(OUT/'council-primary-reconciliation.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2)+'\n')
