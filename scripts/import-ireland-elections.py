"""Build Ireland's national general-election archive from explicit source tables."""
from pathlib import Path
import json,re,uuid,datetime,hashlib,colorsys,collections
P=Path(__file__).resolve().parent/'ireland-election-import';EX=json.loads((P/'source-extract.json').read_text());records=[];profiles={};audit=[]
INFO={
 'Fianna Fáil':('FF','#168b55',['conservatism'],'Fianna_F%C3%A1il'),
 'Fine Gael':('FG','#1687be',['liberal-conservatism','christian-democracy'],'Fine_Gael'),
 'Labour':('Lab','#c82339',['social-democracy'],'Labour_Party_(Ireland)'),
 'Sinn Féin':('SF','#326d48',['democratic-socialism'],'Sinn_F%C3%A9in'),
 'Green':('GP','#72a83b',['green-politics'],'Green_Party_(Ireland)'),
 'Social Democrats':('SD','#8b3a91',['social-democracy'],'Social_Democrats_(Ireland)'),
 'Progressive Democrats':('PD','#244b8e',['classical-liberalism'],'Progressive_Democrats'),
 'Cumann na nGaedheal':('CnaG','#6388a0',[],'Cumann_na_nGaedheal'),
 'Clann na Poblachta':('CnaP','#bb3f39',[],'Clann_na_Poblachta'),
 'Clann na Talmhan':('CnaT','#ba8c35',['agrarianism'],'Clann_na_Talmhan'),
 "Farmers' Party":('FP','#ba8c35',['agrarianism'],"Farmers%27_Party_(Ireland)"),
 'Solidarity–PBP':('S–PBP','#ce3b55',['democratic-socialism'],'People_Before_Profit%E2%80%93Solidarity'),
 'Aontú':('A','#426949',[],'Aont%C3%BA'),
 'Independent Ireland':('II','#287668',[],'Independent_Ireland'),
}
ALIASES={'Labour Party':'Labour','Green Party':'Green','Independents 4 Change':'Inds. 4 Change','Irish Freedom Party':'Irish Freedom','Workers Party':"Workers' Party"}
def number(s):
 s=s.replace(',','').strip();m=re.match(r'^(\d+(?:\.\d+)?)(?:%|\s|/|$)',s);return float(m[1]) if m else None
def integer(s):
 n=number(s);return int(n) if n is not None and n.is_integer() else None
def source(label,url):return dict(label=label,url=url)
def profile(n,y):
 n=ALIASES.get(n,n)
 if n.startswith(('AAA–PBP','PBP–Solidarity','Solidarity–PBP')):n='Solidarity–PBP'
 if n in ['Independent','Independents','Independent Labour','Ind. Nationalist','Ind. Unionist','Independent Unionist','Unknown affiliation','Republican'] or not n:return None
 key=n
 if n=='National Party':key+=' (1995–2012)' if y<2016 else ' (2016–)'
 if n=='Sinn Féin' and y<1970:key='Sinn Féin (1917–1923)' if y<=1923 else 'Sinn Féin (pre-1970)'
 short,color,tags,page=INFO.get(n,('',None,[],None))
 if n=='Sinn Féin' and y<1970:tags=[]
 if color is None:
  h=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)/0xffffffff;color='#'+''.join(f'{round(v*255):02x}' for v in colorsys.hls_to_rgb(h,.4,.5))
 if key not in profiles:profiles[key]=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/party/ie/'+key)),country_id='ie',name=key,short_name=short,color=color,ideology_ids=['ideology-'+t for t in tags],notes='Colours are a display palette. '+('Broad party tradition: https://en.wikipedia.org/wiki/'+page if page else 'Historical ballot organisation; ideology unassessed. No continuity with a similarly named organisation is assumed.'),archived=False)
 return profiles[key],page
def base(date,body,precision='day',suffix=''):
 slug={'Dáil Éireann':'dail','Seanad Éireann':'seanad','President':'president'}[body]
 return dict(id='world-ireland-'+slug+'-'+date+('-'+suffix if suffix else ''),countryId='ie',title='Ireland '+('presidential' if body=='President' else body)+' election '+date[:4],type='presidential' if body=='President' else 'parliamentary',body=body,startDate=date,endDate='',precision=precision,dateStatus='confirmed',status='held',publication='published',round='',seriesId='IE-'+slug,snap=False,summary='',government='',turnout=None,totalSeats=1 if body=='President' else None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked='2026-10-16',notes='',articleId='',version=1,electionMethod='direct')
