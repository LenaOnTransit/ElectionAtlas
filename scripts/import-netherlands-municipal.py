#!/usr/bin/env python3
"""Rebuild official Netherlands municipal comparison data.
Run from any directory: python scripts/import-netherlands-municipal.py
Uses only Python's standard library and curl. Download snapshots are cached
under .cache/netherlands-municipal; public data and the audit manifest are
written into this repository. Every local and national vote sum is verified.
"""
import os,pathlib,json,subprocess,re,html
REPO=pathlib.Path(__file__).resolve().parents[1]
CACHE=REPO/'.cache/netherlands-municipal';CACHE.mkdir(parents=True,exist_ok=True)
os.chdir(CACHE)
def download(url,destination):
 if destination.exists():return
 temporary=destination.with_suffix('.download')
 subprocess.run(['curl','-fsSL','--max-time','300',url,'-o',str(temporary)],check=True)
 temporary.replace(destination)
for year,code in [(2023,'TK20231122'),(2025,'TK20251029')]:
 destination=pathlib.Path(f'nl-tk-{year}.json')
 if not destination.exists():
  snapshot=pathlib.Path(f'nl-tk-{year}.html');download('https://www.verkiezingsuitslagen.nl/verkiezingen/detail/'+code,snapshot)
  data=json.loads(html.unescape(re.findall(r'<textarea[^>]*>(.*?)</textarea>',snapshot.read_text(),re.S)[0]));destination.write_text(json.dumps(data,ensure_ascii=False))
download('https://api.pdok.nl/cbs/wijken-en-buurten-2025/ogc/v1/collections/gemeenten/items?limit=1000&f=json',pathlib.Path('nl-municipal-geometry.json'))
pathlib.Path('nl-municipal-colors.json').write_text((REPO/'scripts/netherlands-municipal-party-colors.json').read_text())

# Collect certified voting-area snapshots.
import pathlib,json,re,html,subprocess,concurrent.futures,time
root=pathlib.Path('nl-municipal-research');root.mkdir(exist_ok=True)
tasks=[]
for y in [2023,2025]:
 p=json.load(open(f'nl-tk-{y}.json'));code=p['Info']['Code']
 for op in next(x for x in p['Regios']['Regios']if x['Name']=='Gemeente')['Options']:
  if op['Value']!='-':tasks.append((y,code,op))
def fetch(t):
 y,code,op=t;dst=root/f'{y}-{op["Id"]}.json'
 if dst.exists():return
 for attempt in range(3):
  r=subprocess.run(['curl','-fsSL','--max-time','35','https://www.verkiezingsuitslagen.nl/verkiezingen/detail/'+code+'/'+str(op['Id'])],capture_output=True,text=True)
  m=re.findall(r'<textarea[^>]*>(.*?)</textarea>',r.stdout,re.S)
  if r.returncode==0 and m:
   p=json.loads(html.unescape(m[0]));dst.write_text(json.dumps(p,ensure_ascii=False));return
 raise RuntimeError(str(t)+' '+r.stderr)
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as ex:
 for i,_ in enumerate(ex.map(fetch,tasks)):
  if i%50==0:print(i+1,'of',len(tasks),flush=True)
print('Done',len(tasks),flush=True)

# Simplify CBS land geometry and choose interior symbol anchors.
import json,math,pathlib
p=json.load(open('nl-municipal-geometry.json'));features=[f for f in p['features']if f['properties']['water']=='NEE']
assert len(features)==342
# Local equirectangular projection at 52 degrees north, appropriate for this national navigation map.
def project(p):return [p[0]*math.cos(math.radians(52)),p[1]]
pts=[project(pt) for f in features for poly in f['geometry']['coordinates']for ring in poly for pt in ring];xmin=min(p[0]for p in pts);xmax=max(p[0]for p in pts);ymin=min(p[1]for p in pts);ymax=max(p[1]for p in pts);scale=760/(ymax-ymin)
def rdp(p,t=.0012):
 if len(p)<3:return p
 a,b=p[0],p[-1];dx,dy=b[0]-a[0],b[1]-a[1];ds=dx*dx+dy*dy;best=0;i=0
 for j,q in enumerate(p[1:-1],1):
  z=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/ds))if ds else 0;d=(q[0]-a[0]-z*dx)**2+(q[1]-a[1]-z*dy)**2
  if d>best:best=d;i=j
 return rdp(p[:i+1])+rdp(p[i:])[1:]if best>t*t else [a,b]
