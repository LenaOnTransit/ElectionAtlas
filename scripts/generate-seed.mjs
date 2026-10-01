import fs from 'node:fs';import ts from 'typescript';
function moduleUrl(source,imports={}){for(const[from,to]of Object.entries(imports))source=source.replaceAll("'"+from+"'","'"+to+"'");return 'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64');}
const worldURL=moduleUrl(fs.readFileSync('lib/world.ts','utf8'));
const {seedWorldElections}=await import(moduleUrl(fs.readFileSync('lib/world-seeds.ts','utf8'),{'./world':worldURL}));
const {seedCountries}=await import(moduleUrl(fs.readFileSync('lib/world-countries.ts','utf8'),{'./world':worldURL}));
const {defaultSenate}=await import(moduleUrl(fs.readFileSync('lib/senate.ts','utf8')));
const content=fs.readFileSync('db/content.ts','utf8').split('export async function content')[0].replace(/^import .*\n/,'');
const {samples,sampleElection}=await import(moduleUrl(content));
const quote=s=>"'"+s.replaceAll("'","''")+"'";
const entries=[...samples.map(data=>({id:data.id,kind:'article',data})),{id:sampleElection.id,kind:'election',data:sampleElection},{id:'senate-2026',kind:'senate',data:defaultSenate()},...seedCountries.map(data=>({id:'world-country-'+data.id,kind:'world_country',data})),...seedWorldElections.map(data=>({id:data.id,kind:'world_election',data}))];
fs.writeFileSync('supabase/seed.sql','-- Public sample/curated seeds only. Existing records are never overwritten.\nINSERT INTO public.ea_records(id,kind,data) VALUES\n'+entries.map(e=>'('+quote(e.id)+','+quote(e.kind)+','+quote(JSON.stringify(e.data))+'::jsonb)').join(',\n')+'\nON CONFLICT(id) DO NOTHING;\n');
console.log(`Prepared ${entries.length} public seed records.`);