def row(e,n,party,v,p,s):
 y=int(e['startDate'][:4]);pr=profile(party,y);r=dict(id=e['id']+'-r'+str(len(e['results'])+1),name=n,party=party,color=pr[0]['color'] if pr else '#808080',votes=v,share=p,seats=s,previousSeats=None,electoralVotes=None,winner=False,ideologyIds=pr[0]['ideology_ids'] if pr else [])
 if pr:
  r['partyId']=pr[0]['id']
  if r['ideologyIds']:r['ideologyBasis']=dict(kind='party-era',year=y,note='Broad organisation-level tradition, not an assessment of an individual candidate.',sources=[source('Party history and political tradition','https://en.wikipedia.org/wiki/'+pr[1])])
 e['results'].append(r);return r
def date(x):
 y=re.search(r'\d{4}',x['name'])[0];m=re.search(r'(?<!\d)(\d{1,2} [A-Z][a-z]+) '+y,x['infobox']+' '+x['prose'][:600]);assert m,x['name'];return datetime.datetime.strptime(m[1]+' '+y,'%d %B %Y').strftime('%Y-%m-%d')
def citation(e,x):e['sources']=[source('Election results and historical references',x['url'])]
def reconcile(e,x,valid=None,seats=None,**extra):
 vv=sum(r['votes'] or 0 for r in e['results']);ss=sum(r['seats'] or 0 for r in e['results'])
 if valid is not None and vv!=valid and ((int(e['startDate'][:4])<=1944 and abs(vv-valid)<=10) or (e['startDate']=='1948-02-04' and valid-vv==450)):
  e['notes']+='The cited party figures sum to '+format(vv,',')+' votes, while its aggregate implies '+format(valid,',')+' valid votes. This small source discrepancy is retained rather than assigned to a party.';extra['unreconciledPublishedValidVotes']=valid;valid=None
 if valid is not None:assert vv==valid,(x['name'],'votes',vv,valid)
 if seats is not None:assert ss==seats,(x['name'],'seats',ss,seats)
 audit.append(dict(id=e['id'],source=x['url'],sha256=x['sha256'],expectedVotes=valid,recordedVotes=vv,expectedSeats=seats,recordedSeats=ss,**extra));records.append(e)
