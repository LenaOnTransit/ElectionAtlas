"""Build the sourced Argentina 1983–2025 national archive without publishing.

The committed factual transcription separates ballot lists from coalition
subtotals. Preserve its counts: never add both levels of a results table.
Previous seats compare the same renewal cohort, not the preceding biennium.
"""
import json,re,uuid,unicodedata,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts'
TABLES=json.loads((OUT/'argentina-source-tables.json').read_text())
CHECKED='2026-10-14'
def slug(s):return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def source(label,url):return dict(label=label,url=url)
ALIASES={'Neuquén People’s Movement':"Neuquén People's Movement",'Fueguian People’s Movement':"Fueguian People's Movement",'Bloquist Party':'Blockist Party of San Juan','Renewal Party of Salta':'Salta Renewal Party','Cambienos':'Cambiemos','FREPASO':'Front for a Country in Solidarity'}
# Only stable organisations or clearly identified ballot labels are unified.
# Heterogeneous Peronist factions and new coalitions retain separate profiles.
INFO={
'Radical Civic Union':('UCR',['social-liberalism'],'Radical_Civic_Union','The broad social-liberal tradition of the UCR; its factions and candidates differ.'),
'Justicialist Party':('PJ',[],'Justicialist_Party','Peronism / Justicialism. The party has contained left- and right-wing tendencies; a single economic ideology is not assigned across these eras.'),
'Front for Victory':('FPV',['left-wing-populism'],'Front_for_Victory','Kirchnerist coalition tradition in this election era, rather than an assessment of each component party.'),
'La Libertad Avanza':('LLA',['libertarianism','right-wing-populism'],'La_Libertad_Avanza','Libertarian and right-wing populist coalition tradition; no separate personal classification is inferred.'),
"Workers' Left Front":('FIT-U',['classical-marxism'],'Workers%27_Left_Front','Trotskyist and revolutionary-socialist alliance; Marxism is the available broad ideology category.'),
'Socialist Party':('PS',['social-democracy'],'Socialist_Party_(Argentina)','Democratic socialist and social-democratic party tradition.'),
'Authentic Socialist Party':('PSA',['democratic-socialism'],'Authentic_Socialist_Party','Democratic socialist party tradition.'),
'Communist Party':('PCA',['communism'],'Communist_Party_of_Argentina','Communist party tradition.'),
'Christian Democratic Party':('PDC',['christian-democracy'],'Christian_Democratic_Party_(Argentina)','Christian-democratic party tradition.'),
'Union of the Democratic Centre':('UCEDE',['economic-liberalism'],'Union_of_the_Democratic_Centre','Liberal economic party tradition.'),
'Republican Proposal':('PRO',['liberal-conservatism'],'Republican_Proposal','Liberal-conservative party tradition.'),
'Civic Coalition ARI':('CC-ARI',['social-liberalism'],'Civic_Coalition_ARI','Broad social-liberal party tradition.'),
}
PROFILES={}
def canon(party,year):
 return 'Frente de Todos (Corrientes)' if party=='Frente de Todos' and year<2019 else ALIASES.get(party,party)
def decorate(r,party,year):
 party=canon(party,year);k=slug(party);short,tags,page,note=INFO.get(party,('',[],None,''))
 pid=str(uuid.uuid5(uuid.NAMESPACE_URL,'worldofelections.com/party/ar/'+k))
 r.update(partyId=pid,ideologyIds=['ideology-'+t for t in tags],ideologyBasis=dict(kind='party-era' if page else 'unassessed',year=year,note=note,sources=[source('Party history and political tradition',f'https://en.wikipedia.org/wiki/{page}')] if page else []))
 PROFILES[k]=dict(id=pid,country_id='ar',name=party,short_name=short,color=r['color'],ideology_ids=r['ideologyIds'],notes='',archived=False)
 return r

def election(id,date,title,body,seats=None,type='parliamentary',method='direct'):
 return dict(id=id,countryId='ar',title=title,type=type,body=body,startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round='',seriesId='',snap=False,summary='',government='',turnout=None,totalSeats=seats,resultStatus='final',resultCoverage='complete',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=1,electionMethod=method,linkedElectionIds=[])

def result(name,color='#667085',votes=None,share=None,seats=None,electoralVotes=None):
 return dict(id=slug(name)[:100],name=name,party='',color=color,votes=votes,share=share,seats=seats,previousSeats=None,electoralVotes=electoralVotes,winner=False,ideologyIds=[])

