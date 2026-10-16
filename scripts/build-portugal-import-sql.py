"""Generate an atomic, additive import guarded against concurrent content edits."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent/'portugal-election-import';records=json.loads((P/'records.json').read_text());parties=json.loads((P/'parties.json').read_text());base=json.loads((P/'pre-import-backup.json').read_text());old=next(x for x in base if x['kind']=='world_election');country=next(x for x in base if x['kind']=='world_country')
coverage='National legislative and presidential elections from 1820 to 2026, including constituent elections, historical Senate ballots and indirect presidential rounds. Modern ballot-list tables retain separate coalition and independent-party returns. Some early elections have no surviving numeric breakdown in the cited sources, and some historical tables exclude overseas seats. Electoral franchises, chamber boundaries and competition changed substantially over this period. Partial coverage is labelled.'
(P/'coverage.txt').write_text(coverage+'\n')
def lit(s):return "'"+s.replace("'","''")+"'"
def val(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
sql='begin;\ndo $import$ declare e jsonb; p jsonb; existing jsonb; begin\n'
sql+=f"if not exists(select 1 from public.ea_records where id={lit(country['id'])} and data->>'coverageNote' in ({lit(country['data']['coverageNote'])},{lit(coverage)})) then raise exception 'Portugal coverage changed'; end if;\n"
sql+=f'for p in select value from jsonb_array_elements({val(parties)}) loop\n'
sql+="select to_jsonb(t)-'updated_at'-'created_at' into existing from public.ea_country_parties t where id=(p->>'id')::uuid; if existing is not null and existing<>p then raise exception 'Party differs %',p->>'id'; end if;\ninsert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values((p->>'id')::uuid,p->>'country_id',p->>'name',p->>'short_name',p->>'color',array(select jsonb_array_elements_text(p->'ideology_ids')),p->>'notes',(p->>'archived')::boolean) on conflict(id) do nothing; end loop;\n"
sql+=f'for e in select value from jsonb_array_elements({val(records)}) loop\n'
sql+="select data into existing from public.ea_records where id=e->>'id' for update;\n"
sql+=f"if existing is not null and existing<>e and not (e->>'id'={lit(old['id'])} and existing={val(old['data'])}) then raise exception 'Election differs %',e->>'id'; end if;\n"
sql+="insert into public.ea_records(id,kind,data,updated) values(e->>'id','world_election',e,now()) on conflict(id) do update set data=excluded.data,updated=now(); end loop;\n"
sql+=f"update public.ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(coverage)}::text)),updated=now() where id={lit(country['id'])};\nend $import$;\ncommit;\n"
(P/'import.sql').write_text(sql);print(len(records),'records;',len(parties),'parties;',len(sql),'SQL characters')