# Dáil: count only first preferences and mandates returned, including an automatically returned Ceann Comhairle.
for x in EX:
 if 'general_election' not in x['name'] or '1921' in x['name']:continue
 y=int(re.search(r'\d{4}',x['name'])[0]);e=base(date(x),'Dáil Éireann');citation(e,x)
 t=next(t for t in x['tables'] if any('Party' in r and any(('votes' in c.lower()) for c in r) and any(c in ['Seats','TDs','TDs / MPs'] for c in r) for r in t[:5]))
 hi,h=next((i,r) for i,r in enumerate(t[:5]) if 'Party' in r and any(c in ['Votes','First pref. votes','First pref votes'] for c in r))
 vi=next(i for i,c in enumerate(h) if c in ['Votes','First pref. votes','First pref votes']);pi=next(i for i,c in enumerate(h) if c in ['% FPv','FPv%','% Votes']);si=next((i for i,c in enumerate(h) if c=='Elected '+str(y)),next((i for i,c in enumerate(h) if c in ['Seats','TDs','TDs / MPs']),None));assert si is not None,(x['name'],h)
 meta={}
 for r in t[hi+1:]:
  if len(r)<=max(vi,pi,si):continue
  n=r[1]
  if r[0] not in ['','●','C']:
   if r[0] in ['Total','Total valid','Total Valid','Spoilt votes','Registered voters/Turnout','Electorate/Turnout']:meta[r[0]]=dict(votes=integer(r[vi]),share=number(r[pi]),seats=integer(r[si]))
   continue
  if not n or n=='Vacant':continue
  if y==2016 and n in ['Independent Alliance','Identity Ireland']:continue
  v=integer(r[vi]);p=number(r[pi]);s=integer(r[si])
  if s is None and '% of seats' in h and number(r[h.index('% of seats')])==0:s=0
  assert v is not None and s is not None,(x['name'],n,r)
  if y==2016 and n=='Independent':v,p,s=334814,15.70,19
  if y==1997 and n=='Independent':p=6.88
  display=n.split(' • ')[0];row(e,display,display,v,p,s)
 total=meta.get('Total',{});spoilt=meta.get('Spoilt votes',{}).get('votes');valid=meta.get('Total valid',meta.get('Total Valid',{})).get('votes')
 if valid is None and total.get('votes') is not None:valid=total['votes']-(spoilt or 0)
 if y==2016:valid=2132895;e['sources'].append(source('Oireachtas: certified 2016 votes and party allocation','https://data.oireachtas.ie/ie/oireachtas/electoralProcess/electionResults/dail/2016/2016-04-28_32nd-dail-general-election-results_en.pdf'))
 e['totalSeats']=total.get('seats') or sum(r['seats'] for r in e['results']);e['turnout']=meta.get('Registered voters/Turnout',meta.get('Electorate/Turnout',{})).get('share')
 if e['turnout'] is None:
  m=re.search(r'Turnout[: ]+(\d+(?:\.\d+)?)%',x['infobox']);e['turnout']=float(m[1]) if m else None
 e['voteBasis']='First-preference votes in contested constituencies; not transferred STV totals'
 e['notes']='Votes and shares are first preferences, not final-count transfers. Seats are mandates returned at the election, including unopposed returns and the outgoing Ceann Comhairle where applicable. No votes are invented for uncontested seats. Historical reported turnout can refer to the eligible electorate in contested constituencies, rather than all registered voters. The electorate, franchise and constituency boundaries changed over time. Colours are a display palette. '
 if y==2016:e['notes']+='The official Independent aggregate includes the Independent Alliance and the unregistered Identity Ireland candidate; those figures are not counted again as separate parties. '
 if y==1997:e['notes']+='The Independent share is calculated from 123,102 first preferences and 1,788,985 valid votes (6.88%), resolving the summary table’s inconsistent 7.9% figure. '
 if y==1918:e['notes']+='This is the all-Ireland result of the United Kingdom election, the constitutional precursor to the First Dáil. Only Sinn Féin MPs convened the revolutionary Dáil; the other elected MPs did not take their seats there. The table is not a count of members who actually attended the Dáil.'
 if y==1932:e['endDate']='1932-03-02';e['notes']+='Most constituencies voted on 16 February; polling in Leitrim–Sligo was postponed to 2 March after a candidate was killed.';e['sources'].append(source('Queen’s/Ulster University ARK: election chronology','https://www.ark.ac.uk/elections/gdala.htm'))
 if y==2024:e['sources'].append(source('Oireachtas: certified 34th Dáil result handbook','https://data.oireachtas.ie/ie/oireachtas/electoralProcess/electionResults/dail/2025/2025-04-02_34th-dail-general-election-results_en.pdf'))
 e['summary']=str(e['totalSeats'])+' seats returned to Dáil Éireann.';reconcile(e,x,valid,e['totalSeats'],meta=meta)
