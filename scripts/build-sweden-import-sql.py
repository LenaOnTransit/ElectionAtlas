"""Atomic Sweden DML: guard existing records, preserve country assessment and 2026 identity."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent/'sweden-election-import';records=json.loads((P/'records.json').read_text());parties=json.loads((P/'parties.json').read_text());base=json.loads((P/'pre-import-backup.json').read_text());country=next(x for x in base if x['kind']=='world_country');old=next(x for x in base if x['kind']=='world_election')
coverage='Lower-house elections from 1866 through 2026, covering Andra kammaren and the unicameral Riksdag, plus First Chamber elections and rotating renewals from 1887 through 1969. Early First Chamber elections before 1887 are not yet included. Results distinguish indirect electoral-college ballots, popular votes, shared lists and historical party groups. Unknown figures remain unreported; date precision and source-classification differences are identified.'
(P/'coverage.txt').write_text(coverage+'\n')
def lit(s):return "'"+s.replace("'","''")+"'"
def val(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
sql='begin;\ndo $import$ declare e jsonb; p jsonb; existing jsonb; begin\n'
sql+=f"if not exists(select 1 from public.ea_records where id={lit(country['id'])} and data->>'coverageNote' in ({lit(country['data']['coverageNote'])},{lit(coverage)})) then raise exception 'Sweden coverage changed'; end if;\n"
sql+=f'for p in select value from jsonb_array_elements({val(parties)}) loop\n'
sql+="select to_jsonb(t)-'updated_at'-'created_at' into existing from public.ea_country_parties t where id=(p->>'id')::uuid; if existing is not null and existing<>p then raise exception 'Party differs %',p->>'id'; end if;\ninsert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values((p->>'id')::uuid,p->>'country_id',p->>'name',p->>'short_name',p->>'color',array(select jsonb_array_elements_text(p->'ideology_ids')),p->>'notes',(p->>'archived')::boolean) on conflict(id) do nothing; end loop;\n"
sql+=f'for e in select value from jsonb_array_elements({val(records)}) loop\n'
sql+="select data into existing from public.ea_records where id=e->>'id' for update;\n"
sql+=f"if existing is not null and existing<>e and not(e->>'id'={lit(old['id'])} and existing={val(old['data'])}) then raise exception 'Election differs %',e->>'id'; end if;\n"
sql+="insert into public.ea_records(id,kind,data,updated) values(e->>'id','world_election',e,now()) on conflict(id) do update set data=excluded.data,updated=now(); end loop;\n"
sql+=f"update public.ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(coverage)}::text)),updated=now() where id={lit(country['id'])};\nend $import$;\ncommit;\n"
(P/'import.sql').write_text(sql);print(len(records),'records;',len(parties),'parties;',len(sql),'SQL characters')
