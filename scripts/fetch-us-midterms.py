"""Cache public historical source pages. Does not write to the database."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,urllib.parse

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/us-midterms';CACHE.mkdir(parents=True,exist_ok=True)
def fetch(item):
 name,url=item;p=CACHE/(name+'.html')
 if not p.exists() or p.stat().st_size<1000:
  result=subprocess.run(['curl','--retry','2','--max-time','45','-L','--fail','-s',url,'-o',str(p)],capture_output=True)
  if result.returncode:return {'file':name,'url':url,'error':result.returncode}
 return {'file':name,'url':url,'bytes':p.stat().st_size}
items=[]
for y in range(1788,2025,2):
 for office in ['senate','governor']:
  title=(f'{y}–{str(y+1)[-2:]}_United_States_Senate_elections' if y<1914 else f'{y}_United_States_Senate_elections') if office=='senate' else f'{y}_United_States_gubernatorial_elections'
  items.append((f'wiki-{office}-{y}','https://en.wikipedia.org/wiki/'+urllib.parse.quote(title)))
results=[]
with ThreadPoolExecutor(max_workers=6) as pool:
 for future in as_completed([pool.submit(fetch,item)for item in items]):
  r=future.result();results.append(r);print(r['file'],r.get('bytes',r.get('error')),flush=True)
(CACHE/'source-pages.json').write_text(json.dumps(sorted(results,key=lambda r:r['file']),indent=2)+'\n')
