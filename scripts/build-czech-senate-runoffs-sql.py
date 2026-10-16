from pathlib import Path
import json
P=Path('scripts/czech-senate-2026-runoffs');records=json.loads((P/'records.json').read_text());base=json.loads((P/'pre-import-backup.json').read_text());prior=next(r['data'] for r in base if r['id']=='world-calendar-cz-senate-2026-runoff')
def val(v):return "'"+json.dumps(v,ensure_ascii=False,separators=(',',':')).replace("'","''")+"'::jsonb"
s='begin;\ndo $import$ declare e jsonb; existing jsonb; begin\n'
s+=f'for e in select value from jsonb_array_elements({val(records)}) loop\n'
s+="select data into existing from public.ea_records where id=e->>'id' for update;\n"
s+=f"if existing is not null and existing<>e and not(e->>'id'='world-calendar-cz-senate-2026-runoff' and existing={val(prior)}) then raise exception 'Czech runoff record changed %',e->>'id'; end if;\n"
s+="insert into public.ea_records(id,kind,data,updated) values(e->>'id','world_election',e,now()) on conflict(id) do update set data=excluded.data,updated=now(); end loop;\nend $import$;\ncommit;\n"
(P/'import.sql').write_text(s);print(len(s),'SQL characters')
