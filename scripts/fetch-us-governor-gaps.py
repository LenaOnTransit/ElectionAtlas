"""Find individual state result pages where national summaries are unavailable."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,urllib.parse
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/us-midterms'
ADMITTED={'AL':1819,'AK':1959,'AZ':1912,'AR':1836,'CA':1850,'CO':1876,'CT':1788,'DE':1787,'FL':1845,'GA':1788,'HI':1959,'ID':1890,'IL':1818,'IN':1816,'IA':1846,'KS':1861,'KY':1792,'LA':1812,'ME':1820,'MD':1788,'MA':1788,'MI':1837,'MN':1858,'MS':1817,'MO':1821,'MT':1889,'NE':1867,'NV':1864,'NH':1788,'NJ':1787,'NM':1912,'NY':1788,'NC':1789,'ND':1889,'OH':1803,'OK':1907,'OR':1859,'PA':1787,'RI':1790,'SC':1788,'SD':1889,'TN':1796,'TX':1845,'UT':1896,'VT':1791,'VA':1788,'WA':1889,'WV':1863,'WI':1848,'WY':1890}
states=json.loads((ROOT/'lib/us-states-map.json').read_text())
years=[y for y in range(1790,2023,4) if not (CACHE/f'wiki-governor-{y}.html').exists() or y==1862]
def fetch(item):
 y,s=item;name=f"governor-{y}-{s['code']}";p=CACHE/(name+'.html');url='https://en.wikipedia.org/wiki/'+urllib.parse.quote(f"{y}_{s['name'].replace(' ','_')}_gubernatorial_election")
 if p.exists():return {'year':y,'state':s['code'],'url':url,'file':name,'bytes':p.stat().st_size}
 r=subprocess.run(['curl','--max-time','18','-L','--fail','-s',url,'-o',str(p)],capture_output=True)
 return {'year':y,'state':s['code'],'url':url,'file':name,**({'error':r.returncode}if r.returncode else {'bytes':p.stat().st_size})}
out=[]
with ThreadPoolExecutor(max_workers=8) as pool:
 futures=[pool.submit(fetch,(y,s))for y in years for s in states if ADMITTED[s['code']]<=y]
 for f in as_completed(futures):
  r=f.result();out.append(r)
  if 'bytes'in r:print(r['file'],r['bytes'],flush=True)
(CACHE/'governor-gap-pages.json').write_text(json.dumps(out,indent=2)+'\n')
