"""Verify every modern national row against the raw Statistics Norway JSON-stat snapshots."""
from pathlib import Path
import json,hashlib
P=Path('scripts/norway-election-import');records=json.loads((P/'records.json').read_text());audit=json.loads((P/'reconciliation.json').read_text())
def get(d,**kw):
 i=0
 for k,size in zip(d['id'],d['size']):i=i*size+d['dimension'][k]['category']['index'][kw.get(k,next(iter(d['dimension'][k]['category']['index'])))]
 return d['value'][i] if isinstance(d['value'],list) else d['value'].get(str(i))
v=json.loads((P/'ssb-08092.json').read_text());s=json.loads((P/'ssb-08219.json').read_text());t=json.loads((P/'ssb-08243.json').read_text());checks=[]
for a in audit:
 if not a.get('primaryRows'):continue
 e=next(e for e in records if e['id']==a['id']);y=e['startDate'][:4];assert e['turnout']==get(t,Tid=y);total=0;seats=0
 for r in a['primaryRows']:
  p=r['partyCode'];vote=get(v,PolitParti=p,ContentsCode='Godkjente1',Tid=y);sx=[get(s,PolitParti=p,Kjonn=k,Tid=y) for k in ['1','2']];seat=None if all(x is None for x in sx) else sum(x or 0 for x in sx);actual=next(x for x in e['results'] if x['name']==r['name']);assert actual['votes']==vote;assert actual['seats']==seat;assert actual['share']==round(vote/a['recordedVotes']*100,2);total+=vote or 0;seats+=seat or 0;checks.append(dict(id=e['id'],partyCode=p,name=r['name'],votes=vote,seats=seat))
 assert total==a['recordedVotes'] and seats==e['totalSeats'];assert len(e['results'])==len(a['primaryRows'])
out=dict(elections=len({r['id'] for r in checks}),partyRows=len(checks),checks=checks,sources=[dict(table=n,sha256=hashlib.sha256((P/('ssb-'+n+'.json')).read_bytes()).hexdigest(),updated=json.loads((P/('ssb-'+n+'.json')).read_text())['updated']) for n in ['08092','08219','08243']]);(P/'primary-reconciliation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(out['elections'],'official national elections;',out['partyRows'],'party/list rows verified')
