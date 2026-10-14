#!/usr/bin/env python3
"""Build eight native-boundary Dutch parliamentary municipal datasets.

Run fetch-netherlands-geography-history.mjs first. Requires pyshp, shapely and
pyproj for archived geometry; output and manifest need no runtime dependencies.
No database writes. Every local and national party total must reconcile.
"""
import collections,hashlib,html,io,json,logging,math,re,unicodedata,zipfile
from pathlib import Path
import shapefile
from shapely.geometry import shape,Polygon,MultiPolygon
from shapely.ops import unary_union,transform
from shapely import make_valid
from pyproj import Transformer
logging.getLogger('shapefile').setLevel(logging.ERROR)
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/dutch-geography'
SPECS={2003:'TK20030122',2006:'TK20061122',2010:'TK20100609',2012:'TK20120912',2017:'TK20170315',2021:'TK20210317',2023:'TK20231122',2025:'TK20251029'}
DATE={2003:'22 January 2003',2006:'22 November 2006',2010:'9 June 2010',2012:'12 September 2012',2017:'15 March 2017',2021:'17 March 2021',2023:'22 November 2023',2025:'29 October 2025'}
TRANSITIONS=json.loads((ROOT/'scripts/netherlands-boundary-transitions.json').read_text())
ORIGINAL=json.loads((ROOT/'public/nl-municipal-2023-2025.json').read_text())
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',html.unescape(s)).encode('ascii','ignore').decode().lower())
def slug(s):return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',html.unescape(s)).encode('ascii','ignore').decode().lower()).strip('-')
def integer(s):
 if isinstance(s,int):return s
 assert isinstance(s,str) and re.fullmatch(r'\d[\d.]*',s),s
 return int(s.replace('.',''))
def src(label,url):return {'label':label,'url':url}
# Electoral lists retain distinct IDs. The joint GroenLinks/PvdA list is not
# retrospectively substituted for the two separate lists in older elections.
ALIAS={}
for key,names in {
 'cda':['CDA','Christen Democratisch Appèl (CDA)'],
 'pvda':['PvdA','Partij van de Arbeid (P.v.d.A.)'],
 'gl':['GL','GROENLINKS'],
 'vvd':['VVD'],'d66':['D66','Democraten 66 (D66)'],
 'pvv':['PVV','PVV (Partij voor de Vrijheid)'],
 'sp':['SP','SP (Socialistische Partij)'],
 'cu':['CU','ChristenUnie'],'sgp':['SGP','Staatkundig Gereformeerde Partij (SGP)'],
 'pvdd':['PvdD','Partij voor de Dieren'],'lpf':['LPF','Fortuyn'],
 'fvd':['Forum voor Democratie'],'bij1':['BIJ1','Artikel 1'],
 'lp':['Libertarische Partij (LP)','LP (Libertaire Partij)'],
 'volt':['Volt'],'denk':['DENK'],'ja21':['JA21'],'bbb':['BBB'],'50plus':['50PLUS'],
 'piratenpartij':['Piratenpartij']}.items():
 for name in names:ALIAS[norm(name)]=key
def pid(name,year):return ALIAS.get(norm(name),f'{year}-{slug(name)}')
BASE={p['id']:p for p in ORIGINAL['parties']}
BASE.update({'pvda':{'name':'PvdA','color':'#E10019'},'gl':{'name':'GroenLinks','color':'#008B47'},'lpf':{'name':'LPF','color':'#F8C500'}})
LEFT={'gl','pvda','gl-pvda','sp','pvdd','denk','bij1'};RIGHT={'pvv','vvd','cda','nsc','bbb','fvd','sgp','ja21','bvnl','lp','lpf'};CENTRE={'cu','50plus','d66','volt'}
def metadata(key,name):
 b=BASE.get(key,{})
 return {'id':key,'name':('Artikel 1' if name=='Artikel 1' else b.get('name',html.unescape(name))),'color':b.get('color','#777777'),'classification':'left' if key in LEFT else 'right' if key in RIGHT else 'centre' if key in CENTRE else 'unclassified'}
