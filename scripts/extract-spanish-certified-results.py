import re,json,hashlib
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('.cache/spain');pages=(ROOT/'official-2023-final.txt').read_text().split('\f');candidates=[]
for page,p in enumerate(pages,1):
 if page<38:continue
 lines=p.splitlines()
 for i,l in enumerate(lines):
  if not re.match(r'\s*Do(?:n|ña)\s',l):continue
  parts=re.split(r'\s{2,}',l.strip());assert len(parts)==3,(page,parts)
  name,party,v=parts;pos=l.index(party);vp=l.rindex(v)
  for nxt in lines[i+1:i+4]:
   if not nxt.strip():continue
   spaces=len(nxt)-len(nxt.lstrip());value=nxt.strip()
   if spaces>=pos-2 and spaces<vp-10 and value.upper()==value and not any(c.isdigit() for c in value):party+=' '+value
   else:break
  votes=int(v.replace('.',''))
  correction=name=='Don Santiago Llorente Gutiérrez'
  if correction:assert v=='1.007.32';votes=1007322
  candidates.append(dict(page=page,name=name,party=party,votes=votes,elected=page<47,correction=correction))
assert len(candidates)==1152 and sum(c['elected'] for c in candidates)==208
from collections import Counter
print('total candidate votes',sum(c['votes'] for c in candidates));print(Counter(c['party'] for c in candidates))
s=BeautifulSoup((ROOT/'official-2023-final.html').read_text(),'html.parser');partyrows=[]
for i,t in enumerate(s.select('table')):
 rows=[[c.get_text(' ',strip=True) for c in r.find_all(['td','th'])] for r in t.select('tr')];head=rows[0];total=rows[-1]
 assert total[0]=='Total estatal.'
 parties=head[2:] if i<3 else head[1:];nums=total[2:] if i<3 else total[1:]
 for j,n in enumerate(parties):
  v=int(nums[j*2 if i<3 else j].strip('.').replace('.',''));seat=int(nums[j*2+1]) if i<3 else 0
  partyrows.append(dict(name=re.sub(r'\s+',' ',n),votes=v,seats=seat))
assert sum(r['votes'] for r in partyrows)==24487414;assert sum(r['seats'] for r in partyrows)==350
out=dict(source='https://www.boe.es/boe/dias/2023/09/01/pdfs/BOE-A-2023-18907.pdf',sha256=hashlib.sha256((ROOT/'official-2023-final.pdf').read_bytes()).hexdigest(),correctionSource='https://www.boe.es/buscar/doc.php?id=BOE-A-2023-19537',congress=dict(registered=37469458,ballots=24952447,validBallots=24688087,blankBallots=200673,invalidBallots=264360,rows=partyrows),senate=dict(candidateVotes=sum(c['votes'] for c in candidates),electedSeats=208,candidates=candidates))
Path('scripts/spanish-election-import/certified-extract.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
# 2024 JEC HTML tables, followed by the officially corrected two party totals.
s=BeautifulSoup((ROOT/'official-european-2024-certified.html').read_text(),'html.parser');rows24=[]
for i,t in enumerate(s.select('table')[1:],1):
 rows=[[c.get_text(' ',strip=True) for c in r.find_all(['td','th'])] for r in t.select('tr')];head=rows[0];total=rows[-1];assert total[0]=='Total estatal.'
 names=head[2:] if i<=2 else head[1:];nums=total[2:] if i<=2 else total[1:]
 for j,n in enumerate(names):rows24.append(dict(name=n,votes=int(nums[j*2 if i<=2 else j].replace('.','')),seats=int(nums[j*2+1]) if i<=2 else 0))
for r in rows24:
 if r['name']=='Partido Socialista Obrero Español':assert r['votes']==5290945;r['votes']=5291102
 if r['name']=='Junts i Lliures per Europa':assert r['votes']==442297;r['votes']=442140
assert sum(r['votes'] for r in rows24)==17402783;assert sum(r['seats'] for r in rows24)==61
out24=dict(source='https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-13092',correctionSource='https://www.boe.es/buscar/doc.php?id=BOE-A-2024-15344',registered=38050286,ballots=17652007,validBallots=17527438,blankBallots=124655,invalidBallots=124569,rows=rows24)
Path('scripts/spanish-election-import/certified-european-2024.json').write_text(json.dumps(out24,ensure_ascii=False,indent=2)+'\n')