# The Southern Ireland ballot of 1921 was entirely unopposed; do not convert seat percentages into vote shares.
x=next(x for x in EX if x['name'].startswith('1921_'));e=base('1921-05-13','Dáil Éireann');citation(e,x);e['totalSeats']=128;e['turnout']=None;e['voteBasis']='Unopposed returns; no public vote was held';row(e,'Sinn Féin','Sinn Féin',None,None,124);row(e,'Independent Unionist','Independent Unionist',None,None,4);e['summary']='All 128 Southern Ireland seats were returned unopposed.';e['notes']='Members were returned at the close of nominations on 13 May; the scheduled polling day was 24 May, but no poll took place. This table covers Southern Ireland only. Sinn Féin treated these returns, alongside its Northern Ireland returns, as the election of the Second Dáil. No turnout or popular vote share can be calculated.';e['sources'].append(source('Oireachtas: Parliament of Southern Ireland and the 1921 election','https://www.oireachtas.ie/en/visit-and-learn/history-and-buildings/history-of-parliament-in-ireland/'));reconcile(e,x,None,128)
# One presidential election per poll: STV counts are stages of the same election, not separate runoff ballots.
for x in EX:
 if 'presidential' not in x['name']:continue
 y=int(x['name'][:4]);unopposed=y in [1938,1952,1974,1976,1983,2004];e=base(str(y)+'-01-01' if unopposed else date(x),'President','year' if unopposed else 'day');citation(e,x);e['sources'].append(source('Presidential Returning Officer: historical election record','https://www.presidentialelection.ie/previous-presidential-elections/index.html'));t=next(t for t in x['tables'] if any('Candidate' in r and ('Count 1' in r or 'Votes' in r or 'Nominated by' in r) for r in t[:3]));hi,h=next((i,r) for i,r in enumerate(t[:3]) if 'Candidate' in r)
 vi=h.index('Count 1') if 'Count 1' in h else h.index('Votes') if 'Votes' in h else None;pi=h.index('% 1st Pref') if '% 1st Pref' in h else h.index('%') if '%' in h else None;ni=h.index('Candidate')+1 if h.count('Candidate')==2 else h.index('Candidate');nom=h.index('Nominated by')
 meta=' '.join(r[0] for r in t);vvalid=None;turn=None;stages=[]
 for r in t[hi+1:]:
  if len(r)<=max(ni,nom,vi or 0):continue
  n=r[ni]
  if not n or n.startswith(('Electorate:','Source:')) or n in ['Total','Valid votes','Invalid/blank votes','Total votes','Registered voters/turnout']:continue
  v=integer(r[vi]) if vi is not None else None;p=number(r[pi]) if pi is not None else None
  nomin=r[nom+1] if h.count('Nominated by')==2 else r[nom]
  party='Independent'
  for q in ['Fianna Fáil','Fine Gael','Labour','Sinn Féin']:
   if q in nomin:party=q;break
  if n in ['Douglas Hyde','Cearbhall Ó Dálaigh','Catherine Connolly'] or (n=='Michael D. Higgins' and y==2018):party='Independent'
  rr=row(e,n,party,v,p,None)
  if vi is not None:
   counts=[(c,integer(r[i]) if i<len(r) else None) for i,c in enumerate(h) if re.fullmatch(r'Count \d+',c)];stages.append((n,counts))
 if vi is None:
  assert len(e['results'])==1,x['name'];e['results'][0]['winner']=True;e['summary']=e['results'][0]['name']+' returned unopposed; no poll was held.';e['voteBasis']='Unopposed return; no ballots cast';e['turnout']=None;e['notes']='Only one valid nomination remained. The candidate was declared elected without a poll; votes, vote share and turnout therefore do not apply. Only the election year is asserted: a planned polling day or inauguration is not substituted for the unopposed declaration.'
 else:
  m=re.search(r'Valid: ([\d,]+)',meta);vvalid=int(m[1].replace(',','')) if m else None
  if vvalid is None:
   vr=next((r for r in t if r[0]=='Total'),None);vvalid=integer(vr[vi]) if vr else None
  m=re.search(r'Turnout: (?:[\d,]+ \()?(\d+(?:\.\d+)?)%',meta);e['turnout']=float(m[1]) if m else None
  if e['turnout'] is None:
   tr=next((r for r in t if r[0]=='Registered voters/turnout'),None);e['turnout']=number(tr[pi]) if tr else None
  final_count=max((len(c) for _,c in stages),default=0)
  finalists=[(n,c[-1][1]) for n,c in stages if c and c[-1][1] is not None]
  winner=max(finalists,key=lambda a:a[1])[0] if finalists else max(e['results'],key=lambda r:r['votes'])['name'];next(r for r in e['results'] if r['name']==winner)['winner']=True
  e['summary']=winner+' elected'+(' after STV transfers.' if final_count>1 else ' on the first count.')
  e['voteBasis']='First-preference votes and share of valid ballots; winner determined after all STV counts'
  e['notes']='This table reports first preferences only. The elected-candidate marker reflects the final result, so the first-preference leader need not be the winner. Later counts redistribute the same ballots and are not added to first preferences or recorded as another polling round. '
  if final_count>1:e['notes']+='Final reported count: '+ '; '.join(n+' '+format(v,',') for n,v in finalists)+'. Non-transferable ballots are not assigned to a candidate.'
 e['sources'].append(source('Presidential Returning Officer: complete result handbook','https://www.presidentialelection.ie/wp-content/uploads/2026/01/Presidential-Elections-1938-2025.pdf'))
 if y==2025:e['turnout']=45.83;e['notes']+='Jim Gavin stopped campaigning before polling but remained on the ballot; his 103,568 valid votes are included. The official poll was 1,656,436, including 213,738 invalid ballots.';e['sources'].append(source('Presidential Returning Officer: certified 2025 result','https://www.presidentialelection.ie/2025-presidential-election/index.html'))
 reconcile(e,x,vvalid,None,stvCounts=stages)