GEO_URLS={2003:'https://www.cbs.nl/-/media/imported/documents/2008/01/2003-buurt-kaart.zip?sc_lang=nl-nl',2006:'https://www.cbs.nl/-/media/imported/documents/2010/13/buurt_2006_gn2.zip?sc_lang=nl-nl',2010:'https://download.cbs.nl/regionale-kaarten/2010-buurtkaart-shape-versie-3.zip',2012:'https://download.cbs.nl/regionale-kaarten/2012-buurtkaart-shape-versie-1.zip',2017:'https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1/collections/gemeente_gegeneraliseerd/items?jaarcode=2017&limit=1000&f=json',2021:'https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1/collections/gemeente_gegeneraliseerd/items?jaarcode=2021&limit=1000&f=json'}
NAME_ALIAS={'sgravenhage':'denhaag','shertogenbosch':'denbosch','gaasterlansleat':'gaasterlandsloten','skarsterlan':'skarsterlan','wunseradiel':'wonseradeel','haarlemmerliedeca':'haarlemmerliedeenspaarnwoude','kollumerlandca':'kollumerlandennieuwkruisland','nuenenca':'nuenengerwenennederwetten','hetbildt':'hetbildt','sudwestfryslan':'sudwestfryslan'}
def area_key(name,province='',code=''):
 k=norm(name)
 if k in ['hengelo','hengelog','hengeloo']:
  return 'hengelog' if code=='GM0248' or province=='Gelderland' or k=='hengelog' else 'hengeloo'
 if k in ['bergen','bergenl','bergennh']:
  return 'bergenl' if code=='GM0893' or province=='Limburg' or k=='bergenl' else 'bergennh'
 if k in ['valkenburg','valkenburgzh','valkenburgaandengeul','valkenburgaandegeul']:
  return 'valkenburgaandegeul' if code=='GM0994' or province=='Limburg' or 'geul' in k else 'valkenburgzh'
 return NAME_ALIAS.get(k,k)
rd=Transformer.from_crs(4326,28992,always_xy=True).transform
GEOMETRY={}
GEO_URLS[2023]='https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1/collections/gemeente_gegeneraliseerd/items?jaarcode=2023&limit=1000&f=json'
for year in [2003,2006,2010,2012,2017,2021,2023]:
 groups={}
 if year<2017:
  z=zipfile.ZipFile(CACHE/f'boundaries-{year}.zip');n=next(n for n in z.namelist() if n.endswith('.shp') and 'gem' in n.lower().split('/')[-1]);stem=n[:-4]
  reader=shapefile.Reader(shp=io.BytesIO(z.read(stem+'.shp')),shx=io.BytesIO(z.read(stem+'.shx')),dbf=io.BytesIO(z.read(stem+'.dbf')),encoding='cp850' if year==2003 else 'cp1252')
  rows=[(r.record.as_dict(),shape(r.shape.__geo_interface__)) for r in reader.iterShapeRecords()]
 else:
  j=json.loads((CACHE/f'geometry-{year}-generalized.json').read_text());rows=[(f['properties'],transform(rd,shape(f['geometry']))) for f in j['features']]
 for p,g in rows:
  if p.get('WATER')=='JA':continue
  c=p.get('GM_CODE',p.get('GM2003',p.get('statcode')));code='GM'+str(c).replace('GM','').zfill(4)
  if code in ['GM0000','GM9999']:continue
  name=p.get('GM_NAAM',p.get('statnaam',''));assert name,(year,code)
  population=p.get('AANT_INW',p.get('AANTINW'))
  if population is not None and population<0:population=None
  entry=groups.setdefault(code,{'name':name,'population':population,'geometry':[]});entry['geometry'].append(make_valid(g));
 for code,entry in groups.items():entry['geometry']=unary_union(entry['geometry'])
 # The 2010 annual map predates the March merger, while the election is in June.
 if year==2010:
  a,b=groups['GM0599'],groups.pop('GM0600');a['geometry']=unary_union([a['geometry'],b['geometry']]);a['population']=(a['population'] or 0)+(b['population'] or 0)
 GEOMETRY[year]=groups
 print(year,'native geometry municipalities',len(groups))

