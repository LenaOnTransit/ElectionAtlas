"""Generate a guarded additive transaction; never connects to Supabase."""
from pathlib import Path
import json
OUT=Path(__file__).resolve().parent/'turkiye-election-import'
records=json.loads((OUT/'records.json').read_text());parties=json.loads((OUT/'parties.json').read_text());baseline=json.loads((OUT/'pre-import-backup.json').read_text())
country=baseline['records'][0];coverage=(OUT/'coverage.txt').read_text().strip()
def lit(s):return "'"+s.replace("'","''")+"'"
def value(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
sql='''begin;
do $import$
declare e jsonb; p jsonb; existing jsonb;
begin
'''
sql+=f"if not exists(select 1 from public.ea_records where id={lit(country['id'])} and kind='world_country' and data->>'coverageNote' in ({lit(country['data']['coverageNote'])},{lit(coverage)})) then raise exception 'Türkiye coverage changed after baseline'; end if;\n"
sql+=f"for p in select * from jsonb_array_elements({value(parties)}) loop\n"
sql+="select to_jsonb(t)-'updated_at'-'created_at' into existing from public.ea_country_parties t where id=(p->>'id')::uuid;\nif existing is not null and existing<>p then raise exception 'Party profile differs: %',p->>'id'; end if;\n"
sql+="insert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values((p->>'id')::uuid,p->>'country_id',p->>'name',p->>'short_name',p->>'color',array(select jsonb_array_elements_text(p->'ideology_ids')),p->>'notes',(p->>'archived')::boolean) on conflict(id) do nothing;\nend loop;\n"
sql+=f"for e in select * from jsonb_array_elements({value(records)}) loop\n"
sql+="if exists(select 1 from public.ea_records where id=e->>'id' and (kind<>'world_election' or data<>e)) then raise exception 'Election differs from checked import: %',e->>'id'; end if;\ninsert into public.ea_records(id,kind,data,updated) values(e->>'id','world_election',e,now()) on conflict(id) do nothing;\nend loop;\n"
sql+=f"update public.ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(coverage)}::text)),updated=now() where id={lit(country['id'])};\n"
sql+='end $import$;\ncommit;\n'
(OUT/'import.sql').write_text(sql)
print(f'{len(records)} elections, {len(parties)} parties; {len(sql)} SQL characters; additive guarded transaction')
