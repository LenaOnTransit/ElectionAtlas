"""Generate an atomic, additive import guarded against concurrent content edits."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent/'finland-election-import';records=json.loads((P/'records.json').read_text());parties=json.loads((P/'parties.json').read_text());base=json.loads((P/'pre-import-backup.json').read_text());country=next(x for x in base if x['kind']=='world_country')
coverage='National Eduskunta elections from 1907 through 2023 and presidential elections from 1919 through 2024, including popular rounds, public elector elections and the final decisive parliamentary or electoral-college ballot. These different ballot types are recorded separately. The 1944 appointment by special law and the 1973 term extension were not contested presidential elections. Finland has a unicameral parliament. Parliamentary turnout from 1908 uses Statistics Finland’s resident-citizen series; it excludes eligible citizens living abroad. Earlier estate-based Diet elections are outside this coverage.'
(P/'coverage.txt').write_text(coverage+'\n')
def lit(s):return "'"+s.replace("'","''")+"'"
def val(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
sql='begin;\ndo $import$ declare e jsonb; p jsonb; existing jsonb; begin\n'
sql+=f"if not exists(select 1 from public.ea_records where id={lit(country['id'])} and data->>'coverageNote' in ({lit(country['data']['coverageNote'])},{lit(coverage)})) then raise exception 'Finland coverage changed'; end if;\n"
sql+=f'for p in select value from jsonb_array_elements({val(parties)}) loop\n'
sql+="select to_jsonb(t)-'updated_at'-'created_at' into existing from public.ea_country_parties t where id=(p->>'id')::uuid; if existing is not null and existing<>p then raise exception 'Party differs %',p->>'id'; end if;\ninsert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values((p->>'id')::uuid,p->>'country_id',p->>'name',p->>'short_name',p->>'color',array(select jsonb_array_elements_text(p->'ideology_ids')),p->>'notes',(p->>'archived')::boolean) on conflict(id) do nothing; end loop;\n"
sql+=f'for e in select value from jsonb_array_elements({val(records)}) loop\n'
sql+="select data into existing from public.ea_records where id=e->>'id' for update;\n"
sql+="if existing is not null and existing<>e then raise exception 'Election differs %',e->>'id'; end if;\n"
sql+="insert into public.ea_records(id,kind,data,updated) values(e->>'id','world_election',e,now()) on conflict(id) do update set data=excluded.data,updated=now(); end loop;\n"
scheduled=next(x for x in base if x['id']=='world-finland-2027');updated=dict(scheduled['data'],title='Finland Eduskunta parliamentary election 2027',body='Eduskunta',seriesId='FI-eduskunta')
sql+=f"if not exists(select 1 from public.ea_records where id='world-finland-2027' and data in ({val(scheduled['data'])},{val(updated)})) then raise exception 'Scheduled Finland election changed'; end if;\nupdate public.ea_records set data={val(updated)},updated=now() where id='world-finland-2027';\n"
sql+=f"update public.ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(coverage)}::text)),updated=now() where id={lit(country['id'])};\nend $import$;\ncommit;\n"
(P/'import.sql').write_text(sql);print(len(records),'records;',len(parties),'parties;',len(sql),'SQL characters')