units={};boundaries=[];elections=[];audit={};sources=[];geometry_audit={};municipal_joins={}
def unit_id(year,code):return f'{year}-{code}'
def add_unit(id,name,population=None):
 if id in units:assert units[id]['name']==name,(id,name,units[id]['name'])
 else:units[id]={'id':id,'name':name,'population':population}
def native_boundary(groups,year):
 features={};allg=[g['geometry'] for g in groups.values()];xmin=min(g.bounds[0] for g in allg);ymin=min(g.bounds[1] for g in allg);xmax=max(g.bounds[2] for g in allg);ymax=max(g.bounds[3] for g in allg);scale=760/(ymax-ymin)
 def xy(x,y):return ((x-xmin)*scale+25,(ymax-y)*scale+25)
 for gm,g in groups.items():
  geometry=g['geometry'].simplify(150,preserve_topology=True);polygons=list(geometry.geoms) if geometry.geom_type=='MultiPolygon' else [geometry] if geometry.geom_type=='Polygon' else [v for v in geometry.geoms if v.geom_type=='Polygon'];assert polygons,(year,gm)
  path=''
  for poly in polygons:
   for ring in [poly.exterior,*poly.interiors]:path+='M'+'L'.join(f'{a:.1f},{b:.1f}' for a,b in (xy(x,y) for x,y in ring.coords))+'Z'
  center=max(polygons,key=lambda p:p.area).representative_point();features[unit_id(year,gm)]={'path':path,'center':[round(v,1) for v in xy(center.x,center.y)]}
 boundary={'id':f'nl-native-{year}','label':f'© CBS / Kadaster, {year} municipality boundaries'+('; Rotterdam includes Rozenburg from 18 March' if year==2010 else ''),'width':round((xmax-xmin)*scale+50),'height':810,'features':features}
 return boundary