def svgpt(p):return [(p[0]-xmin)*scale+25,(ymax-p[1])*scale+25]
def area(r):return sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(r,r[1:]))/2
def inside(pt,ring):
 x,y=pt;hit=False
 for a,b in zip(ring,ring[1:]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
out=[]
for f in features:
 polys=[[[project(pt)for pt in ring]for ring in poly]for poly in f['geometry']['coordinates']];largest=max(polys,key=lambda poly:abs(area(poly[0])));ring=largest[0];ar=area(ring)
 cx=sum((a[0]+b[0])*(a[0]*b[1]-b[0]*a[1])for a,b in zip(ring,ring[1:]))/(6*ar);cy=sum((a[1]+b[1])*(a[0]*b[1]-b[0]*a[1])for a,b in zip(ring,ring[1:]))/(6*ar)
 # Concave municipality centroids can fall outside. Pick the nearest interior grid point for the symbol anchor.
 if not inside([cx,cy],ring):
  xs=[q[0]for q in ring];ys=[q[1]for q in ring];candidates=[[min(xs)+(max(xs)-min(xs))*i/25,min(ys)+(max(ys)-min(ys))*j/25]for i in range(1,25)for j in range(1,25)];cx,cy=min((q for q in candidates if inside(q,ring)),key=lambda q:(q[0]-cx)**2+(q[1]-cy)**2)
 path=''
 for poly in polys:
  for r in poly:
   simp=rdp(r);path+='M'+'L'.join(f'{x:.1f},{y:.1f}'for x,y in map(svgpt,simp))+'Z'
 props=f['properties'];out.append({'id':props['gemeentecode'],'name':props['gemeentenaam'],'population':props['aantal_inwoners'],'path':path,'center':[round(v,1)for v in svgpt([cx,cy])]})
pathlib.Path('nl-municipal-map.json').write_text(json.dumps({'width':round((xmax-xmin)*scale+50),'height':810,'municipalities':out},ensure_ascii=False,separators=(',',':')));print(len(out),'map features',pathlib.Path('nl-municipal-map.json').stat().st_size)

# Match areas, preserve every list, and reconcile vote totals.
import pathlib,json,re,unicodedata,collections,hashlib
root=pathlib.Path('nl-municipal-research');geometry=json.load(open('nl-municipal-map.json'));colors=json.load(open('nl-municipal-colors.json'))
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
aliases={'nieuwsociaalcontractnsc':'nsc','nieuwsociaalcontract':'nsc','belangvannederlandbvnl':'bvnl','bvnlgroepvanhaga':'bvnl','nederlandmeteenplan':'nl-plan','nlplan':'nl-plan','pvvpartijvoordevrijheid':'pvv','groenlinkspartijvandearbeidpvda':'gl-pvda','spsocialistischepartij':'sp','partijvoordedieren':'pvdd','forumvoordemocratie':'fvd','staatkundiggereformeerdepartijsgp':'sgp','christenunie':'cu','lplibertairepartij':'lp','piratenpartijdegroenen':'piratenpartij-de-groenen'}
def pid(name):return aliases.get(norm(name),re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower()).strip('-'))
colorlookup={pid(r['name']):r for r in colors}
left={'gl-pvda','sp','pvdd','denk','bij1'};right={'pvv','vvd','nsc','bbb','cda','fvd','sgp','ja21','bvnl','lp'};centre={'cu','50plus','d66','volt'}
parties={}
for y in [2023,2025]:
 p=json.load(open(f'nl-tk-{y}.json'))
 for row in p['Stemregio']['Partij']:
  id=pid(row['Naam']);r=colorlookup.get(id,{});entry=parties.setdefault(id,{'id':id,'name':r.get('short',row['Naam']),'color':r.get('color','#777777'),'classification':'left'if id in left else'right'if id in right else'centre'if id in centre else'unclassified','aliases':[]});entry['aliases'].append(row['Naam'])if row['Naam']not in entry['aliases']else None
# These are different electoral lists; do not silently merge the 2023 Pirate/Green alliance into 2025 Pirates.
assert 'piratenpartij' in parties and 'piratenpartij-de-groenen' in parties
allresults={};national={};notes=[];sourcecounts={}
def integer(v):
 if not isinstance(v,str)or not re.fullmatch(r'[0-9.]+',v):raise ValueError(repr(v))
 return int(v.replace('.',''))