records=[];tableBy={(t['year'],t['body'],t['round']):t for t in TABLES}
WIN={1983:'Raúl Alfonsín',1989:'Carlos Menem',1995:'Carlos Menem',1999:'Fernando de la Rúa',2003:'Néstor Kirchner',2007:'Cristina Fernández de Kirchner',2011:'Cristina Fernández de Kirchner',2015:'Mauricio Macri',2019:'Alberto Fernández',2023:'Javier Milei'}
for t in TABLES:
 y=t['year'];body=t['body'];pres=body=='President';indirect=t.get('indirect',False) or pres and y<1995
 suffix='presidential'+('-runoff' if t['round']==2 else '') if pres else 'deputies' if body=='Chamber of Deputies' else 'senate'
 title=f'Argentina {"presidential runoff" if t["round"]==2 else "presidential" if pres else body} election {y}'
 e=election(f'world-argentina-{suffix}-{y}',t['date'],title,'President of Argentina' if pres else body,t['totalSeats'],'presidential' if pres else 'parliamentary','indirect' if indirect else 'direct')
 e.update(precision=t['precision'],endDate=t['end'],turnout=t['turnout'],seriesId='argentina-'+('president' if pres else 'deputies' if body=='Chamber of Deputies' else 'senate'),round=('Runoff' if t['round']==2 else 'First round' if y in [2015,2023,2003] else '') if pres else '',sources=[source(f'{y} {t["sourceTable"]} — detailed historical results',t['source'])])
 if t.get('dateSource'):e['sources'].append(source('District voting dates by chamber',t['dateSource']))
 if not t.get('indirect'):
  e['sources'].append(source('National Electoral Directorate — election archive',f'https://www.argentina.gob.ar/dine/resultados-electorales/elecciones-{y}' if y!=2025 else 'https://www.argentina.gob.ar/dine/resultados-electorales'))
 if y in [2015,2023,2025] and pres:
  urls={2015:'https://www.argentina.gob.ar/sites/default/files/p_v_definitivo_x_distrito_'+('2da_vuelta_2015_web' if t['round']==2 else 'grales_20152')+'.pdf',2023:'https://www.electoral.gob.ar/nuevo/paginas/btn/actas_esc_'+('segvta2023' if t['round']==2 else 'generales2023')+'.php'}
  e['sources'].append(source('Definitive presidential count by electoral district',urls[y]))
 if not pres and y>=2001:
  e['sources'].append(source('IPU — parliamentary election archive',f'https://data.ipu.org/parliament/AR/AR-{ "LC01" if body=="Chamber of Deputies" else "UC01"}/election/AR-{ "LC01" if body=="Chamber of Deputies" else "UC01"}-E{t["date"].replace("-","")}/' if y!=2003 else t['source']))
 if y==2025:
  e['resultStatus']='provisional';e['sources'].append(source('National Electoral Chamber — definitive district returns','https://www.electoral.gob.ar/nuevo/paginas/btn/actas2025.php'))
  e['notes']='The national vote totals and turnout follow the detailed compiled results table. They are marked provisional because this import does not independently aggregate all definitive district returns. Seats follow the completed district allocations. Detailed-table turnout and alliance groupings differ from some headline summaries.'
 if pres:
  e['voteBasis']='Votes for presidential tickets, excluding blank and invalid ballots'+('; electoral votes are electors won by the ticket' if y<1995 else '')
  e['summary']=f'{WIN[y]} '+('won the presidential runoff.' if t['round']==2 else 'was elected President of Argentina.' if y not in [2015,2023,2003] else 'won the presidency after this first-round contest.')
  e['notes']='Results aggregate all ballot endorsements of each presidential/vice-presidential ticket. Shares exclude blank and invalid ballots. Turnout follows the detailed result table, rather than rounded headline figures.'
  if y<1995:e['notes']+=' The presidency was elected indirectly through an electoral college. Votes and turnout here refer to the public election of presidential electors; electoral votes are electors allocated, not a separately counted college ballot.'
  if y==1989:e['notes']+=' Eduardo Angeloz appeared on two tickets with different running mates; those tickets remain separate.'
  if y==1995:e['notes']+=' Candidate totals sum to 17,395,284, while the English historical table prints 17,395,092 in its aggregate row. The Spanish presidential table reports 17,395,284. Candidate counts and published shares are retained; turnout 81.94% follows the detailed table (18,173,647 ballots / 22,178,201 registered), rather than the 82.08% infobox.';e['sources'].append(source('Spanish presidential table — candidate-total cross-check','https://es.wikipedia.org/wiki/Elecciones_presidenciales_de_Argentina_de_1995'))
  if y==2003:e['notes']+=' Carlos Menem led the first round but withdrew on 14 May. The planned 18 May runoff was cancelled and Néstor Kirchner became president without a second ballot.'
  for x in t['results']:
   name=x['name']+(' / '+x['runningMate'] if y==1989 and x['name']=='Eduardo Angeloz' else '')
   r=result(name,x['color'],x['votes'],x['share'],electoralVotes=x['electoralVotes']);r['party']=ALIASES.get(x['party'],x['party']);r['winner']=x['name']==WIN[y] and (y not in [2015,2023] or t['round']==2)
   if y in [2015,2023] and t['round']==1:r['advanced']=x['name'] in ([WIN[y],'Daniel Scioli'] if y==2015 else [WIN[y],'Sergio Massa'])
   e['results'].append(decorate(r,x['party'],y))
 elif t.get('indirect'):
  e['voteBasis']='Seats obtained in indirect Senate selections; no national popular-vote total'
  e['summary']=f'Argentina’s indirect Senate renewal of {y} covered {t["totalSeats"]} seats.'
  e['notes']='Selections were made during the year by provincial legislatures and, before 1998, by an electoral college for the federal capital. The date is shown to year precision because selections occurred throughout the year. Votes, shares and turnout are blank because there was no simultaneous nationwide Senate ballot. Seats show this renewal, not the entire chamber.'
  if y==1995:e['notes']+=' The constitutional transition expanded the Senate to 72 seats. Of 40 positions in this renewal, 38 were filled and two remained vacant; the unfilled positions are shown separately.'
  if y==1992:e['notes']+=' The renewal includes the first two senators for Tierra del Fuego. The capital’s public election of senatorial electors took place on 28 June; it is not treated as nationwide turnout.'
  for x in t['results']:
   name=ALIASES.get(x['name'],x['name']);r=result(name,x['color'],seats=x['seats'])
   if y in [1986,1989,1992]:
    first=tableBy[(1983,'Senate',None)];p=next((z for z in first['results'] if ALIASES.get(z['name'],z['name'])==name),None);r['previousSeats']=p['cohortSeats'][[1986,1989,1992].index(y)] if p else None
   e['results'].append(r if name=='Unfilled seats' else decorate(r,name,y))
 else:
  e['voteBasis']='Positive votes for '+body+' ballot lists; seats won in this renewal only'
  if y<2007:e['resultCoverage']='partial'
  full=254 if y<1991 and body=='Chamber of Deputies' else 257 if body=='Chamber of Deputies' else 72
  e['summary']=f'Argentina elected {t["totalSeats"]} members of its {full}-seat {body} in {y}.'
  e['notes']='The table follows the cited national party and alliance categories, including zero-seat entries. Some historical categories combine allied local lists; votes under those categories are not separate votes cast for the national party alone. Coalition subtotal rows are excluded to prevent double counting. Vote shares exclude blank and invalid ballots. Seats are won in this election, not the party’s total representation across the chamber. Previous seats compare the preceding election of the same cohort (four years earlier for deputies, six years for senators), under the same ballot label; later transfers and vacancies are excluded. Comparisons are blank where a label or coalition is not safely comparable.'
  if y==1983:e['notes']+=' The entire 254-seat Chamber was elected; previous seats are not comparable with the military-rule period.'
  if body=='Senate' and y==2001:e['notes']+=' This was the first direct election of all 72 senators. Initial two-, four- and six-year terms established the subsequent renewal cohorts; previous seats are left blank.'
  if y in [1991,1999,2003]:e['notes']+=f' National legislative ballots were held on several district dates between {t["date"]} and {t["end"]}; the date range does not mean continuous voting. '+('The 1991 renewal includes three additional Tierra del Fuego deputy seats.' if y==1991 else '')
  if y==2025:e['notes']+=' National totals remain marked provisional; the detailed-table turnout of 67.26% for deputies differs from the headline 67.43% figure.' if body=='Chamber of Deputies' else ' National vote totals remain marked provisional; the compiled Senate turnout is 68.05%.'
  grouped={}
  for x in t['results']:
   name=canon(x['name'],y);k=slug(name)
   if k in grouped:
    r=grouped[k];r['votes']+=x['votes'];r['seats']+=x['seats'];r['share']=round(r['share']+x['share'],2)
   else:grouped[k]=result(name,x['color'],x['votes'],x['share'],x['seats'])
  for r in grouped.values():
   previous=tableBy.get((y-(4 if body=='Chamber of Deputies' else 6),body,None))
   if body=='Chamber of Deputies' and y in [1985,1987]:previous=tableBy[(1983,body,None)]
   if body=='Senate' and y in [2003,2005,2007]:previous=tableBy[(2001,body,None)]
   if previous:
    pp=[z for z in previous['results'] if canon(z['name'],previous['year'])==r['name']]
    if r['name'] not in set(INFO)|{'Cambiemos','Juntos por el Cambio','Frente de Todos (Corrientes)',"Neuquén People's Movement","Fueguian People's Movement",'Blockist Party of San Juan','Salta Renewal Party'}:pp=[]
    if pp:r['previousSeats']=sum(z['cohortSeats'][[2003,2005,2007].index(y)] for z in pp) if body=='Senate' and y in [2003,2005,2007] else sum(z['cohortSeats'][0 if y==1985 else 1] for z in pp) if body=='Chamber of Deputies' and y in [1985,1987] else sum(z['seats'] for z in pp)
   if r['name']=='La Libertad Avanza' and y==2021:r['previousSeats']=0
   e['results'].append(decorate(r,r['name'],y))
 if not pres:e['results'].sort(key=lambda r:(-(r['votes'] or 0),-(r['seats'] or 0),r['name']))
 records.append(e)

