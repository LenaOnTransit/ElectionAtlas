"""Build Luxembourg's national legislative/constituent and European archive.
Requires beautifulsoup4; reads audited ignored HTML snapshots; never publishes.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from us_presidential_html import Tables,expand
import re,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/luxembourg';OUT=ROOT/'scripts/luxembourg-election-import';OUT.mkdir(exist_ok=True)
MONTHS={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
CHECKED='2026-10-09';records=[];audit=[];reconciliation=[]
def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def num(v):
 v=v.replace(',','').replace('%','').replace('\xa0','').strip();return float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
def integer(v):
 x=num(v);return int(x) if x is not None and x.is_integer() else None
def grid(table):
 p=Tables();p.feed(str(table));return expand(p.tables[0]['rows'])
def read(key,url=None):
 p=CACHE/(key+'.html');s=BeautifulSoup(p.read_text(),'html.parser')
 for n in s.select('sup,script,style'):n.decompose()
 audit.append(dict(file=p.name,url=url or 'https://en.wikipedia.org/wiki/'+key,sha256=hashlib.sha256(p.read_bytes()).hexdigest()));return s

def dates(s,y,key):
 if key=='Constituent_Assembly_of_Luxembourg':return ['1848-04-19'],'day'
 lead=next((txt(p) for p in s.select('p') if re.search(r'(?:elections? (?:were|was)|election.* on)',txt(p),re.I) and str(y) in txt(p)),None)
 if lead is None:lead=txt(s.select_one('table.infobox')) if s.select_one('table.infobox') else ''
 lead=lead.split('. ')[0]
 ds=[]
 pattern=r'(\d{1,2})(?:\s*(?:and|–|-|to)\s*(\d{1,2}))?\s+('+'|'.join(MONTHS)+r')\s*(\d{4})?'
 inputs=[lead]
 box=s.select_one('table.infobox')
 if box:
  datecells=[txt(td) for td in box.select('td') if '→' in txt(td) and len(txt(td))<400]
  inputs+=datecells[:1]
 for candidate in inputs:
  for m in re.finditer(pattern,candidate):
   a,b,month,year=m.groups();year=int(year or y)
   if year!=y:continue
   ds.append(datetime.date(y,MONTHS[month],int(a)).isoformat())
   if b:ds.append(datetime.date(y,MONTHS[month],int(b)).isoformat())
  if ds:break
 if ds:return sorted(set(ds)),'day'
 for m,n in MONTHS.items():
  if re.search(r'\b'+m+r'\b',lead):return [f'{y}-{n:02}-01'],'month'
 return [f'{y}-01-01'],'year'

def base(key,s):
 y=1848 if key=='Constituent_Assembly_of_Luxembourg' else int(re.search(r'\d{4}',key).group());scope='european' if 'European_Parliament' in key else 'constituent' if 'Assembly' in key else 'chamber';ds,precision=dates(s,y,key)
 body='European Parliament — Luxembourg delegation' if scope=='european' else 'Constituent Assembly' if scope=='constituent' else 'Assembly of Estates' if y==1845 or 1857<=y<=1866 else 'Chamber of Deputies';lead=' '.join(txt(p) for p in s.select('p')[:5]);partial=bool(re.search(r'Partial general elections',lead,re.I))
 e=dict(id=f'world-luxembourg-{scope}-{ds[0]}',countryId='lu',title=body,type='parliamentary',body=body,startDate=ds[0],endDate=ds[-1] if len(ds)>1 else '',precision=precision,dateStatus='confirmed' if precision=='day' else 'expected',status='held',publication='published',round='Partial renewal' if partial else 'General',seriesId='lu-european' if scope=='european' else 'lu-legislature',snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='not-entered',resultCoverage='partial',voteBasis='Election-era candidate/list votes; multiple votes per elector',results=[],sources=[dict(label='Historical results and cited source bibliography',url='https://en.wikipedia.org/wiki/'+key)],checked=CHECKED,notes='',articleId='',version=1,electionMethod='indirect' if y in [1845,1857] or key=='Constituent_Assembly_of_Luxembourg' else 'direct')
 if precision!='day':e['notes']+='The date is established only to '+precision+' precision; no exact election day is inferred. '
 if y<1919:e['notes']+='Restricted tax-qualified male franchise; historical institutions, groups and constituency boundaries differ from today. '
 if partial:e['notes']+='Only part of the legislature was renewed. Entered seat totals cover the seats elected in this ballot, excluding continuing members. Vote totals cover only the contested constituencies. '
 if scope=='constituent':e['round']='Constituent election';e['notes']+='National constituent election for constitutional revision. '
 if scope=='european':e['notes']+='Luxembourg elected six MEPs in a nationwide constituency. Each elector could cast up to six candidate votes, including votes across lists. '
 else:e['notes']+='Candidate-vote totals are not ballot counts or counts of individual voters. National percentages use raw candidate/list votes, not the separate voter-weighted theoretical-elector measure. '
 if y==1918:e['notes']+='Popular votes and shares refer to the first round; seats are the final allocation following the second round. '
 e['sources'].append(dict(label='Chamber of Deputies: historical electoral system and franchise',url='https://www.chd.lu/en/elections'))
 return e

def result(e,name,votes=None,share=None,seats=None,color='#808080',candidate=False):
 e['results'].append(dict(id=e['id']+'-'+str(len(e['results'])+1),name=name[:200],party='' if candidate else name[:200],color=color,votes=votes,share=share,seats=seats,electoralVotes=None,winner=candidate,ideologyIds=[]))
def party_results(e,s):
 for t in s.select('table.wikitable'):
  g=grid(t);hi=next((i for i,row in enumerate(g) if 'Party' in [c['text'] for c in row] and 'Votes' in [c['text'] for c in row] and '%' in [c['text'] for c in row]),None)
  if hi is None:continue
  h=[c['text'] for c in g[hi]]
  if hi+1<len(g) and 'Elected' in [c['text'] for c in g[hi+1]]:hi+=1;h=[c['text'] for c in g[hi]]
  if len(h)>12 or 'Constituency' in h or 'Canton' in h:continue
  if not any(any(c['text']=='Total' for c in row) for row in g[hi+1:]):continue
  ni=max(i for i,v in enumerate(h) if v=='Party');vi=h.index('Votes');pi=h.index('%');si=h.index('Elected') if 'Elected' in h else h.index('Won') if 'Won' in h else h.index('Total seats') if 'Total seats' in h else h.index('Seats') if 'Seats' in h else None
  denominator=None;sourceSeats=None;validBallots=None;voteGroups={};seatSeen=set()
  for row in g[hi+1:]:
   r=[c['text'] for c in row]
   if len(r)<=ni:continue
   if r[ni]=='Total':
    denominator=integer(r[vi]);sourceSeats=integer(r[si]) if si is not None and len(r)>si else None;continue
   if r[ni]=='Valid votes':validBallots=integer(r[vi]) if len(r)>vi else None
   if r[ni]=='Registered voters/turnout' and len(r)>pi:e['turnout']=num(r[pi])
   name=r[ni]
   if not name or name=='Party' or name.startswith(('Valid','Invalid','Blank','Total','Registered','Source')):continue
   v=integer(r[vi]) if len(r)>vi else None;share=num(r[pi]) if len(r)>pi else None;seats=integer(r[si]) if si is not None and len(r)>si else None
   if si is not None and len(r)>si and r[si] in ['–','—','-']:seats=0
   if v is None and share is None and not seats:continue
   if si is not None and len(row)>si:
    cell=id(row[si]);seats=None if cell in seatSeen else seats;seatSeen.add(cell)
   cell=id(row[vi])
   if cell in voteGroups and v is not None:
    prev=voteGroups[cell];prev['name']+=' / '+name;prev['party']=prev['name'];prev['seats']=(prev['seats'] or 0)+(seats or 0);continue
   m=re.search(r'background(?:-color)?\s*:\s*(#[a-fA-F0-9]{6})',row[0].get('style',''));result(e,name,v,share,seats,m.group(1) if m else '#808080');voteGroups[cell]=e['results'][-1]
  if not e['results']:continue
  votes=sum(r['votes'] or 0 for r in e['results']);seats=sum(r['seats'] or 0 for r in e['results']);e['totalSeats']=sourceSeats if sourceSeats is not None and sourceSeats>=seats else None
  e['voteBasis']=f'Raw candidate/list votes ({denominator:,}); multiple votes per elector' if denominator else 'Election-era candidate/list votes; denominator unavailable'
  if validBallots:e['notes']+=f'Source reports {validBallots:,} valid ballots separately from candidate/list vote totals. '
  if denominator and votes!=denominator:e['notes']+=f'Source rows sum to {votes:,} votes versus its {denominator:,} total; coverage is partial. '
  if sourceSeats is not None and seats!=sourceSeats:e['notes']+='Entered seat rows do not reconcile to the source total; coverage is partial. '
  e['resultStatus']='final';e['resultCoverage']='complete' if denominator and votes==denominator and sourceSeats is not None and seats==sourceSeats and abs(sum(r['share'] or 0 for r in e['results'])-100)<.2 else 'partial'
  reconciliation.append(dict(id=e['id'],voteTotal=denominator,recordedVotes=votes,seatTotal=sourceSeats,recordedSeats=seats,validBallots=validBallots));return True
 return False

def historical_members(e,s):
 for t in s.select('table.wikitable'):
  g=grid(t);hi=next((i for i,r in enumerate(g) if 'Candidate' in [c['text'] for c in r] and 'Canton' in [c['text'] for c in r]),None)
  if hi is None:continue
  h=[c['text'] for c in g[hi]];ni=h.index('Candidate');ci=h.index('Canton');si=h.index('Seats') if 'Seats' in h else None
  bold={txt(b) for b in t.select('b,strong')};sourceSeats=0;seenSeats=set()
  for row in g[hi+1:]:
   r=[c['text'] for c in row]
   if si is not None and len(row)>si and integer(r[si]) is not None and id(row[si]) not in seenSeats:sourceSeats+=integer(r[si]);seenSeats.add(id(row[si]))
   if len(r)<=ni or not r[ni].strip() or r[ni] not in bold or r[ni] in ['Turnout','Candidate']:continue
   result(e,r[ni]+' — '+r[ci],seats=1,candidate=True)
  if e['results']:
   e['totalSeats']=sourceSeats if sourceSeats>=len(e['results']) else None;e['resultStatus']='final';e['resultCoverage']='partial';e['voteBasis']='Elected-member names; national vote totals unavailable';e['notes']+='Only candidates explicitly marked elected in the source are transcribed, with one elected seat each and no inferred party affiliation. Local multi-round candidate votes are not combined into a national percentage table. Named-member coverage may be incomplete. ';return True
 return False
read('overview','https://en.wikipedia.org/wiki/Elections_in_Luxembourg')
links=json.loads((OUT/'links.json').read_text())
for key,url in links.items():
 s=read(key,url);e=base(key,s)
 if not party_results(e,s):historical_members(e,s)
 if not e['results']:e['notes']+='No reconciled quantitative results are entered; this election is retained in the national chronology. '
 records.append(e)
# Reviewed corrections distinguish Luxembourg's polling day from the Europe-wide interval.
for correction in json.loads((OUT/'date-corrections.json').read_text()):
 e=next(x for x in records if x['sources'][0]['url'].endswith('/'+correction['key']));e.update(id='world-luxembourg-'+correction['scope']+'-'+correction['date'],startDate=correction['date'],endDate='',precision='day',dateStatus='confirmed');e['sources'].append(dict(label=correction['label'],url=correction['source']));e['notes']+=correction['note']
 for i,r in enumerate(e['results']):r['id']=e['id']+'-'+str(i+1)
 for a in reconciliation:
  if a['id'].startswith('world-luxembourg-'+correction['scope']+'-'+correction['date'][:4]):a['id']=e['id']
# Add reviewed primary national result sources, without assuming voter-weighted figures are raw votes.
for key,url in json.loads((OUT/'official-links.json').read_text()).items():
 p=CACHE/(key+'.html')
 if not p.exists():continue
 read(key,url)
 if key=='parliament-history':continue
 y=int(key.rsplit('-',1)[1]);scope='european' if 'european' in key else 'chamber';e=next(e for e in records if e['id'].startswith('world-luxembourg-'+scope+'-'+str(y)))
 e['sources'].append(dict(label='Luxembourg Government: national result tables',url=url))
 if y in [2023,2024]:e['resultStatus']='provisional';e['notes']+='The government web result page explicitly labels its tally unofficial (résultats officieux); this transcription preserves that status. '
# Certified canvasses supersede election-night HTML and secondary transcriptions.
certified=json.loads((OUT/'certified-extract.json').read_text())
for key in ['legislative2023','european2024']:
 c=certified[key];e=next(e for e in records if e['id']==c['id']);e['results']=[]
 for row in c['rows']:result(e,row['name'],row['votes'],row['share'],row['seats'],row['color'])
 e.update(resultStatus='final',resultCoverage='complete',totalSeats=sum(r['seats'] for r in c['rows']),turnout=round(c['ballots']/c['registeredVoters']*100,2),voteBasis=f'Certified raw candidate/list votes ({c["voteTotal"]:,}); multiple votes per elector')
 e['notes']=re.sub(r'Source reports [\d,]+ valid ballots separately from candidate/list vote totals\. ','',e['notes']).replace('The government web result page explicitly labels its tally unofficial (résultats officieux); this transcription preserves that status. ','')
 e['notes']+=f'Final signed recensement reports supersede the unofficial election-night figures. They record {c["ballots"]:,} ballots cast and {c["validBallots"]:,} valid ballots separately from {c["voteTotal"]:,} candidate/list votes. '
 if key=='legislative2023':e['notes']+='National raw votes and seats are summed across Sud, Centre, Nord and Est; shares are calculated against their combined certified raw-vote total. Turnout uses the certified ballot sum and the national electoral-roll total. '
 primary=[]
 for report in c['reports']:
  p=CACHE/report['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==report['sha256'],'Certified source changed; review before regenerating'
  audit.append(dict(file=p.name,url=report['url'],sha256=report['sha256']))
  primary.append(dict(label='Certified final recensement: '+report.get('region','European nationwide')+'; vote pages '+', '.join(map(str,report['votePages']))+'; seat pages '+', '.join(map(str,report['seatPages'])),url=report['url']))
 e['sources']=primary+e['sources']
 a=next(a for a in reconciliation if a['id']==e['id']);a.update(voteTotal=c['voteTotal'],recordedVotes=sum(r['votes'] for r in e['results']),seatTotal=e['totalSeats'],recordedSeats=sum(r['seats'] for r in e['results']),validBallots=c['validBallots'],ballots=c['ballots'],basis='certified recensement')
for e in records:
 e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['precision']=='day' and e['precision']=='day' and x['startDate']==e['startDate']]
 e['summary']=e['body']+': '+(f'{e["totalSeats"]} seats in the recorded election scope.' if e['totalSeats'] is not None else 'Historical national election; see coverage notes.')
records.sort(key=lambda e:(e['startDate'],e['id']));assert len({e['id'] for e in records})==len(records)
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'source-audit.json').write_text(json.dumps(dict(checked=CHECKED,recordCount=len(records),sources=audit),indent=2)+'\n');(OUT/'reconciliation.json').write_text(json.dumps(reconciliation,indent=2)+'\n')
print('Built',len(records),'records;',sum(e['seriesId']=='lu-european' for e in records),'European,',sum(e['seriesId']=='lu-legislature' for e in records),'legislative/constituent.');print('Chronology only:',[(e['startDate'],e['body']) for e in records if not e['results']])