# Seanad since 1938: sum the seven elected constituency columns; never import the eleven nominees as seats won.
YEARS={2:1938,3:1938,4:1943,5:1944,6:1948,7:1951,8:1954,9:1957,10:1961,11:1965,12:1969,13:1973,14:1977,15:1981,16:1982,17:1983,18:1987,19:1989,20:1993,21:1997,22:2002,23:2007,24:2011,25:2016,26:2020,27:2025}
PRECISE={2:('1938-03-01','','month'),3:('1938-08-01','','month'),17:('1983-01-31','','day'),23:('2007-07-23','2007-07-24','day'),24:('2011-04-26','2011-04-27','day'),25:('2016-04-25','2016-04-26','day'),26:('2020-03-30','2020-03-31','day'),27:('2025-01-29','2025-01-30','day')}
for x in EX:
 m=re.fullmatch(r'(\d+)(?:st|nd|rd|th)_Seanad',x['name'])
 if not m:continue
 term=int(m[1]);y=YEARS[term];d,end,precision=PRECISE.get(term,(str(y)+'-01-01','','year'));e=base(d,'Seanad Éireann',precision,str(term));e['endDate']=end;e['round']=x['name'].replace('_',' ');citation(e,x);e['electionMethod']='indirect';e['totalSeats']=60;t=next(t for t in x['tables'] if 'Origin Party' in t[0] and 'Nominated' in t[0]);h=t[1];nom=h.index('Nominated');elected=[]
 for r in t[2:]:
  if not r or r[0]=='Total':continue
  if len(r)<=nom:continue
  n=r[1];vals=[integer(c) for c in r[2:nom]];assert all(v is not None for v in vals),(x['name'],r);s=sum(vals);row(e,n,n,None,None,s);elected.append(dict(name=n,elected=s,nominated=integer(r[nom])))
 e['voteBasis']='Elected mandates only: 43 vocational-panel seats and six university seats; no national vote share'
 e['summary']='49 senators elected; the Taoiseach’s 11 nominees are excluded from the result table.'
 e['notes']='Party totals add only the seven elected-constituency columns in the initial-composition table. Eleven Taoiseach nominees are excluded from seats won; the chamber capacity remains 60. Vocational panels are elected by a political electoral college and university seats by registered graduates. There is no single national popular vote, share or turnout, and unrelated panel ballots are not summed. Party affiliations are descriptive; party labels do not appear on Seanad ballot papers. '+('Only the election year is asserted; opening sittings and predecessor term-end dates are not substituted for polling dates.' if precision=='year' else 'Dates cover the documented poll/close-of-poll period, rather than the first sitting or appointments.')
 e['sources'].append(source('Electoral Commission: Seanad electoral system','https://www.electoralcommission.ie/seanad-eireann/'))
 if term==27:e['sources'].append(source('Oireachtas: 2025 Seanad result handbook','https://data.oireachtas.ie/ie/oireachtas/electoralProcess/electionResults/seanad/2026/2026-05-20_seanad-general-election-2025-results-handbook_en.pdf'))
 if term==17:e['sources'].append(source('IPU: Seanad polling on 31 January 1983','https://data.ipu.org/election-summary/PDF/IRELAND_1982_E_2.PDF'))
 if term in [2,3]:e['sources'].append(source('University College Dublin: historical Seanad elections','https://historyhub.ie/past-reforms-present-policy'))
 reconcile(e,x,None,49,term=term,allocation=elected)
