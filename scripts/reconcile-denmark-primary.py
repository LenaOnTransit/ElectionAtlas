"""Reconcile mainland seats against Statistics Denmark table 43, plus certified 2022 votes."""
from pathlib import Path
import json,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'scripts/denmark-election-import';CACHE=ROOT/'.cache/denmark'
records=json.loads((OUT/'records.json').read_text());text=(CACHE/'dst-2019.txt').read_text();part=text.split('Tabel 43                                 Mandatfordelingen')[1].split('Tillægsmandater i alt')[0];years=[1971,1973,1975,1977,1979,1981,1984,1987,1988,1990,1994,1998,2001,2005,2007,2011,2015,2019]
names={'A. Socialdemokratiet':'Social Democrats','B. Radikale Venstre':'Social Liberals','C. Det Konservative Folkeparti':"Conservative People's Party",'D. Centrum-Demokraterne':'Centre Democrats','D. Nye Borgerlige':'New Right','E. Danmarks Retsforbund':'Justice Party','F. SF - Socialistisk Folkeparti':"Socialist People's Party",'I. Liberal Alliance':'Liberal Alliance','K. Danmarks Kommunistiske Parti':'Communist Party of Denmark','K. Kristendemokraterne':'Christian Democrats','O. Dansk Folkeparti':"Danish People's Party",'P. Fælles Kurs':'Common Course','V. Venstre, Danmarks Liberale Parti':'Venstre','Y. Venstresocialisterne':'Left Socialists','Z. Fremskridtspartiet':'Progress Party','Ø. Enhedslisten - De Rød-Grønne':'Red–Green Alliance','Å. Alternativet':'The Alternative','Uden for partierne':'Independents'}
checks=[]
for line in part.splitlines():
 cells=re.split(r'\s{2,}',line.strip())
 if cells[0] not in names:continue
 vals=cells[1:] if len(cells)==19 else re.findall(r'\d+|-',line[len(cells[0]):])
 # Columns are separated by variable single/multiple spaces.
 vals=re.findall(r'\d+|-',line[line.index(cells[0])+len(cells[0]):]);assert len(vals)==18,(cells[0],vals)
 for year,value in zip(years,vals):
  e=next(e for e in records if e['body']=='Folketing' and e['startDate'].startswith(str(year)));name=names[cells[0]];r=next((r for r in e['results'] if r['name']==name or (year==2007 and name=='Liberal Alliance' and r['name']=='New Alliance')),None);expected=0 if value=='-' else int(value);actual=r['seats'] if r else 0
  assert actual==expected,(year,name,actual,expected)
  checks.append(dict(year=year,party=name,seats=expected))
s=BeautifulSoup((CACHE/'dst-2022.html').read_bytes(),'html.parser');txt=s.get_text(' ',strip=True)
map2022={'A. Socialdemokratiet':'Social Democrats','B. Radikale Venstre':'Social Liberals','C. Det Konservative Folkeparti':"Conservative People's Party",'D. Nye Borgerlige':'New Right','F. SF - Socialistisk Folkeparti':"Socialist People's Party",'I. Liberal Alliance':'Liberal Alliance','K. KD - Kristendemokraterne':'Christian Democrats','M. Moderaterne':'Moderates','O. Dansk Folkeparti':"Danish People's Party",'Q. Frie Grønne, Danmarks Nye Venstrefløjsparti':'Independent Greens','V. Venstre, Danmarks Liberale Parti':'Venstre','Æ. Danmarksdemokraterne - Inger Støjberg':'Denmark Democrats','Ø. Enhedslisten - De Rød-Grønne':'Red–Green Alliance','Å. Alternativet':'The Alternative','Uden for partierne':'Independents'}
e=next(e for e in records if e['startDate']=='2022-11-01')
for label,name in map2022.items():
 m=re.search(re.escape(label)+r' ([\d.]+)',txt);assert m,label;v=int(m[1].replace('.',''));r=next(r for r in e['results'] if r['name']==name);assert r['votes']==v,(name,r['votes'],v);checks.append(dict(year=2022,party=name,votes=v))
(OUT/'primary-reconciliation.json').write_text(json.dumps(dict(sources=['https://www.dst.dk/pubfile/34694/ftvalg2019','https://www.dst.dk/valg/Valg1968094/valgopg/valgopgHL.htm'],checks=checks),ensure_ascii=False,indent=2)+'\n')
print(len(checks),'primary-source checks passed')