for y in [2023,2025]:
 p=json.load(open(f'nl-tk-{y}.json'));code=p['Info']['Code'];ops=[o for o in next(x for x in p['Regios']['Regios']if x['Name']=='Gemeente')['Options']if o['Value']!='-'];sourcecounts[str(y)]=len(ops)
 national[str(y)]={'valid':integer(p['Stemregio']['AantalGeldigeStemmen']),'votes':{pid(r['Naam']):integer(r['AantalStemmen'])for r in p['Stemregio']['Partij']}}
 assert len(ops)==346
 for op in ops:
  f=root/f'{y}-{op["Id"]}.json'
  if not f.exists():raise RuntimeError('Missing '+str(f))
  d=json.loads(f.read_text());s=d['Stemregio'];name=s['Naam'];votes={pid(r['Naam']):integer(r['AantalStemmen'])for r in s['Partij']if r['AantalStemmen']is not None};valid=integer(s['AantalGeldigeStemmen']);assert sum(votes.values())==valid,(y,name,valid,sum(votes.values()));assert all(id in parties for id in votes)
  turnout=s['OpkomstPercentage'];turnout=float(turnout.replace('%','').replace(',','.'))if turnout else None
  province=next(x for x in d['Regios']['Regios']if x['Name']=='Provincie');provinceName=next(o['Value']for o in province['Options']if o['Id']==province['Selected'])
  suffix={'Beek':'(L.)','Stein':'(L.)','Hengelo':'(O.)','Laren':'(NH.)','Rijswijk':'(ZH.)','Middelburg':'(Z.)'}.get(name,'')
  if name=='Bergen':suffix='(L.)'if provinceName=='Limburg'else'(NH.)'
  if suffix:name+=' '+suffix
  if name=='NBSB':name='Non-resident postal voters (NBSB)'
  key=norm(name);assert str(y)not in allresults.get(key,{}).get('results',{}),('duplicate area',y,name);allresults.setdefault(key,{'name':name,'results':{}})['results'][str(y)]={'valid':valid,'turnout':turnout,'votes':votes,'source':f'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/{code}/{op["Id"]}'}
 sums=collections.Counter()
 for m in allresults.values():
  if str(y)in m['results']:sums.update(m['results'][str(y)]['votes'])
 assert dict(sums)==national[str(y)]['votes'],(y,{k:v-national[str(y)]['votes'].get(k,0)for k,v in sums.items()if v!=national[str(y)]['votes'].get(k,0)})
 print(y,'all 346 source areas reconcile with national totals',sum(sums.values()))
municipalities=[];used=set()
for g in geometry['municipalities']:
 k=norm(g['name']);assert k in allresults,g['name'];r=allresults[k];assert set(r['results'])=={'2023','2025'};assert g['population']>0;municipalities.append({**g,'results':r['results']});used.add(k)
outside=[r for k,r in allresults.items()if k not in used];assert len(outside)==4,[r['name']for r in outside]
municipalities.sort(key=lambda m:m['name'].casefold());parties=sorted(parties.values(),key=lambda p:p['name'].casefold())
notes=['Municipal boundaries are unchanged between these elections: all 342 European Netherlands municipalities are matched by name and province to their 2025 CBS codes. The map uses simplified 2025 land boundaries; inland and offshore water polygons are omitted for readability.','Population is the CBS figure on 1 January 2025, used consistently in both election views. Circle area represents population, not valid votes or eligible voters.','The 346 official voting-area records in each year—including the three Caribbean public bodies and non-resident votes—reconcile exactly with each national party vote total. All participating lists are retained.','Left–right shift compares aggregate vote shares under a fixed international party grouping. It is separate from the private nine-axis ideology scores and cannot establish individual voter movements.']
sources=[{'label':'Kiesraad: national and municipal results, 2023','url':'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/TK20231122'},{'label':'Kiesraad: national and municipal results, 2025','url':'https://www.verkiezingsuitslagen.nl/verkiezingen/detail/TK20251029'},{'label':'CBS / PDOK: 2025 municipality boundaries and population','url':'https://api.pdok.nl/cbs/wijken-en-buurten-2025/ogc/v1/collections/gemeenten'}]
sources.append({'label':'Kiesraad: voter passes allow voting in another municipality','url':'https://www.kiesraad.nl/verkiezingen/tweede-kamer/stemmen/kiezerspas'})
notes.append('Official local turnout can exceed 100% when people use a voter pass to vote outside their home municipality. These published local percentages are preserved.')
result={'width':geometry['width'],'height':geometry['height'],'checked':'2026-10-05','parties':parties,'municipalities':municipalities,'outsideMap':outside,'notes':notes,'sources':sources,'national':national}
path=(REPO/'public/nl-municipal-2023-2025.json');path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
manifest={'checked':result['checked'],'municipalities':342,'sourceAreasPerYear':sourcecounts,'nationalValidVotes':{y:r['valid']for y,r in national.items()},'partyLists':len(parties),'outsideMap':[r['name']for r in outside],'sources':sources,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};(REPO/'scripts/netherlands-municipal-sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Published dataset',path.stat().st_size,'bytes;',len(parties),'distinct lists;',[(m['name'],m['population'])for m in municipalities if m['name']=='Amsterdam']);print('Outside map',[r['name']for r in outside])
