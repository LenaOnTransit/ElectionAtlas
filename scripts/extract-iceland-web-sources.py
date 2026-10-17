"""Normalize retrieved historical tables; preserve archived retrieval text separately."""
from pathlib import Path
import json,re,hashlib
P=Path(__file__).parent/'iceland-election-import';src=json.loads((P/'web-sources.json').read_text());out=[]
def clean(s):
 s=re.sub(r'【\d+†([^】]+)】',lambda m:m[1].split('†')[0],s);s=re.sub(r'\^?\{?\[\s*[a-z0-9]+\s*\]\}?','',s);return s.strip()
for name,r in src.items():
 raw='\n'.join(x['text'] for x in r['content'] if x['type']=='text');lines=[clean(m[1]) for l in raw.splitlines() if (m:=re.match(r'L\d+: (.*)',l))];tables=[];cur=[]
 for l in lines+['']:
  if '|' in l and not l.startswith(('Source:','This article')):
   row=[clean(x) for x in l.split('|')]
   if all(not c or re.fullmatch(r'[-: ]+',c) for c in row):continue
   cur.append(row)
  elif cur:
   if len(cur)>1:tables.append(cur)
   cur=[]
 out.append(dict(name=name,url='https://en.wikipedia.org/wiki/'+name,sha256=hashlib.sha256(raw.encode()).hexdigest(),prose='\n'.join(lines),tables=tables))
(P/'web-extract.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for x in out:
 if 'parliamentary' in x['name']:
  print(x['name'],[(t[:2],len(t)) for t in x['tables'] if any('Votes'in h for h in t[:4])])
