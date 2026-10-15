"""Build Denmark's national archive from checked source transcriptions; no database access."""
from pathlib import Path
import json,re,uuid,hashlib,colorsys,datetime,copy
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/denmark-election-import'
EX=json.loads((OUT/'source-extract.json').read_text());BASE=json.loads((OUT/'pre-import-backup.json').read_text());ARCH=json.loads((OUT/'official-archive-years.json').read_text())
CHECKED='2026-10-15';BOOK='https://www.dst.dk/pubfile/34694/ftvalg2019'
ALIASES={'Social Democratic Party':'Social Democrats','Danish Social Liberal Party':'Social Liberals','Conservatives':"Conservative People's Party",'Green Left':"Socialist People's Party",'Justice Party of Denmark':'Justice Party',"Christian People's Party":'Christian Democrats','New Alliance':'Liberal Alliance','Partii Naleraq':'Naleraq'}
INFO={
 'Social Democrats':('A','#a82721',['social-democracy'],'Social_Democrats_(Denmark)'),
 'Social Liberals':('B','#e5007d',['social-liberalism'],'Danish_Social_Liberal_Party'),
 "Conservative People's Party":('C','#00583c',['liberal-conservatism'],'Conservative_People%27s_Party_(Denmark)'),
 'Venstre':('V','#254b87',['liberalism'],'Venstre_(Denmark)'),
 "Socialist People's Party":('SF','#c31924',['democratic-socialism'],'Green_Left_(Denmark)'),
 'Red–Green Alliance':('Ø','#e6801a',['socialism','green-politics'],'Red%E2%80%93Green_Alliance_(Denmark)'),
 "Danish People's Party":('O','#e4bd39',['national-conservatism'],'Danish_People%27s_Party'),
 'Liberal Alliance':('I','#00a0b0',['classical-liberalism'],'Liberal_Alliance_(Denmark)'),
 'The Alternative':('Å','#2b8738',['green-politics'],'The_Alternative_(Denmark)'),
 'Christian Democrats':('K','#b68320',['christian-democracy'],'Christian_Democrats_(Denmark)'),
 'Communist Party of Denmark':('DKP','#b8131b',['communism'],'Communist_Party_of_Denmark'),
 'Left Socialists':('VS','#b12641',['socialism'],'Left_Socialists'),
 'Centre Democrats':('CD','#c45c2a',[],'Centre_Democrats_(Denmark)'),
 'Progress Party':('Z','#d5b324',[],'Progress_Party_(Denmark)'),
 'Justice Party':('E','#653f82',[],'Justice_Party_of_Denmark'),
 'Moderates':('M','#824c97',['liberalism'],'Moderates_(Denmark)'),
 'Denmark Democrats':('Æ','#7a9ed2',[],'Denmark_Democrats'),
 'New Right':('D','#176578',['national-conservatism'],'New_Right_(Denmark)'),
 'Højre':('H','#27754a',['conservatism'],'H%C3%B8jre'),
 'National Liberal Party':('NLP','#caaa35',['liberalism'],'National_Liberal_Party_(Denmark)'),
 'Society of the Friends of Peasants':('Bondevennerne','#4d8056',[],'Society_of_the_Friends_of_Peasants'),
 'Borgernes Parti - Lars Boje Mathiesen':('H','#4b8e92',[],'Citizens%27_Party_(Denmark)')}
profiles={};records=[];audit=[]
def num(s):
 s=s.replace(',','').strip()
 return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else None
def integer(s):
 n=num(s);return int(n) if n is not None and n.is_integer() else None
def canon(n,y):
 n=re.sub(r'\s*\[ da \]','',n)
 if y<=1892 and n in ['Liberals','Venstre Reform Party']:return 'Venstre (Left grouping)'
 return ALIASES.get(n,n)
