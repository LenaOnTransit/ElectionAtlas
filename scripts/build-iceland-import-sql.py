"""Generate additive, idempotent, content-guarded public archive updates."""
from pathlib import Path
import json
P=Path(__file__).parent/'iceland-election-import';records=json.loads((P/'records.json').read_text());parties=json.loads((P/'parties.json').read_text());baseline=json.loads((P/'pre-import-backup.json').read_text());old={r['id']:r['data'] for r in baseline};country=old['world-country-is']
coverage='National parliamentary elections from 1874 through 2024, the 1844 election to the restored Althing, separate nationwide upper-house elections in 1916–1930, presidential selections and unopposed renewals from 1944 through 2024, and the subsequently annulled 2010 Constitutional Assembly election. Royal appointees are not portrayed as elected. Historical combined-house tables can include continuing upper-house members and identify that distinction. Five elections—1902, 1903, 1908, 1911 and 1914—have verified dates and turnout but no verified national party breakdown in this archive. Some historical vote allocations contain fractions, explained in their notes. No ballot totals or turnout are invented for unopposed returns.'
(P/'coverage.txt').write_text(coverage+'\n')
def lit(x):return "'"+x.replace("'","''")+"'"
def val(x):return lit(json.dumps(x,ensure_ascii=False,separators=(',',':')))+'::jsonb'
head='begin; do $import$ declare e jsonb; p jsonb; existing jsonb; begin\n'
guard=f"if not exists(select 1 from ea_records where id='world-country-is' and data->>'coverageNote' in ({lit(country['coverageNote'])},{lit(coverage)})) then raise exception 'Iceland coverage changed'; end if;\n"
partyloop=f"for p in select value from jsonb_array_elements({val(parties)}) loop select to_jsonb(t)-'created_at'-'updated_at' into existing from ea_country_parties t where id=(p->>'id')::uuid; if existing is not null and existing<>p then raise exception 'Party changed'; end if; insert into ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values((p->>'id')::uuid,p->>'country_id',p->>'name',p->>'short_name',p->>'color',array(select jsonb_array_elements_text(p->'ideology_ids')),p->>'notes',(p->>'archived')::boolean) on conflict(id) do nothing; end loop;\n"
def elections(es):
 s=''
 for e in es:
  allowed=[val(e)]+([val(old[e['id']])] if e['id'] in old else [])
  s+=f"select data into existing from ea_records where id={lit(e['id'])} for update; if existing is not null and existing not in ({','.join(allowed)}) then raise exception 'Election changed {e['id']}'; end if; insert into ea_records(id,kind,data,updated) values({lit(e['id'])},'world_election',{val(e)},now()) on conflict(id) do update set data=excluded.data,updated=now();\n"
 return s
end='end $import$; commit;\n';cover=f"update ea_records set data=jsonb_set(data,'{{coverageNote}}',to_jsonb({lit(coverage)}::text)),updated=now() where id='world-country-is';\n"
(P/'import.sql').write_text(head+guard+partyloop+elections(records)+cover+end)
# Publication batches keep individual review requests small; every record remains guarded.
batches=[head+guard+partyloop+end]+[head+guard+elections(records[i:i+3])+end for i in range(0,len(records),3)]+[head+guard+cover+end]
cache=P.parents[1]/'.cache/iceland';(cache/'batches.json').write_text(json.dumps(batches));print(len(records),'records;',len(parties),'parties;',len(batches),'guarded batches')
