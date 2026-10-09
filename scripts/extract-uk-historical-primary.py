"""Extract Commons Library spreadsheet controls; read-only source processing."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'.cache/uk-history';OUT=ROOT/'scripts/uk-historical-election-import';NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sheets(p):
 z=zipfile.ZipFile(p);strings=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)] if 'xl/sharedStrings.xml' in z.namelist() else []
 names=[s.attrib['name'] for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS)];out={}
 for i,name in enumerate(names,1):
  rows=[]
  for r in ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')).findall('m:sheetData/m:row',NS):
   cells={}
   for c in r.findall('m:c',NS):
    v=c.find('m:v',NS);text=v.text if v is not None else ''.join(c.itertext())
    if c.attrib.get('t')=='s':text=strings[int(text)]
    cells[re.sub(r'\d+','',c.attrib['r'])]=text
   rows.append(cells)
  out[name]=rows
 return out
def count(v):
 if v in ['',None]:return 0
 n=float(v);assert abs(n-round(n))<0.0001,v;return int(round(n))
seat=sheets(CACHE/'official-seats-xlsx.xlsx');stats=sheets(CACHE/'official-statistics-xlsx.xlsx')
capacities={}
for r in seat['Table 1']:
 if re.fullmatch(r'\d{4}',r.get('A','')) and r.get('F'):capacities[r['A']]=count(r['F'])
national={};countries={};ni={};turnout={}
for r in stats['3. GE results UK & GB']:
 if not re.fullmatch(r'\d{4}[FO]?',r.get('A','')):continue
 election=r['A'];country=r['B'];row=dict(code=r['C'],votes=count(r.get('D')),seats=count(r.get('I')),sourceShare=float(r.get('F') or 0),totalVotes=count(r['E']),totalSeats=count(r['J']))
 countries.setdefault(election,{}).setdefault(country,[]).append(row)
 if country=='UK':national.setdefault(election,[]).append(row)
for r in stats['4. GE results NI']:
 if re.fullmatch(r'\d{4}[FO]?',r.get('A','')):ni.setdefault(r['A'],[]).append(dict(code=r['B'],votes=count(r.get('C')),seats=count(r.get('H'))))
for r in stats['5. Turnout']:
 if re.fullmatch(r'\d{4}[FO]?',r.get('A','')):turnout[r['A']]=round(float(r['F'])*100,4)
notes=[r.get('A','') for r in stats['Notes and sources'] if r.get('A')]
for year,rows in national.items():
 assert sum(r['seats'] for r in rows)==rows[0]['totalSeats'],year
 assert sum(r['votes'] for r in rows)==rows[0]['totalVotes'],year
out=dict(checked='2026-10-09',seatSource='https://researchbriefings.files.parliament.uk/documents/SN02384/SN02384.xlsx',resultSource='https://researchbriefings.files.parliament.uk/documents/CBP-7529/general-elections-and-governments.xlsx',seatSha256=hashlib.sha256((CACHE/'official-seats-xlsx.xlsx').read_bytes()).hexdigest(),resultSha256=hashlib.sha256((CACHE/'official-statistics-xlsx.xlsx').read_bytes()).hexdigest(),capacities=capacities,national=national,countries=countries,northernIreland=ni,turnout=turnout,sourceNotes=notes)
(OUT/'primary-extract.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Primary seat capacities:',len(capacities),'national results:',len(national))