def profile(name,y):
 if name in ['Others','Other parties','Independents','Independent','Faroese representative'] or ' – ' in name or 'Coalition' in name:return None
 key=name
 if name=='Højre':key+=' (1848–1866)' if y<=1866 else ' (1881–1915)' if y>=1881 else ' (Right grouping '+str(y)+')'
 # Do not force continuity across the nineteenth-century Left factions.
 if name=='Venstre (Left grouping)':key+=' '+str(y)
 short,color,tags,page=INFO.get(name,('',None,[],None))
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.40,.50))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/dk/'+key)),country_id='dk',name=key,short_name=short,color=color,ideology_ids=['ideology-2da13b9e-92bd-488f-9f72-de3dbbacaa39' if t=='socialism' else 'ideology-'+t for t in tags],notes='Historical ballot organisation. Colours are a display palette. Ideology describes the broad party tradition, not each candidate. '+('Party history: https://en.wikipedia.org/wiki/'+page if page else 'Ideology unassessed; no continuity with similarly named parties is assumed.'),archived=False)
 return profiles[key],page

def result(e,name,votes,share,seats):
 original_name=name;name=canon(name,int(e['startDate'][:4]));p=profile(name,int(e['startDate'][:4]));r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=name,party=name if p else '',color=p[0]['color'] if p else '#808080',votes=votes,share=share,seats=seats,previousSeats=None,electoralVotes=None,winner=False,ideologyIds=p[0]['ideology_ids'] if p else [])
 if p:
  r['partyId']=p[0]['id']
  if p[1]:
   r['ideologyBasis']=dict(kind='party-era' if r['ideologyIds'] else 'unassessed',year=int(e['startDate'][:4]),note='Broad organisation-level tradition; no candidate-specific ideology is inferred.',sources=[dict(label='Party history and political tradition',url='https://en.wikipedia.org/wiki/'+p[1])])
 if original_name=='New Alliance':
  r['name']='New Alliance';r['party']='New Alliance';r['ideologyIds']=[];r['ideologyBasis']=dict(kind='unassessed',year=2007,note='The founding New Alliance platform is not assigned the later Liberal Alliance classification.',sources=[])
 e['results'].append(r);return r

def base(date,body,month=''):
 return dict(id='world-denmark-'+('landsting' if body=='Landsting' else 'folketing')+'-'+date,countryId='dk',title='Denmark '+body+' election '+(month+' ' if month else '')+date[:4],type='parliamentary',body=body,startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round='',seriesId='dk-'+body.lower(),snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=1,electionMethod='indirect' if body=='Landsting' else 'direct')

def source(label,url):return dict(label=label,url=url)
def official(y):
 for label,cid in ARCH.items():
  if str(y) in label:return 'https://www.dst.dk/da/Statistik/Publikationer/VisPub?cid='+cid
 return 'https://www.dst.dk/da/Statistik/Publikationer/VisPub?cid=20242'
