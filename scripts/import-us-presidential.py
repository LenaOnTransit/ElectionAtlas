from pathlib import Path
from us_presidential_html import read,expand
import re,json,unicodedata,datetime,collections,argparse,subprocess,concurrent.futures,hashlib
REPO=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Rebuild all 60 public presidential election records and electoral maps from NARA, UCSB and FEC sources. Does not write to the database.')
parser.add_argument('--source-directory',type=Path,default=REPO/'.cache/us-presidential')
ROOT=parser.parse_args().source_directory
ROOT.mkdir(parents=True,exist_ok=True)
YEARS=[1789]+list(range(1792,2025,4))
def fetch(pair):
 kind,y=pair;p=ROOT/f'{kind}-{y}.html'
 if p.exists() and p.stat().st_size>15000:return
 url=f'https://www.archives.gov/electoral-college/{y}'if kind=='nara'else f'https://www.presidency.ucsb.edu/statistics/elections/{y}'
 subprocess.run(['curl','-L','-s','--fail','--retry','1','--max-time','40',url,'-o',str(p)],check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:list(pool.map(fetch,[(k,y)for y in YEARS for k in ['nara','ucsb']]))
fecdata={}
for y in [2016,2020,2024]:
 p=ROOT/f'fec-{y}.pdf';t=ROOT/f'fec-{y}.txt'
 if not p.exists():
  name='federalelections2016.pdf'if y==2016 else f'{y}presgeresults.pdf'
  subprocess.run(['curl','-L','-s','--fail','--max-time','40',f'https://www.fec.gov/resources/cms-content/documents/{name}','-o',str(p)],check=True)
 if not t.exists():subprocess.run(['pdftotext','-layout',*(['-f','4','-l','15']if y==2016 else []),str(p),str(t)],check=True)
 text=t.read_text();d={}
 if y==2016:
  start=text.index('2016 PRESIDENTIAL POPULAR VOTE SUMMARY');text=text[start:text.index('U.S. Census Bureau Voting Age Population',start)]
  for line in text.splitlines():
   m=re.match(r'^(.*?)\s{2,}([\d,]+)\s+(?:[\d.]+%)?\s*$',line)
   if m:d[m[1].strip()]=int(m[2].replace(',',''))
  assert sum(d.values())==136669276
 else:
  cols=None
  for line in text.splitlines():
   if re.match(r'^STATE\s{2,}',line)and 'ELECTORAL'not in line:cols=re.split(r'\s{2,}',line.strip())[1:]
   if cols and line.strip().startswith('Total:'):
    nums=re.findall(r'\d[\d,]*',line[len('Total:'):]);assert len(nums)==len(cols),(y,cols,nums)
    d.update({c:int(n.replace(',',''))for c,n in zip(cols,nums)})
  assert sum(v for k,v in d.items()if k!='TOTAL VOTES')==d['TOTAL VOTES']
 fecdata[str(y)]=d
(ROOT/'fec-popular.json').write_text(json.dumps(fecdata,indent=2))
STATES=json.loads((REPO/'lib/us-states-map.json').read_text());CODES={s['name']:s['code']for s in STATES};CODES['District of Columbia']='DC'
def plain(s):return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
def key(s):return re.sub(r'[^a-z0-9]','',plain(s).lower())
def clean(s):return re.sub(r',?\s+of\s+(?:'+ '|'.join(map(re.escape,CODES)) +')$','',s).replace(', Esq','').replace('*','').strip()
ALIASES={
'Barry M. Goldwater':'Barry Goldwater','John F. Kerry':'John Kerry','Charles Pinckney':'Charles C. Pinckney','De Witt Clinton':'DeWitt Clinton','William H. Harrison':'William Henry Harrison','John Breckenridge':'John C. Breckinridge','John C. Fremont':'John C. Frémont','James G. Blane':'James G. Blaine','Stephen Douglas':'Stephen A. Douglas','George McClellan':'George B. McClellan','Samuel Tilden':'Samuel J. Tilden','William J. Bryan':'William Jennings Bryan','William H. Taft':'William Howard Taft','Robert LaFollette':'Robert M. La Follette','Herbert C. Hoover':'Herbert Hoover','Harry S Truman':'Harry S. Truman','J. Strom Thurmond':'Strom Thurmond','Richard Nixon':'Richard M. Nixon','Hubert Humphrey':'Hubert H. Humphrey','George Wallace':'George C. Wallace','John Anderson':'John B. Anderson','Walter Mondale':'Walter F. Mondale','Michael Dukakis':'Michael S. Dukakis','Albert Gore, Jr.':'Al Gore','Albert Gore, Jr':'Al Gore','Joseph R. Biden Jr.':'Joe Biden','Joseph R. Biden':'Joe Biden','Kamala D. Harris':'Kamala Harris','Donald J. Trump':'Donald Trump',
}
ALIASES={key(a):b for a,b in ALIASES.items()}
def canon(s):s=clean(s);return ALIASES.get(key(s),s)
def ident(s):return re.sub(r'[^a-z0-9]+','-',plain(s).lower()).strip('-')
def num(s):
 s=s.strip()
 if re.fullmatch(r'\(\d+\)',s):s=s[1:-1]
 s=re.sub(r'\s*\(\d+\)','',s).replace(',','').replace('*','').strip()
 if s in ('','-','–','—','--'):return 0
 if not re.fullmatch(r'\d+',s):raise ValueError(f'Invalid numeric cell {s!r}')
 return int(s)
def summary(y):
 ts=read(ROOT/f'ucsb-{y}.html');t=next(t for t in ts if t and any(c['text']=='Party'for c in t[0]));out=[]
 for row in t[1:]:
  if any(c['text']=='STATE' for c in row):break
  if not row or any(c['text']=='Presidential'for c in row):continue
  cells=[]
  for c in row:cells.extend([c]*int(c.get('colspan',1)))
  # Numeric election-result columns follow the nominee(s), independently of malformed headers.
  i=next((i for i,c in enumerate(cells)if re.fullmatch(r'[\d,]+',c['text']) and i+1<len(cells)and ('%'in cells[i+1]['text'] or cells[i+1]['text'] in ('--','—','-'))),None)
  if i is None or i<2:continue
  before=[c['text']for c in cells[:i]if c['text'] and c['text']!='>']
  party=before[0];name=before[1];name=canon(name)
  out.append({'name':name,'party':party,'electoral':num(cells[i]['text']),'votes':num(cells[i+2]['text'])if y>=1824 and i+3<len(cells)else None,'winner':any(c['winner']for c in cells[:i])})
 return out
# Disaggregations recorded in the National Archives table footnotes.
OTHER={
1796:{'CT':{'John Jay':5},'GA':{'George Clinton':4},'MD':{'John Henry':2},'MA':{'Samuel Johnston':2},'NC':{'James Iredell':3,'George Washington':1,'Charles C. Pinckney':1},'VA':{'George Clinton':3,'George Washington':1}},
1824:{'DE':{'William H. Crawford':2},'GA':{'William H. Crawford':9},'KY':{'Henry Clay':14},'MD':{'William H. Crawford':1},'MO':{'Henry Clay':3},'NY':{'William H. Crawford':5,'Henry Clay':4},'OH':{'Henry Clay':16},'VA':{'William H. Crawford':24}},
1832:{'SC':{'John Floyd':11},'VT':{'William Wirt':7}},
1836:{'GA':{'Hugh Lawson White':11},'MA':{'Daniel Webster':14},'SC':{'Willie Person Mangum':11},'TN':{'Hugh Lawson White':15}},
1860:{**{c:{'John C. Breckinridge':v}for c,v in {'AL':9,'AR':4,'DE':3,'FL':3,'GA':10,'LA':6,'MD':8,'MS':7,'NC':10,'SC':8,'TX':4}.items()},**{c:{'John Bell':v}for c,v in {'KY':12,'TN':12,'VA':15}.items()}},
1872:{'GA':{'Benjamin Gratz Brown':6,'Charles J. Jenkins':2},'KY':{'Benjamin Gratz Brown':4,'Thomas A. Hendricks':8},'MD':{'Thomas A. Hendricks':8},'MO':{'Benjamin Gratz Brown':8,'Thomas A. Hendricks':6,'David Davis':1},'TN':{'Thomas A. Hendricks':12},'TX':{'Thomas A. Hendricks':8}},
2016:{'HI':{'Bernie Sanders':1},'TX':{'Ron Paul':1,'John Kasich':1},'WA':{'Colin Powell':3,'Faith Spotted Eagle':1}},
}
PARTIES={'Federalist':'#a36d2b','Democratic-Republican':'#2d806b','Democratic':'#174a9c','Republican':'#aa202a','Whig':'#c99424','National Republican':'#c99424','Anti-Masonic':'#8054a0','Free Soil':'#8f6b36','American':'#8f6b36','Constitutional Union':'#bd8522','Progressive':'#27846a','Populist':'#965895','Socialist':'#bb4154','Independent':'#8054a0','Libertarian':'#b79423','Green':'#3d8b46','Various':'#777777'}
MINOR_PARTY={'Thomas Pinckney':'Federalist','Charles C. Pinckney':'Federalist','John Jay':'Federalist','Oliver Ellsworth':'Federalist','Samuel Huntington':'Federalist','James Iredell':'Federalist','Samuel Johnston':'Federalist','John Henry':'Federalist','George Clinton':'Democratic-Republican','Aaron Burr':'Democratic-Republican','Thomas Jefferson':'Democratic-Republican','Samuel Adams':'Democratic-Republican','John Quincy Adams':'Democratic-Republican','John Adams':'Federalist','George Washington':'Independent','John Floyd':'Nullifier','William Wirt':'Anti-Masonic','Hugh Lawson White':'Whig','Daniel Webster':'Whig','Willie Person Mangum':'Whig','John C. Breckinridge':'Southern Democratic','John Bell':'Constitutional Union','Benjamin Gratz Brown':'Liberal Republican / Democratic','Thomas A. Hendricks':'Democratic','Charles J. Jenkins':'Democratic','David Davis':'Independent','Walter B. Jones':'Democratic','Harry F. Byrd':'Independent Democratic','John Hospers':'Libertarian','Ronald Reagan':'Republican','Lloyd Bentsen':'Democratic','John Edwards':'Democratic','Bernie Sanders':'Independent','Ron Paul':'Libertarian','John Kasich':'Republican','Colin Powell':'Republican','Faith Spotted Eagle':'Independent'}
def partyclean(s):
 s=s.replace('unofficially Federalist','Independent').replace('Democrat-Republican','Democratic-Republican')
 return {'Democrat':'Democratic','Republicans':'Republican','Whigs':'Whig'}.get(s,s)

def electoral(y):
 t=read(ROOT/f'nara-{y}.html')[1];states=[]
 if y==1789:
  names=[canon(r[0]['text'])for r in t[1:-1]]
  for i,c in enumerate(t[0][1:-1],1):
   v={ident(names[j]):num(t[j+1][i]['text'])for j in range(len(names)) if num(t[j+1][i]['text'])}
   states.append({'code':c['text'],'name':next(s['name']for s in STATES if s['code']==c['text']),'electors':num(t[-1][i]['text']),'votes':v,'unallocated':0})
  return states,dict(zip(map(ident,names),names)),69,35,[]
 n=int(t[0][2].get('colspan',1));headers=[canon(c['text'])for c in t[1][:n]];labels={ident(h):h for h in headers if not h.lower().startswith(('other','othes'))};totals=None
 for row in t[2:]:
  if not row:continue
  if row[0]['text'].lower().startswith('total'):totals=row;continue
  stateName=row[0]['text'].replace('*','').strip()
  if stateName not in CODES:continue
  code=CODES[stateName];ev=num(row[1]['text']);v={};others=0
  for i,h in enumerate(headers,2):
   count=num(row[i]['text'])
   if h.lower().startswith(('other','othes')):others+=count
   elif count:v[ident(h)]=v.get(ident(h),0)+count
  if others:
   split=OTHER.get(y,{}).get(code)
   assert split is not None,(y,code,others,'UNRESOLVED OTHER')
   assert sum(split.values())==others,(y,code,others,split)
   for name,count in split.items():labels[ident(name)]=name;v[ident(name)]=v.get(ident(name),0)+count
  if y==1800 and code=='VA':v['aaron-burr']=21
  # Greeley's three rejected Georgia votes are not counted presidential votes.
  if y==1872 and code=='GA':v.pop('horace-greeley',None)
  unallocated=(2 if y<1804 else 1)*ev-sum(v.values())
  assert unallocated>=0,(y,code,ev,v)
  states.append({'code':code,'name':stateName,'electors':ev,'votes':v,'unallocated':unallocated})
 assert totals is not None,y
 total=num(totals[1]['text']);assert sum(s['electors']for s in states)==total,(y,total,sum(s['electors']for s in states))
 # Verify every raw candidate column independently, before footnote disaggregation.
 for i,h in enumerate(headers,2):
  expected=num(totals[i]['text'])
  if h.lower().startswith(('other','othes')):actual=sum(num(row[i]['text'])for row in t[2:]if row and row[0]['text'].replace('*','').strip()in CODES)
  else:actual=sum(s['votes'].get(ident(h),0)for s in states)
  if y==1872 and h=='Horace Greeley':expected=0
  assert actual==expected,(y,h,actual,expected)
 return states,labels,total,total//2+1,headers

SPECIAL={1789:'The first presidential election selected electors during 1788–89. George Washington received a vote from every elector who voted. New York did not appoint electors; North Carolina and Rhode Island had not yet ratified the Constitution.',1792:'George Washington again received a vote from every elector who voted.',1800:'Thomas Jefferson and Aaron Burr tied at 73 electoral votes. The House of Representatives elected Jefferson on its 36th ballot in February 1801.',1824:'No candidate won an electoral majority. Andrew Jackson led the electoral tally, but the House elected John Quincy Adams in February 1825.',1832:'Two Maryland electors did not vote. The recorded Electoral College tally includes 286 voting electors.',1836:'The Senate decided the vice-presidential election; Martin Van Buren won the presidential electoral vote outright.',1864:'Eleven seceded states had no electoral votes counted. Nevada cast two electoral votes although it was entitled to three.',1868:'Mississippi, Texas and Virginia had not been readmitted and cast no counted electoral votes.',1872:'Horace Greeley died after the popular election. His electors voted for several other recipients; three votes cast for Greeley were rejected. Arkansas and Louisiana had no electoral votes counted.',1876:'The disputed returns were resolved through an Electoral Commission and congressional count. Rutherford B. Hayes received 185 electoral votes to Samuel J. Tilden’s 184.',1888:'Benjamin Harrison won the electoral vote while Grover Cleveland received more popular votes.',1960:'Unpledged and faithless electors voted for Harry F. Byrd. Historical Alabama popular-vote totals use votes for individual electors and require care when comparing national candidate totals.',2000:'George W. Bush won the electoral vote despite Al Gore’s popular-vote lead. One District of Columbia elector abstained.',2004:'One Minnesota elector cast a presidential vote for John Edwards.',2008:'Nebraska split its electoral votes: four for John McCain and one for Barack Obama.',2016:'The counted electoral tally was Donald Trump 304, Hillary Clinton 227, and seven votes for other recipients. It differs from the pledged 306–232 allocation. Maine split its votes and Hawaii, Texas and Washington recorded faithless votes.',2020:'Nebraska and Maine split their electoral votes between candidates.',2024:'Maine split 3–1 for Kamala Harris; Nebraska split 4–1 for Donald Trump.'}
allmaps={};records=[];audit=[]
for y in YEARS:
 us=summary(y);st,labels,total,majority,headers=electoral(y)
 national=collections.Counter()
 for state in st:national.update(state['votes'])
 results={}
 for u in us:
  name=u['name'];id=ident(name);party=partyclean(u['party'])
  results[id]={'id':id,'name':name,'party':party,'color':PARTIES.get(party,'#8054a0'),'votes':u['votes']if y>=1824 else None,'share':None,'seats':None,'electoralVotes':national.get(id,0),'winner':u['winner']}
 for id,count in national.items():
  if id not in results:
   name=labels[id];party=MINOR_PARTY.get(name,'Independent')
   results[id]={'id':id,'name':name,'party':party,'color':PARTIES.get(party,'#8054a0'),'votes':None,'share':None,'seats':None,'electoralVotes':count,'winner':False}
 # APP's winner marker is authoritative for the 1824 contingent outcome.
 assert sum(r['winner']for r in results.values())==1,(y,us)
 declared=canon(read(ROOT/f'nara-{y}.html')[0][0][1]['text'].split('[')[0].strip())
 if y!=1824:assert ident(declared)==next(id for id,r in results.items()if r['winner']),(y,declared,us)
 # APP's national total comes from its state table, not rounded candidate shares.
 totals=[]
 for table in read(ROOT/f'ucsb-{y}.html'):
  for row in table:
   if row and row[0]['text'].lower().startswith('total')and len(row)>1:
    try:totals.append(num(row[1]['text']))
    except ValueError:pass
 poptotal=max(totals,default=0) if y>=1824 else 0
 assert y<1824 or poptotal>0,(y,'NO POP TOTAL')
 if y in (2016,2020,2024):
  fec=json.loads((ROOT/'fec-popular.json').read_text())[str(y)]
  results={id:r for id,r in results.items()if r['party']!='Various'}
  for r in results.values():r['votes']=None
  if y==2016:
   poptotal=136669276
   named=[(canon(label.rsplit(' (',1)[0]),partyclean(label.rsplit(' (',1)[1].split(',')[0].rstrip(')')) if ' ('in label else 'Various',votes)for label,votes in fec.items()]
  else:
   poptotal=fec['TOTAL VOTES']
   selected={2020:{'BIDEN':('Joe Biden','Democratic'),'TRUMP':('Donald Trump','Republican'),'JORGENSEN':('Jo Jorgensen','Libertarian'),'HAWKINS':('Howie Hawkins','Green'),'DE LA':('Rocky De La Fuente','Independent'),'LA RIVA':('Gloria La Riva','Party for Socialism and Liberation'),'WEST':('Kanye West','Independent'),'BLANKENSHIP':('Don Blankenship','Constitution'),'PIERCE':('Brock Pierce','Independent'),'CARROLL':('Brian Carroll','American Solidarity')},2024:{'TRUMP':('Donald Trump','Republican'),'HARRIS':('Kamala Harris','Democratic'),'STEIN':('Jill Stein','Green'),'KENNEDY':('Robert F. Kennedy Jr.','Independent'),'OLIVER':('Chase Oliver','Libertarian'),'DE LA':('Claudia De la Cruz','Party for Socialism and Liberation'),'WEST':('Cornel West','Independent'),'TERRY':('Randall Terry','Constitution'),'SONSKI':('Peter Sonski','American Solidarity'),'AYYADURAI':('Shiva Ayyadurai','Independent')}}[y]
   named=[(name,party,fec[col])for col,(name,party)in selected.items()]
  for name,party,votes in named:
   id=ident(name)
   if id in results:results[id]['votes']=votes
   else:results[id]={'id':id,'name':name,'party':party,'color':PARTIES.get(party,'#8054a0'),'votes':votes,'share':None,'seats':None,'electoralVotes':0,'winner':False}
 if y>=1824:
  known=sum(r['votes']or 0 for r in results.values());assert known<=poptotal,(y,known,poptotal)
  if known<poptotal:
   id='other-popular-votes';results[id]={'id':id,'name':'Other candidates / recorded votes','party':'Various','color':'#777777','votes':poptotal-known,'share':None,'seats':None,'electoralVotes':0,'winner':False}
  for r in results.values():
   if r['votes']is not None:r['share']=100*r['votes']/poptotal
 winner=next(r for r in results.values()if r['winner'])
 # Washington's personal nonpartisanship is retained even when the source calls him unofficially Federalist.
 if y==1789:
  for r in results.values():r['party']='Independent';r['color']='#8054a0'
 if 'george-washington'in results:results['george-washington']['party']='Independent';results['george-washington']['color']='#8054a0'
 # Different factions within the same historical party remain visually distinguishable.
 if y==1824:
  for id,color in {'andrew-jackson':'#174a9c','john-quincy-adams':'#c99424','william-h-crawford':'#a15b70','henry-clay':'#3c8875'}.items():results[id]['color']=color
 notes=['Electoral votes are the presidential votes actually recorded in the National Archives count, including split and faithless votes. The map uses modern state outlines as a geographic reference; these are not historical boundaries.','Minor popular-vote candidates not separately tabulated by the source are grouped as other recorded votes. Historical popular-vote figures and definitions can vary between compilations.']
 if y<1804:notes.append('Before the Twelfth Amendment, each elector cast two undifferentiated votes. The table includes both votes, so candidate totals add to twice the number of electors. These are not modern separate presidential and vice-presidential ballots.')
 if y<1824:notes.append('A comparable nationwide popular-vote total is not provided. Electors were chosen under varying state rules, including appointment by legislatures; missing popular figures are not zero votes.')
 if y==1824:notes.append('The popular-vote total covers recorded voting states, not a universal national presidential ballot; several states appointed electors through their legislatures.')
 if y<1848:notes.append('States selected electors on different schedules; the archive records the election year rather than inventing a single national election day.')
 if y in SPECIAL:notes.append(SPECIAL[y])
 date=f'{y}-01-01';precision='year';dateStatus='expected'
 if y>=1848:
  first=datetime.date(y,11,1);day=first+datetime.timedelta(days=(0-first.weekday())%7+1);date=day.isoformat();precision='day';dateStatus='confirmed'
 election={'id':f'world-us-president-{y}','countryId':'us','title':'President'+(' · 1788–89'if y==1789 else ''),'body':'President','type':'presidential','startDate':date,'endDate':'','precision':precision,'dateStatus':dateStatus,'status':'held','publication':'published','round':'General','seriesId':'us-presidential','snap':False,'summary':f'{winner["name"]} was elected president.'+(' '+SPECIAL[y]if y in SPECIAL else ''),'government':'','turnout':None,'totalSeats':None,'resultStatus':'final','resultCoverage':'complete','voteBasis':'Counted Electoral College votes'+('; recorded popular votes'if y>=1824 else '; nationwide popular vote unavailable'),'results':sorted(results.values(),key=lambda r:(not r['winner'],-(r['votes']or 0),-(r['electoralVotes']or 0),r['name'])),'sources':[{'label':f'National Archives: {y} electoral count and state allocations','url':f'https://www.archives.gov/electoral-college/{y}'},{'label':f'American Presidency Project, UCSB: {y} election tables','url':f'https://www.presidency.ucsb.edu/statistics/elections/{y}'}],'checked':'2026-10-05','notes':'\n\n'.join(notes),'articleId':'','version':0}
 if y in (2016,2020,2024):
  election['sources'].append({'label':f'FEC: official {y} popular-vote results compiled from state election offices','url':f'https://www.fec.gov/resources/cms-content/documents/'+('federalelections2016.pdf'if y==2016 else f'{y}presgeresults.pdf')})
  election['notes']+='\n\nPopular-vote counts use the FEC compilation; electoral votes use the actual National Archives count. Source totals may differ from other historical series or earlier published updates.'
 if y==1800:
  election['sources'].append({'label':'National Archives: original 1800 electoral tally (NAID 2668821)','url':'https://www.archives.gov/legislative/features/1800-election/1800-election.html'})
  election['notes']+='\n\nThe original 1800 tally records Virginia’s 21 votes for Aaron Burr, which are omitted from the Archives web table’s Virginia row. Our map follows the original tally.'
 records.append(election)
 allmaps[election['id']]={'year':y,'electors':total,'majority':majority,'ballotsPerElector':2 if y<1804 else 1,'states':st,'candidates':[{k:r[k]for k in ['id','name','party','color']}for r in results.values()if r['electoralVotes']],'note':SPECIAL.get(y,''),'source':f'https://www.archives.gov/electoral-college/{y}'}
 audit.append({'year':y,'winner':winner['name'],'electors':total,'candidateVotes':sum(national.values()),'unallocated':sum(s['unallocated']for s in st),'popularTotal':poptotal,'candidates':len(results)})
(REPO/'scripts/us-presidential-election-records.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')))
mapfile=REPO/'public/us-presidential-electoral.json'
mapfile.write_text(json.dumps(allmaps,ensure_ascii=False,separators=(',',':')))
manifest={'checked':'2026-10-05','elections':60,'first':'1788–89','last':2024,'audit':audit,'sources':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(ROOT.glob('*.html'))if p.name.startswith(('nara-','ucsb-'))]+[{'file':f'fec-{y}.pdf','sha256':hashlib.sha256((ROOT/f'fec-{y}.pdf').read_bytes()).hexdigest()}for y in [2016,2020,2024]],'mapSha256':hashlib.sha256(mapfile.read_bytes()).hexdigest()}
(REPO/'scripts/us-presidential-sources.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print(f'Validated {len(records)} elections; {sum(len(m["states"])for m in allmaps.values())} state allocations; map {mapfile.stat().st_size} bytes.')
