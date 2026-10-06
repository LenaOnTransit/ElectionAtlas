// Read-only anonymous publication check; no credentials with write access.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {electionMetadata} from '../lib/seo.mjs';
const source=fs.readFileSync('lib/supabase.ts','utf8');
const api=source.match(/const url.*?'(https:[^']+)'/)[1];
const key=source.match(/const key.*?'(sb_publishable_[^']+)'/)[1];
const headers={apikey:key,'Content-Type':'application/json'};
const expected=JSON.parse(fs.readFileSync('scripts/timor-leste-election-records.json','utf8'));
const profiles=JSON.parse(fs.readFileSync('scripts/timor-leste-party-profiles.json','utf8'));
async function rpc(name,body={}) {
  const response=await fetch(api+'/rest/v1/rpc/'+name,{method:'POST',headers,body:JSON.stringify(body),signal:AbortSignal.timeout(60000)});
  assert.equal(response.status,200);
  return response.json();
}
const summaries=await rpc('ea_world_summaries');
await Promise.all(expected.map(async e=>{
  assert.ok(summaries.some(r=>r.id===e.id&&r.data.countryId==='tl'&&r.data.publication==='published'));
  const actual=await rpc('ea_public_election',{record_id:e.id});
  assert.deepEqual(actual,{...e,version:1});
}));
const partiesResponse=await fetch(api+'/rest/v1/ea_country_parties?country_id=eq.tl&select=*',{headers,signal:AbortSignal.timeout(60000)});
assert.equal(partiesResponse.status,200);
const actualParties=await partiesResponse.json();
for(const p of profiles) assert.deepEqual(actualParties.find(x=>x.id===p.id),p);
const country=fs.readFileSync('dist/archive/country/tl/index.html','utf8');
for(const e of expected) {
  assert.ok(country.includes('/world/election/'+e.id));
  const html=fs.readFileSync('dist/world/election/'+e.id+'/index.html','utf8');
  const seo=electionMetadata(e,'Timor-Leste');
  assert.ok(html.includes('<title>'+seo.title.replaceAll('&','&amp;')+'</title>'));
  assert.ok(html.includes('<h1>'+e.title+'</h1>'));
  assert.equal((html.match(/<title>/g)||[]).length,1);
  assert.equal((html.match(/<h1>/g)||[]).length,1);
  assert.ok(html.includes('https://worldofelections.com/world/election/'+e.id));
  assert.ok(html.includes(e.resultCoverage+' coverage'));
  for(const r of e.results) assert.ok(html.includes(r.name.replaceAll('&','&amp;').replaceAll('’','’').replaceAll("'",'&#39;')));
}
console.log('Anonymous publication verified: 14 exact version-1 records, 46 saved profiles, archive links and all generated election headings/SEO.');