for x in EX:
 name=x['name'];upper='Landsting' in name
 if not x['tables'] or 'Rigsrådets' in name:continue
 year=int(re.search(r'\d{4}',name)[0]);text=x['prose'];date_match=re.search(r'(\d{1,2} [A-Z][a-z]+ '+str(year)+')',text)
 if name=='1915_Danish_Folketing_election':date='1915-05-07' # Official Statistics Denmark bibliography, not the conflicting secondary lead.
 elif name=='1947_Danish_Landsting_election':date='1947-04-11'
 elif name=='1953_Danish_Landsting_election':date='1953-04-28'
 elif name=='1951_Danish_Landsting_election':date='1951-04-10'
 else:
  assert date_match,(name,text[:150]);date=datetime.datetime.strptime(date_match[0],'%d %B %Y').strftime('%Y-%m-%d')
 month=name.split('_')[0] if name.split('_')[0].isalpha() else 'April' if name=='1953_Danish_Folketing_election' else 'September' if name=='1953_Danish_general_election' else ''
 e=base(date,'Landsting' if upper else 'Folketing',month);table=next(t for t in reversed(x['tables']) if any('Votes' in r for r in t)) if any(any('Votes' in r for r in t) for t in x['tables']) else x['tables'][-1]
 hi,h=next((i,r) for i,r in enumerate(table) if 'Party' in r and ('Won' in r or "People's" in r or (upper and 'Electors' in r and 'Parliament' in r) or (not upper and 'Seats' in r and len(set(r))>2)))
 vi=h.index('Votes') if 'Votes' in h else None;pi=h.index('%') if '%' in h else None
 si=h.index("People's") if "People's" in h else h.index('Won') if 'Won' in h else h.index('Electors') if upper else h.index('Seats')
 section='Denmark';meta={};rawrows=[]
 for r in table[hi+1:]:
  if len(set(r))==1 and r[0] in ['Denmark','Denmark proper','Faroe Islands','Greenland']:section=r[0];continue
  if section in ['Faroe Islands','Greenland']:continue
  if len(r)<=si:continue
  n=r[1] if len(r)>1 else r[0]
  if n.startswith('Source:') or not n or n in ['Party','Seats']:continue
  if n in ['Total','Valid votes','Invalid/blank votes','Invalid votes','Blank votes','Total votes','Registered voters/turnout']:
   meta[n]=dict(votes=integer(r[vi]) if vi is not None else None,share=num(r[pi]) if pi is not None else None,seats=integer(r[si]));continue
  v=integer(r[vi]) if vi is not None else None;p=num(r[pi]) if pi is not None else None;s=integer(r[si]);
  if v is None and s is None and p is None:continue
  rawrows.append(dict(name=n,votes=v,share=p,seats=s));result(e,n,v,p,s)
 assert e['results'],name
 total=meta.get('Total',{});seat_sum=sum(r['seats'] or 0 for r in e['results']);votes=sum(r['votes'] or 0 for r in e['results']);expected=total.get('seats')
 assert expected is None or expected==seat_sum,(name,expected,seat_sum)
 e['sources']=[source('Historical result table and cited electoral bibliography',x['url'])]
 if not upper:
  e['sources'].append(source('Statistics Denmark: historical election publication archive',official(year)))
  if year==2022:e['sources'].append(source('Statistics Denmark: certified 2022 mainland votes and turnout','https://www.dst.dk/valg/Valg1968094/valgopg/valgopgHL.htm'))
  if year>=1918:e['sources'].append(source('Statistics Denmark: 2019 election report, historical series and bibliography',BOOK))
  capacity=re.search(r'All ([\d,]+) seats',x['infobox']);e['totalSeats']=int(capacity[1].replace(',','')) if capacity else seat_sum
  e['voteBasis']='Mainland Denmark valid votes where available; separate North Atlantic counts are outside this table'
  e['notes']='Seats are the election result for the listed Danish party or historical grouping, not a later parliamentary membership snapshot. Where the source separates Denmark proper from the Faroe Islands and Greenland, only the mainland count is transcribed here; vote shares and turnout use that same electorate. Separate territorial results are not silently combined with mainland percentages. Missing vote counts remain blank, including elections with uncontested constituencies. Historical group and alliance labels are preserved without dividing shared lists into invented party votes. Colours are a display palette; ideology labels describe broad party traditions. Coverage is partial.'
  if year<1918:e['notes']+=' The franchise was restricted and changed over time; reported turnout is a share of the then-eligible electorate, not the adult population. Uncontested returns can limit historical vote and turnout comparability.'
  if year<=1892:e['notes']+=' Venstre (Left grouping) denotes the historical Left factions and is not retroactively called the Venstre Reform Party, which was established in 1895.'
  if name=='1915_Danish_Folketing_election':e['notes']+=' The date follows Statistics Denmark’s official publication bibliography (7 May), resolving a conflicting 6 May date in the secondary article. Most constituencies were uncontested and no national vote tally is assigned.'
  e['turnout']=meta.get('Registered voters/turnout',{}).get('share')
 else:
  e['totalSeats']=seat_sum;e['electionMethod']='indirect'
  e['voteBasis']='Public votes for electoral-college electors where recorded; seats are mandates selected through that electoral college'
  e['notes']='The Landsting was the national upper chamber until 1953. The seat column transcribes only this election’s constituency/electoral-college mandates (the source’s Won, Electors or People’s seats column), not the entire post-election chamber. Royal appointments, seats not up for election, and members selected separately by the outgoing parliament are excluded. Where available, votes and shares are public ballots selecting electors, not votes cast by those electors for Landsting members. Previous seats remain blank because rotating renewals cover different constituencies. Coverage is partial; no parliamentary-composition total is substituted for mandates won in this ballot.'
  e['turnout']=meta.get('Registered voters/turnout',{}).get('share')
  if year==1947:e['notes']+=' The table reports 28 constituency mandates; the separately chosen Faroese member is not assigned to a party or added to these public vote rows.'
  if year==1951:e['notes']+=' The public elected electors on 3 April; the Landsting members were selected on 10 April.'
  if year==1953:e['notes']+=' The public chose electors on 21 April; they chose Landsting members on 28 April. The table covers 56 constituency mandates and excludes the separately selected parliamentary and Faroese members.'
  if year in [1918,1920]:e['notes']+=' The article’s Electors column denotes seats selected by electors, not a count of electoral-college members.'
  if year==1943:e['notes']+=' The source’s Parliament column combines separately selected and continuing members; those figures are not treated as seats won in the public electoral-college ballot.'
  if year in [1928,1936,1951]:e['sources'].append(source('Statistics Denmark: historical election publication archive',official(year)))
 e['summary']=f'{seat_sum} '+('constituency mandates selected through the electoral college.' if upper else 'seats allocated in the transcribed result table.')
 if year==1943:e['notes']+=' This election took place during the German occupation of Denmark.'
 records.append(e);audit.append(dict(id=e['id'],source=x['url'],sourceSha256=x['sha256'],expectedVotes=total.get('votes'),recordedVotes=votes if any(r['votes'] is not None for r in e['results']) else None,expectedSeats=expected,recordedSeats=seat_sum,scope='constituency renewal mandates' if upper else 'Denmark proper where territorially separated',sourceSeatColumn=h[si]))