for year,code in SPECS.items():
 results={};national={};parties=[]
 if year in [2023,2025]:
  groups={m['id']:m for m in ORIGINAL['municipalities']};features={unit_id(year,k):{'path':g['path'],'center':g['center']} for k,g in groups.items()}
  for k,g in groups.items():uid=unit_id(year,k);add_unit(uid,g['name'],g['population']);results[uid]=g['results'][str(year)]
  for u in ORIGINAL['outsideMap']:
   uid='outside-'+slug(u['name']);add_unit(uid,u['name']);results[uid]=u['results'][str(year)]
  national=ORIGINAL['national'][str(year)]
  parties=[{k:p[k] for k in ['id','name','color','classification']} for p in ORIGINAL['parties'] if p['id'] in national['votes']]
  boundary={'id':f'nl-native-{year}','label':'CBS / PDOK 2025 land boundaries; unchanged municipal membership in this electoral cycle','width':ORIGINAL['width'],'height':ORIGINAL['height'],'features':features}
  if year==2023:
   assert set(groups)==set(GEOMETRY[year]);boundary=native_boundary(GEOMETRY[year],year);features=boundary['features']
  geo_source=src('CBS / Kadaster — 2023 native municipal geometry',GEO_URLS[2023]) if year==2023 else ORIGINAL['sources'][2]
 else:
  p=json.loads((CACHE/(code+'.json')).read_text());national_rows=p['Stemregio']['Partij'];national={'valid':integer(p['Stemregio']['AantalGeldigeStemmen']),'votes':{pid(r['Naam'],year):integer(r['AantalStemmen']) for r in national_rows}}
  parties=[metadata(pid(r['Naam'],year),html.unescape(r['Naam'])) for r in national_rows]
  assert len({p['id'] for p in parties})==len(parties)
  groups=GEOMETRY[year];lookup={area_key(g['name'],code=k):k for k,g in groups.items()};assert len(lookup)==len(groups),(year,'duplicate geometry names')
  consumed=set();ops=[o for o in next(r for r in p['Regios']['Regios'] if r['Name']=='Gemeente')['Options'] if o['Value']!='-'];foreign=[]
  for op in ops:
   d=json.loads((CACHE/f'{code}-{op["Id"]}.json').read_text());r=d['Stemregio'];name=html.unescape(r['Naam']);votes={pid(x['Naam'],year):integer(x['AantalStemmen']) for x in r['Partij'] if x['AantalStemmen'] is not None}
   assert sum(votes.values())==integer(r['AantalGeldigeStemmen']),(year,name,'local vote sum')
   assert set(votes)<=set(national['votes']),(year,name,'unknown list',set(votes)-set(national['votes']))
   province=next(x for x in d['Regios']['Regios'] if x['Name']=='Provincie');province_name=next((o['Value'] for o in province['Options'] if o['Id']==province['Selected']),'')
   k=area_key(name,province_name)
   if k in lookup:
    gm=lookup[k];assert gm not in consumed,(year,name,'duplicate geographic join');consumed.add(gm);uid=unit_id(year,gm);g=groups[gm];municipal_joins.setdefault(str(year),{})[gm]={'sourceAreaId':op['Id'],'sourceName':name,'province':province_name};label=name+(' (Limburg)' if gm=='GM0893' else ' (North Holland)' if gm=='GM0373' else '')
    add_unit(uid,label,g['population'])
   else:
    assert name in ['Bonaire','Saba','Sint Eustatius','NBSB','Briefstembureaus','Briefstemmen'],(year,'unmatched area',name,province_name)
    label='Non-resident postal voters (NBSB)' if name=='NBSB' else name;uid='outside-'+slug(label);add_unit(uid,label);foreign.append(label)
   turnout=r['OpkomstPercentage'];results[uid]={'valid':integer(r['AantalGeldigeStemmen']),'turnout':float(turnout.replace('%','').replace(',','.')) if turnout else None,'votes':votes,'source':f'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/{code}/{op["Id"]}'}
  assert consumed==set(groups),(year,'geometry without results',set(groups)-consumed)
  total=collections.Counter()
  for r in results.values():total.update(r['votes'])
  delta={k:n-total.get(k,0) for k,n in national['votes'].items()}
  # Preserve separately reported national votes absent from the municipal index.
  # This is an explicit arithmetic residual, not an invented municipality.
  if year in [2017,2021]:
   known=json.loads((ROOT/f'scripts/netherlands-{year}-reconciliation.json').read_text());expected={pid(k,year):-n for k,n in known['municipalMinusNationalBySourceParty'].items()}
   assert delta==expected,(year,'source discrepancy changed',delta)
   sources.extend(known['sources'])
  elif any(delta.values()):
   assert all(n>=0 for n in delta.values()),(year,'municipal counts exceed certified national counts',delta)
   assert sum(delta.values())<.02*national['valid'],(year,'too much unallocated national data',delta)
   uid='outside-national-residual';add_unit(uid,'National votes outside the municipal index');results[uid]={'valid':sum(delta.values()),'votes':delta,'turnout':None,'source':f'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/{code}'};foreign.append('National votes outside the municipal index')
  boundary=native_boundary(groups,year);features=boundary['features']
  geo_source=src(f'CBS / Kadaster — {year} historical municipal geometry',GEO_URLS[year])
 total=collections.Counter()
 for r in results.values():assert sum(r['votes'].values())==r['valid'];total.update(r['votes'])
 if year not in [2017,2021]:
  assert dict(total)==national['votes'],(year,'national party totals',set(total)-set(national['votes']))
  assert sum(r['valid'] for r in results.values())==national['valid']
 else:assert sum(r['valid'] for r in results.values())==known['municipalValidVotes']
 boundaries.append(boundary);sources+=[src(f'Kiesraad — {year} certified national and municipal result archive',f'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/{code}'),geo_source]
 elections.append({'id':str(year),'label':str(year),'dateLabel':DATE[year],'name':'Tweede Kamer','country':'Netherlands','boundarySetId':boundary['id'],'voteBasis':'Valid candidate votes','parties':parties,'results':results,'nationalRoute':'/world/election/world-netherlands-'+str(year),'populationLabel':'1 January 2025' if year>=2023 else f'1 January {year}','defaultUnitId':unit_id(year,'GM0363')})
 if year in [2017,2021]:
  elections[-1]['coverageNote']=('The 2017 municipal returns total 10,524,838 valid votes, 8,797 above the certified national total of 10,516,041. Official investigations documented aggregation errors, including omitted votes from Boxmeer and Bergeijk. This map retains the published municipal counts; the national election result remains the certified figure. The Hague’s archive return includes non-resident votes and is excluded from municipal shift comparisons.' if year==2017 else 'The 2021 municipal archive totals 10,422,851 valid votes, one fewer than the national summary of 10,422,852. Small party-total discrepancies are retained as published, rather than redistributing votes between municipalities. The Hague’s archive return includes non-resident votes and is excluded from municipal shift comparisons.')
 audit[str(year)]={'municipalities':len(features),'resultAreas':len(results),'validVotes':sum(r['valid'] for r in results.values()),'certifiedNationalValidVotes':national['valid'],'nationalPartyVotes':national['votes'],'municipalPartyVotes':dict(total),'outsideMap':[units[u]['name'] for u in results if u not in features]}
 print(year,len(features),'mapped municipalities;',national['valid'],'valid national votes; local sums audited')

