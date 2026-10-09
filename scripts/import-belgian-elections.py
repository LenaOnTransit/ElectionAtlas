"""Build Belgium's sourced federal, regional/community and European chronology.
Requires beautifulsoup4; reads ignored .cache/belgium snapshots; never publishes.
"""
from pathlib import Path
import json,re,hashlib,datetime
from bs4 import BeautifulSoup
from us_presidential_html import Tables,expand
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/belgium';OUT=ROOT/'scripts/belgian-election-import';OUT.mkdir(exist_ok=True)
CHECKED='2026-10-09';records=[];audit=[]
def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def num(v):
 v=v.replace(',','').replace('%','').replace('\xa0','').strip()
 return float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
def integer(v):
 n=num(v);return int(n) if n is not None and n.is_integer() else None
def grid(table):
 p=Tables();p.feed(str(table));return expand(p.tables[0]['rows'])
def load(key):
 p=CACHE/(key+'.html');s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,script,style'):n.decompose()
 audit.append(dict(file=p.name,url='https://en.wikipedia.org/wiki/'+key,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return s
BODIES={'chamber':'Chamber of Representatives','senate':'Senate','congress':'National Congress','flemish':'Flemish Parliament','walloon':'Walloon Parliament','brussels':'Brussels-Capital Parliament','german':'Parliament of the German-speaking Community','european':'European Parliament — Belgian delegation'}
def base(scope,date,url):
 y=int(date[:4]);body=BODIES[scope]
 e=dict(id=f'world-belgium-{scope}-{date}',countryId='be',title=body,type='parliamentary',body=body,startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round='General',seriesId='be-'+scope,snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='Valid votes in the recorded election scope',results=[],sources=[dict(label='Historical results and cited source bibliography',url=url)],checked=CHECKED,notes='',articleId='',version=1,electionMethod='direct')
 if y<1894:e['notes']='Restricted tax-qualified male franchise; historical political groups and boundaries differ from present-day Belgium. '
 elif y<1919:e['weightedVotes']=True;e['notes']='Universal male plural voting: some electors could cast multiple votes; vote totals are not counts of individual voters. '
 elif y<1949:e['notes']='Women did not yet have equal national voting rights; the historical franchise differs from today. '
 if scope=='senate':e['notes']+='Results describe the source’s directly elected Senate seats or post-renewal composition; provincial, co-opted and ex-officio members are not silently added. '
 return e

def parse(e,t):
 g=grid(t);hi=next((i for i,r in enumerate(g) if any(c['text'] in ['Party','Party or alliance'] for c in r) and any(c['text'] in ['Seats','Votes'] for c in r)),None)
 if hi is None:return False
 h=[c['text'] for c in g[hi]]
 # The second header distinguishes seats won from the resulting chamber total.
 if hi+1<len(g) and any(c['text'] in ['Won','Flanders','Elected'] for c in g[hi+1]):hi+=1;h=[c['text'] for c in g[hi]]
 vi=next((i for i,x in enumerate(h) if x=='Votes'),None);pi=next((i for i,x in enumerate(h) if x=='%'),None)
 si=next((i for i,x in enumerate(h) if x=='Total'),None)
 if e['seriesId']=='be-senate' and e['startDate']>='1995' and 'Won' in h:si=h.index('Won')
 if si is None:si=next((i for i,x in enumerate(h) if x in ['Seats','Won']),None)
 ni=max(i for i,x in enumerate(h) if x in ['Party','Party or alliance']);totals=[];group='';votes_seen={};seats_seen=set();valid=None
 for row in g[hi+1:]:
  r=[c['text'] for c in row]
  if len(r)<=ni:continue
  if 'language group' in r[0].lower() or 'speaking electoral college' in r[0].lower():group=r[0];continue
  if 'Valid votes' in r and vi is not None:valid=integer(r[vi]) if len(r)>vi else None
  if 'Registered voters/turnout' in r and pi is not None and len(r)>pi:e['turnout']=num(r[pi])
  if r[ni]=='Total':
   if any(x not in ['','Total'] for x in r[:ni]):continue
   totals.append((integer(r[vi]) if vi is not None and len(r)>vi else None,integer(r[si]) if si is not None and len(r)>si else None));continue
  name=r[ni]
  if not name or name=='Party' or name.startswith(('Source:','Registered','Total','Invalid','Blank','Valid')):continue
  v=integer(r[vi]) if vi is not None and len(r)>vi else None;share=num(r[pi]) if pi is not None and len(r)>pi else None;seats=integer(r[si]) if si is not None and len(r)>si else None
  if si is not None and len(r)>si and r[si] in ['–','—','-']:seats=0
  if v is None and share is None and seats is None:continue
  if group:name+=' — '+group
  if si is not None and len(row)>si:
   key=id(row[si]);seats=None if key in seats_seen else seats;seats_seen.add(key)
  if vi is not None and len(row)>vi:
   key=id(row[vi])
   if key in votes_seen and v is not None:
    prev=votes_seen[key];prev['name']+=' / '+name;prev['party']=prev['name'];prev['seats']=(prev['seats'] or 0)+(seats or 0);continue
  m=re.search(r'background(?:-color)?\s*:\s*(#[a-fA-F0-9]{6})',row[0].get('style',''))
  result=dict(id=e['id']+'-'+str(len(e['results'])+1),name=name[:200],party=name[:200],color=m.group(1) if m else '#808080',votes=v,share=share,seats=seats,electoralVotes=None,winner=False,ideologyIds=[]);e['results'].append(result)
  if vi is not None and len(row)>vi:votes_seen[id(row[vi])]=result
 if not e['results']:return False
 for r in e['results']:
  if len(r['name'])>200:
   e['notes']+='Combined source vote group: '+r['name']+'. ';r['name']=r['party']='Other combined parties / lists'
 if any(' / ' in r['name'] for r in e['results']):e['notes']+='Votes shared across rows in the source are recorded once for the combined group. '
 seats=sum(r['seats'] or 0 for r in e['results']);votes=sum(r['votes'] or 0 for r in e['results']);sourceSeats=sum(n or 0 for _,n in totals) if totals and any(n is not None for _,n in totals) else None
 e['totalSeats']=sourceSeats if sourceSeats is not None and sourceSeats>=seats else None
 if len(totals)>1:
  denominator=sum(n or 0 for n,_ in totals)
  if denominator:
   for r in e['results']:r['share']=round(r['votes']/denominator*100,6) if r['votes'] is not None else None
   valid=denominator;e['notes']+='Separate language-group/college tables are combined. Displayed shares are calculated against all valid votes across the groups, not the separate group denominators. Group labels retain the seat allocation distinction. '
 if valid is None and totals:valid=sum(n or 0 for n,_ in totals) or None
 if si is not None and h[si]=='Won':e['notes']+='The seat figures are seats won in this partial renewal, not the entire chamber composition. '
 if valid:e['voteBasis']=f'Valid votes in recorded scope ({valid:,})'+('; plural-vote system' if e.get('weightedVotes') else '')
 if valid and votes!=valid:e['notes']+=f'Source rows total {votes:,} votes versus its {valid:,} denominator; the discrepancy is preserved and coverage is partial. '
 if e['totalSeats'] is not None and seats!=e['totalSeats']:e['notes']+='Seat rows do not reconcile to the source total; coverage is partial. '
 e['resultStatus']='final';e['resultCoverage']='complete' if valid and votes==valid and seats==e['totalSeats'] and abs(sum(r['share'] or 0 for r in e['results'])-100)<.2 else 'partial'
 return True

links=json.loads((OUT/'links.json').read_text());overview=BeautifulSoup((CACHE/'overview.html').read_text(),'html.parser');context={}
for tr in overview.select('table.wikitable tr'):
 st=txt(tr)
 for a in tr.select('a[href]'):
  k=a['href'].rsplit('/',1)[-1]
  if k in links:context[k]=st
for key,ds in links.items():
 date=datetime.datetime.strptime(ds,'%d %B %Y').date().isoformat();y=int(date[:4]);s=load(key);url='https://en.wikipedia.org/wiki/'+key;ctx=context.get(key,'')
 ts=[];headings={}
 for n in s.select('h2,h3,h4,table.wikitable'):
  if n.name!='table':
   level=int(n.name[1]);headings={k:v for k,v in headings.items() if k<level};headings[level]=txt(n);continue
  g=grid(n)
  if any(any(c['text'] in ['Party','Party or alliance'] for c in r) and any(c['text'] in ['Votes','Seats'] for c in r) for r in g):ts.append((' / '.join(headings.values()),n))
 if '_regional_elections' in key:
  scopes=['german'] if y in [1986,1990] else ['brussels'] if y==1989 else ['flemish','walloon','brussels','german']
 elif 'European_Parliament' in key:scopes=['european']
 elif y==1830:scopes=['congress']
 elif y in [1851,1855,1867]:scopes=['senate']
 else:
  scopes=['chamber']
  if y<1919:
   if y==1831 or ('both chambers' in ctx and not key.startswith('June_1870')) or re.search(r'Chamber [AE] and Senate',ctx):scopes+=['senate']
  elif y<=2010:scopes+=['senate']
  if y==1884:scopes+=['senate']
 for scope in scopes:
  d='1884-06-10' if y==1884 and scope=='chamber' else '1884-07-08' if y==1884 else date;e=base(scope,d,url)
  if y<1919 and scope in ['chamber','senate'] and 'partial:' in ctx and not (y==1884 and scope=='senate'):
   e['round']='Partial renewal';e['notes']+='Only the designated provincial rotation was contested. Seat totals labelled Total describe the resulting composition, not all seats won at this ballot. '
  if scope=='congress':e['notes']+='Constituent National Congress elected before the 1831 bicameral constitution. '
  target=None
  for headings,t in ts:
   matches={'chamber':'Chamber','senate':'Senate','flemish':'Flemish','walloon':'Walloon','brussels':'Brussels','german':'German','congress':'Results','european':'Results'}
   if matches[scope].lower() in headings.lower():target=t;break
  if target is None and scope=='chamber':
   target=next((t for headings,t in ts if 'Results' in headings and 'Senate' not in headings and any(any(c['text']=='Votes' for c in row) for row in grid(t))),None)
  if target is None and len(ts)==1 and scope in ['senate','german','brussels','congress','european']:target=ts[0][1]
  if target is not None:parse(e,target)
  if scope=='senate' and e['totalSeats'] in [94,87]:
   e['resultCoverage']='partial';e['notes']+='This source seat total has not been reconciled to the full elected Senate size; coverage remains partial. '
  if scope=='german':continue # Reconcile all community elections with its own parliamentary historical tables below.
  if not e['results']:e['notes']+='No reconciled quantitative results are entered; this contest is retained in the chronology. '
  if y>=2014 and scope in ['chamber','flemish','walloon','brussels','european']:e['sources'].append(dict(label='Federal Interior Ministry: official result archive',url='https://elections.fgov.be/informations-generales/resultats'))
  if y==2024:e['sources'].append(dict(label='Federal Interior Ministry: 9 June 2024 official result tables',url='https://elections.fgov.be/elections-du-9-juin-2024-tableaux-des-resultats'))
  records.append(e)
# German-speaking Community: parliamentary primary tables resolve blank/invalid vote columns
# that a secondary table incorrectly called an additional party in 1974/1977/1978/1981.
p=CACHE/'pdg-history.html';s=BeautifulSoup(p.read_text(),'html.parser');gt=s.select('table');voteRows=grid(gt[0]);seatRows=grid(gt[1]);names=['Christian Social Party','Ecolo','Party for Freedom and Progress','Socialist Party','Party of German-speaking Belgians / PJU-PDB','ProDG','Vivant','SEP','Parti libertarien','Huppertz+Co','Liste24.dg']
seatMap={}
for row in seatRows:
 r=[c['text'] for c in row]
 if r and re.match(r'\d{4}-\d{4}',r[0]):seatMap[int(r[0][:4])]=[integer(v) if integer(v) is not None else 0 for v in r[1:9]]
for row in voteRows:
 r=[c['text'] for c in row]
 if not r or not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}',r[0]):continue
 date=datetime.datetime.strptime(r[0],'%d.%m.%Y').date().isoformat();y=int(date[:4]);e=base('german',date,'https://pdg.be/desktopdefault.aspx/tabid-4107/');e['sources'][0]['label']='German-speaking Community Parliament: election results and seat composition since 1974';e['totalSeats']=25;e['notes']='Shares are the parliament’s published party percentages; blank/invalid ballots are excluded from party rows. Historical rounding discrepancies remain visible. '
 # Old primary rows omit empty trailing columns; use the first eight established party columns.
 for i,name in enumerate(names):
  v=r[i+1] if i+1<len(r)-1 else '-';share=num(v.replace(',','.'))
  if share is None:continue
  seats=seatMap[y][i] if i<8 else 0
  e['results'].append(dict(id=e['id']+'-'+str(i+1),name=name,party=name,color='#808080',votes=None,share=share,seats=seats,electoralVotes=None,winner=False,ideologyIds=[]))
 # Supply actual vote counts only where the secondary full result table reconciles to primary figures.
 candidates=[k for k in links if k.startswith(str(y)+'_') and ('regional' in k or 'general' in k)]
 for k in candidates:
  ss=BeautifulSoup((CACHE/(k+'.html')).read_text(),'html.parser')
  for t in ss.select('table.wikitable'):
   st=txt(t)
   if 'Party' not in st[:100] or 'Votes' not in st[:100]:continue
   prev=' '.join(txt(h) for h in t.find_all_previous(['h2','h3','h4'])[:3])
   if 'German' not in prev and y not in [1986,1990]:continue
   temp=base('german',date,'https://en.wikipedia.org/wiki/'+k)
   if not parse(temp,t):continue
   if all(x['votes'] is not None for x in temp['results']) and sum(x['seats'] or 0 for x in temp['results'])==25 and abs(sum(x['share'] or 0 for x in temp['results'])-100)<.2:
    e['results']=temp['results'];e['turnout']=temp['turnout'];e['voteBasis']=temp['voteBasis'];e['resultCoverage']=temp['resultCoverage'];e['sources']+=temp['sources'];break
 e['resultStatus']='final';records.append(e)
audit.append(dict(file=p.name,url='https://pdg.be/desktopdefault.aspx/tabid-4107/',sha256=hashlib.sha256(p.read_bytes()).hexdigest()));audit.append(dict(file='overview.html',url='https://en.wikipedia.org/wiki/List_of_elections_in_Belgium',sha256=hashlib.sha256((CACHE/'overview.html').read_bytes()).hexdigest()))
# Reciprocal same-day links connect institutional contests without hiding the separate histories.
for e in records:
 e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['startDate']==e['startDate']]
 e['summary']=e['body']+': '+(f'{e["totalSeats"]} seats in the recorded source scope.' if e['totalSeats'] is not None else 'Historical election / chamber renewal.')
records.sort(key=lambda e:(e['startDate'],e['id']));assert len(records)==len({e['id'] for e in records})
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,recordCount=len(records),sources=audit),indent=2)+'\n')
print('Built',len(records),'records');print('No results:',[(e['startDate'],e['body']) for e in records if not e['results']]);print('Scopes:',{scope:sum(e['seriesId']=='be-'+scope for e in records) for scope in BODIES})