# Parliament's affirmative confirmation votes are not public ballot totals.
for y,date,name,yes,no,abst,url,report in [
 (2001,'2001-12-23','Adolfo Rodríguez Saá',169,138,0,'https://www.argentina.gob.ar/normativa/nacional/decreto-989-2001-71061/texto','https://www.cidob.org/lider-politico/adolfo-rodriguez-saa'),
 (2002,'2002-01-01','Eduardo Duhalde',262,21,18,'https://www.argentina.gob.ar/normativa/nacional/decreto-2-2002-98083/texto','https://www.lanacion.com.ar/politica/duhalde-fue-designado-por-una-abrumadora-mayoria-legislativa-nid363560/')]:
 e=election(f'world-argentina-presidential-parliamentary-{y}',date,f'Argentina parliamentary presidential election {y}','President of Argentina',type='presidential',method='indirect')
 r=decorate(result(name,'#318CE7',yes,round(yes/(yes+no)*100,2)),'Justicialist Party',y);r.update(party='Justicialist Party',winner=True)
 e.update(results=[r],seriesId='argentina-president',snap=True,summary=f'Congress selected {name} as President of Argentina following the presidential succession crisis.',voteBasis='Affirmative Legislative Assembly votes as a share of votes for or against the appointment',notes=f'This is an indirect congressional selection. The assembly recorded {yes} votes for and {no} against the appointment'+(f', with {abst} abstentions' if abst else '')+'. The percentage excludes abstentions. Opposition votes are not assigned to an invented rival candidate. Public turnout is not applicable.',sources=[source('Official parliamentary appointment decree',url),source('Contemporary selection and vote count',report)])
 records.append(e)