# Track complete territorial origins through the official annual transitions.
# Any split or partial border correction makes the affected comparison unavailable.
def gm(value):
 m=re.match(r'^(\d{4}) ',value or '');return 'GM'+m[1] if m else None
def mapping(before,after):
 origins={u.split('-',1)[1]:{u} for u in before['results'] if re.fullmatch(r'\d{4}-GM\d{4}',u)}
 # Earlier Hague returns combine municipal and non-resident postal ballots.
 # Do not present that counting-area change as a municipal voter shift.
 if int(before['id'])<2023:origins.pop('GM0518',None)
 for y in range(int(before['id'])+1,int(after['id'])+1):
  rows=TRANSITIONS[str(y)]['rows'];destinations=collections.defaultdict(set);blocked=set();mergers=collections.defaultdict(set)
  for row in rows:
   a=gm(row['fromAbolished']);b=gm(row['toExisting']) or gm(row['toNew']);old=gm(row['fromExisting'])
   if a and b:destinations[a].add(b);mergers[b].add(a)
   else:blocked.update(c for c in [a,b,old] if c)
  for old,dests in destinations.items():
   if len(dests)>1:blocked.add(old);blocked.update(dests)
  prior={k:set(v) for k,v in origins.items()}
  for target,parts in mergers.items():
   if target in blocked or parts&blocked or any(p not in prior for p in parts):blocked.add(target);continue
   combined=set().union(*(prior[p] for p in parts))
   if target in prior and target not in parts:combined.update(prior[target])
   for old in parts:origins.pop(old,None)
   origins[target]=combined
  for code in blocked:origins.pop(code,None)
 # A partial transfer can block a destination already used by a later merger;
 # unavailable origins stay unavailable for every subsequent year.
 return {u:sorted(origins[u.split('-',1)[1]]) for u in after['results'] if re.fullmatch(r'\d{4}-GM\d{4}',u) and u.split('-',1)[1] in origins}