# Compare only matched organisations in the immediately preceding Folketing election.
previous={}
for e in sorted((e for e in records if e['body']=='Folketing'),key=lambda e:e['startDate']):
 y=int(e['startDate'][:4])
 for r in e['results']:
  if y>=1910 and r.get('partyId') and r['partyId'] in previous:r['previousSeats']=previous[r['partyId']]
 previous={r['partyId']:r['seats'] for r in e['results'] if r.get('partyId') and r['seats'] is not None}
e=copy.deepcopy(next(x['data'] for x in BASE if x['id']=='world-denmark-2026'));old_rows=e['results'];e['results']=[];e['title']='Denmark Folketing election 2026';e['checked']=CHECKED;e['version']+=1;e['seriesId']='dk-folketing';e['electionMethod']='direct'
labels={'a-socialdemokratiet':'Social Democrats','b-radikale-venstre':'Social Liberals','c-det-konservative-folkeparti':"Conservative People's Party",'f-sf-socialistisk-folkeparti':"Socialist People's Party",'h-borgernes-parti-lars-boje-mathiesen':'Borgernes Parti - Lars Boje Mathiesen','i-liberal-alliance':'Liberal Alliance','m-moderaterne':'Moderates','o-dansk-folkeparti':"Danish People's Party",'v-venstre-danmarks-liberale-parti':'Venstre','danmarksdemokraterne-inger-st-jberg':'Denmark Democrats','enhedslisten-de-r-d-gr-nne':'Red–Green Alliance','alternativet':'The Alternative','uden-for-partierne':'Independents'}
for old in old_rows:
 r=result(e,labels[old['id']],old['votes'],old['share'],old['seats'])
 if r.get('partyId') in previous:r['previousSeats']=previous[r['partyId']]
e['summary']='Certified mainland results for the 2026 Folketing election.'
records.append(e)
audit.append(dict(id=e['id'],source=e['sources'][-1]['url'],expectedVotes=sum(r['votes'] for r in old_rows),recordedVotes=sum(r['votes'] for r in old_rows),expectedSeats=175,recordedSeats=175,scope='Existing 2026 mainland count preserved; party identity, colour, previous seats and SEO title added',sourceSeatColumn='Seats'))
records.sort(key=lambda e:(e['startDate'],e['body']))
for n,data in [('records',records),('parties',list(profiles.values())),('reconciliation',audit)]: (OUT/(n+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(len(records),'elections;',sum(len(e['results']) for e in records),'rows;',len(profiles),'party profiles')