# Free State renewals: use elected cohorts, not the entire continuing 60-member composition.
for y in [1928,1931,1934]:
 x=next(x for x in EX if x['name']==str(y)+'_Seanad');e=base(str(y)+'-01-01','Seanad Éireann','year','free-state');e['seriesId']='IE-seanad-free-state';e['electionMethod']='indirect';citation(e,x);t=x['tables'][1];h=next(r for r in t[:3] if 'Name' in r);ni=h.index('Name');pi=len(h)-1 if y==1928 else h.index('Party');members=[]
 for r in t:
  if any(re.match(r'^Elected in '+str(y)+r'(?: for|$)',c) for c in r):members.append((r[ni],r[pi]))
 counts=collections.Counter(p for _,p in members)
 for p,s in counts.items():row(e,p,p,None,None,s)
 expected={1928:17,1931:23,1934:23}[y];e['totalSeats']=60;e['voteBasis']='Mandates in the elected renewal cohort; continuing senators and appointments excluded';e['summary']=str(expected)+' senators returned in the documented renewal cohort.';e['notes']='The table counts only members identified as elected in this renewal, not the full post-election chamber. Votes and public turnout are unavailable/not applicable to this parliamentary electorate. The election year is shown; sitting dates are not polling dates. Previous seats are omitted because the rotating cohorts and casual vacancies differ.'
 if y==1934:e['sources'].append(source('Oireachtas centenary history: 23 seats filled in 1934','https://data.oireachtas.ie/ie/oireachtas/communications/other/2023/2023-10-01_100-bliain-de-sheanad-ireann_en.pdf'));e['notes']+='The Oireachtas centenary history confirms 23 seats; this resolves the secondary lead’s conflicting figure of 22.'
 reconcile(e,x,None,expected,members=members)
for y in [1922,1925]:
 x=next(x for x in EX if x['name']==str(y)+'_Seanad_election');e=base('1922-12-07' if y==1922 else '1925-09-17','Seanad Éireann');citation(e,x);e['seriesId']='IE-seanad-free-state';e['totalSeats']=60
 if y==1922:
  e['electionMethod']='indirect';t=x['tables'][0];counts=collections.Counter()
  for r in t[1:]:
   if len(r)>5 and integer(r[5]) is not None:counts[r[1]]+=1
  for p,s in counts.items():
   display='Pro-Treaty / Cumann na nGaedheal supporters' if p=='Cumann na nGaedheal' else p;row(e,display,display,None,None,s)
  e['summary']='Dáil members elected 30 senators; 30 Executive Council appointees are excluded.';e['notes']='Seats show the 30 winners elected by TDs on 7 December. The source retrospectively labels some members Cumann na nGaedheal, which was established in 1923; these are identified as pro-Treaty supporters here. The weighted count values are not presented as public vote totals.';e['voteBasis']='Thirty mandates elected by the Dáil; nominees and public turnout excluded';reconcile(e,x,None,30)
 else:
  t=x['tables'][0]
  for r in t[1:]:
   if len(r)<4 or r[0]!='':continue
   row(e,r[1],r[1],integer(r[2]),number(r[3]),integer(r[4]) if len(r)>4 else None)
  e['turnout']=23.4;e['voteBasis']='National first-preference votes; seats are the 19 mandates contested';e['summary']='A direct national STV poll elected 19 senators to join the continuing members.';e['notes']='The table covers this 19-seat renewal only, not the complete 60-seat chamber. Cumann na nGaedheal supporters are a retrospective grouping rather than an official party endorsement. Unknown affiliations remain separate; no seats are invented for that row.';reconcile(e,x,305701,19)
# Compare the immediately preceding result in the same scope; independent aggregates are not a single party.
for body in ['Dáil Éireann','Seanad Éireann']:
 prev=None
 for e in sorted((e for e in records if e['body']==body and (body=='Dáil Éireann' or e['seriesId']=='IE-seanad')),key=lambda e:e['startDate']):
  if prev and not (body=='Dáil Éireann' and e['startDate'][:4] in ['1921','1922']):
   for r in e['results']:
    p=next((p for p in prev['results'] if p.get('partyId') and p.get('partyId')==r.get('partyId')),None)
    if p:r['previousSeats']=p['seats']
  prev=e
for e in records:
 y=e['startDate'][:4];same=[o for o in records if o['body']==e['body'] and o['startDate'].startswith(y)];detail=datetime.datetime.strptime(e['startDate'],'%Y-%m-%d').strftime('%B') if len(same)>1 else ''
 e['title']='Ireland '+('presidential' if e['body']=='President' else e['body'])+' election'+(' ('+detail+')' if detail else '')+' '+y
for n,v in [('records',sorted(records,key=lambda e:(e['startDate'],e['body']))),('parties',list(profiles.values())),('reconciliation',audit)]: (P/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(len(records),'records;',sum(len(e['results']) for e in records),'result rows;',len(profiles),'party profiles')