for after in elections:
 previous=[e for e in elections if 2017<=int(e['id'])<int(after['id'])]
 if not previous:continue
 after['comparisons']=[]
 for before in reversed(previous):
  links=mapping(before,after);years=range(int(before['id'])+1,int(after['id'])+1)
  source_links=[src(f'CBS — municipal boundary changes {y}',TRANSITIONS[str(y)]['source']) for y in years if TRANSITIONS[str(y)]['rows']]
  after['comparisons'].append({'electionId':before['id'],'unitMap':links,'note':f'Compared on {after["id"]} municipal boundaries. Earlier votes are summed only for complete municipality mergers documented by CBS. Split municipalities and any partial border corrections are excluded; their comparison is unavailable. Merged turnout percentages are not averaged. Comparisons using 2017 or 2021 also exclude The Hague because the archive groups non-resident votes with that municipality.','sources':source_links or [src('CBS — annual municipality boundary changes','https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/regionale-statistieken/gebiedswijzigingen-gemeenten')]})
  audit[after['id']].setdefault('comparisons',{})[before['id']]=len(links)

data={'version':1,'id':'netherlands-tweede-kamer-history','title':'Netherlands Tweede Kamer municipal election results 2003–2025','unitLabel':'municipality','unitPlural':'municipalities','defaultElectionId':'2025','defaultUnitId':'2025-GM0363','description':'Explore eight Dutch national parliamentary elections on their contemporary municipal boundaries. Select an election for local results, winning parties and winning margins. Comparisons from 2017 onward use documented municipality histories.','coverageNote':'All participating lists and votes in the cited municipal returns are retained. Each election uses valid candidate votes, excluding blank and invalid ballots. This is a municipal breakdown of Tweede Kamer elections, not municipal council elections. Earlier elections before 2003 are outside this map series.','outsideMapNote':'Caribbean public bodies and separately identified postal voting are outside the European Netherlands map. Some archived municipal indexes omit a small portion of national votes; those votes appear as an explicitly labelled national residual. Non-resident votes follow the grouping in the source, which can differ by election.','classificationNote':'Our editorial left/right/centre groupings follow a broad international spectrum. D66 and Volt are centre. Separate parties and joint electoral lists remain distinct; a vote-share change does not imply individual voter switching.','turnoutNote':'Official local turnout can exceed 100% when voter-pass holders cast their ballot outside their home municipality. These published percentages are preserved.','units':list(units.values()),'boundaries':boundaries,'elections':elections,'notes':['Municipal geometry is attributed to © CBS / Kadaster and simplified for display. Historical generalized boundary files may include water areas. The 2006 geometry credit is © 2007 Centraal Bureau voor de Statistiek / Topografische Dienst Kadaster, Emmen, 2006.','Population circles use the published CBS annual figures where available. Some archived counts are rounded; circle sizing is unavailable where population was not supplied. The 2023 and 2025 views share the 1 January 2025 population reference.','Rotterdam’s 2010 map combines its January boundary with Rozenburg, which joined Rotterdam on 18 March 2010, before the June election. Their January population figures are also combined.','Each municipal party-vote total is reconciled to valid local votes. National reconciliation is checked for every party. The source discrepancies in 2017 and 2021 are documented on those election views; published counts are preserved without redistributing the differences.','Comparison coverage is checked through the official CBS annual transition tables. Before 2017, those crosswalks have not been added: the older maps provide standalone results without inferred shifts.'],'comparisonNotes':['Vote-share changes are percentage-point differences using each election’s positive-vote denominator. Left/right arrows compare the change in left share minus right share; centre and unclassified votes remain in the denominator.','A missing comparison is unavailable, not zero. Unclassified or historically distinct lists are not silently merged into later parties.'], 'sources':sources+[src('CBS — Rozenburg merged into Rotterdam, 18 March 2010','https://www.cbs.nl/nl-nl/cijfers/detail/37259ned')],'checked':'2026-10-14'}
path=ROOT/'public/nl-municipal-history.json';path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
manifest={'checked':data['checked'],'elections':audit,'sources':sources,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometrySources':GEO_URLS,'municipalJoins':municipal_joins}
(ROOT/'scripts/netherlands-municipal-history-sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Wrote',path.stat().st_size,'bytes;',len(elections),'elections')