cancel=election('world-argentina-presidential-runoff-2003','2003-05-18','Argentina presidential runoff election 2003','President of Argentina',type='presidential')
cancel.update(status='cancelled',resultStatus='not-entered',resultCoverage='partial',round='Runoff',seriesId='argentina-president',summary='The presidential runoff was cancelled following Carlos Menem’s withdrawal; Néstor Kirchner became president without a second ballot.',notes='The planned 18 May election did not take place. There are no runoff votes, vote shares or turnout figures.',voteBasis='No ballot held',sources=[source('2003 presidential election and cancelled runoff','https://en.wikipedia.org/wiki/2003_Argentine_general_election')]);records.append(cancel)
for e in records:
 e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['startDate'][:4]==e['startDate'][:4]]
records.sort(key=lambda e:(e['startDate'],e['id']))
for name,value in [('argentina-election-records',records),('argentina-party-profiles',list(PROFILES.values()))]:
 (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
print(f'{len(records)} elections; {len(PROFILES)} party/ballot-alliance profiles; {sum(len(e["results"]) for e in records)} result rows')
# Replayable transaction: never overwrite an intervening editor change.
def lit(s):return "'"+s.replace("'","''")+"'"
def j(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
lines=['begin;','do $guard$ begin']
for e in records:
 lines.append(f"if exists(select 1 from public.ea_records where id={lit(e['id'])} and data<>{j(e)}) then raise exception 'Election differs from checked import: {e['id']}'; end if;")
lines+=['end $guard$;']
for p in PROFILES.values():
 tags='ARRAY['+','.join(lit(z) for z in p['ideology_ids'])+']::text[]'
 lines.append(f"insert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values({lit(p['id'])}::uuid,'ar',{lit(p['name'])},{lit(p['short_name'])},{lit(p['color'])},{tags},'',false) on conflict(id) do nothing;")
for e in records:lines.append(f"insert into public.ea_records(id,kind,data,updated) values({lit(e['id'])},'world_election',{j(e)},now()) on conflict(id) do nothing;")
COVERAGE='Democratic-era national elections, 1983–2025: Chamber of Deputies renewals, indirect and direct Senate elections, presidential ballots and parliamentary presidential selections. Earlier elections are outside this series. Historical party categories may combine allied lists; those tables are marked partial. The 2025 national vote compilation is marked provisional. Seats count each renewal, with comparisons to the same outgoing cohort where labels remain comparable.'
lines+=[f"update public.ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(COVERAGE)}::text)),updated=now() where kind='world_country' and data->>'id'='ar' and data->>'coverageNote'='Selected records only. Earlier elections and additional result detail are still being added.';",'commit;']
(OUT/'argentina-election-import.sql').write_text('\n'.join(lines)+'\n')
