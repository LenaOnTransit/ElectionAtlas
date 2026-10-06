import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import ts from 'typescript';
import {electionMetadata} from '../lib/seo.mjs';

function moduleUrl(file, imports = {}) {
  let source = fs.readFileSync(file, 'utf8');
  for (const [from, to] of Object.entries(imports)) source = source.replaceAll(`'${from}'`, `'${to}'`);
  const js = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022}}).outputText;
  return 'data:text/javascript;base64,' + Buffer.from(js).toString('base64');
}
const {validateWorldElection} = await import(moduleUrl('lib/world.ts', {
  './house': moduleUrl('lib/house.ts'), './legitimacy': moduleUrl('lib/legitimacy.ts'),
}));
const {validateParty} = await import(moduleUrl('lib/country-parties.ts'));
const dir = 'scripts/montenegro-election-import/';
const read = name => JSON.parse(fs.readFileSync(dir + name, 'utf8'));
const records = read('records.json'), parties = read('parties.json'), audit = read('source-audit.json');
assert.equal(records.length, 59);
assert.equal(parties.length, 20);
const ids = new Set(records.map(e => e.id)), partyIds = new Set(parties.map(p => p.id));
assert.equal(ids.size, records.length);
assert.equal(partyIds.size, parties.length);
for (const party of parties) {
  validateParty(party);
  assert.equal(party.country_id, 'me');
  assert.deepEqual(party.ideology_ids, []);
}
for (const e of records) {
  validateWorldElection(e);
  assert.equal(e.countryId, 'me');
  assert.equal(e.type, 'parliamentary');
  assert.equal(e.publication, 'published');
  assert.equal(e.resultStatus, 'final');
  assert.equal(e.version, 1);
  assert.equal(e.precision, 'day');
  assert.equal(e.checked, audit.checked);
  assert.ok(e.id.startsWith(`world-montenegro-${e.startDate}-`));
  assert.ok(e.seriesId && e.voteBasis && e.summary && e.notes);
  for (const r of e.results) {
    assert.ok(!r.partyId || partyIds.has(r.partyId));
    assert.deepEqual(r.ideologyIds, []);
    assert.equal(r.winner, false);
    assert.equal(r.advanced, false);
  }
  for (const linked of e.linkedElectionIds || []) {
    assert.ok(ids.has(linked));
    assert.ok(records.find(r => r.id === linked).linkedElectionIds.includes(e.id));
  }
  const metadata = electionMetadata(e, 'Montenegro');
  assert.ok(metadata.title.includes('Montenegro'));
  assert.ok(metadata.description.length > 30);
  if (e.startDate < '1990-01-01') {
    assert.equal(e.resultCoverage, 'partial');
    assert.equal(e.turnout, null);
    for (const r of e.results) {
      assert.equal(r.votes, null);
      assert.equal(r.share, null);
      assert.equal(r.previousSeats, null);
      assert.equal(r.electoralVotes, null);
    }
    if (e.round === 'Half-renewal') {
      assert.equal(e.results.reduce((s, r) => s + r.seats, 0), e.totalSeats / 2);
      assert.ok(e.notes.includes('retained'));
    }
  }
}
for (const a of audit.nationalElections) {
  const e = records.find(r => r.id === a.id);
  assert.equal(e.results.reduce((s, r) => s + r.votes, 0), a.recordedVotes);
  assert.equal(e.results.reduce((s, r) => s + r.seats, 0), a.seats);
  assert.equal(e.totalSeats, a.seats);
  assert.ok(Math.abs(e.turnout - 100 * a.voters / a.electorate) < .000051);
  for (const r of e.results) assert.ok(Math.abs(r.share - 100 * r.votes / a.validVotes) < .00000051);
  assert.equal(a.validVotes - a.recordedVotes, e.startDate.startsWith('2006') ? 2 : 0);
  assert.equal(e.resultCoverage, a.unallocatedVotes ? 'partial' : 'complete');
}
for (const [file, hash] of Object.entries(audit.sourceExtractHashes)) {
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(dir + file)).digest('hex'), hash);
}
const radicals = records.find(e => e.startDate === '2016-10-16').results.find(r => r.votes === 693);
assert.equal(radicals.party, 'SSR');
assert.ok(!radicals.partyId);
assert.equal(records.filter(e => e.resultCoverage === 'complete').length, 11);
console.log('Montenegro: 59 model-valid records, 20 party profiles, 12 reconciled national tables (documented 2006 gap), historical nulls, links and SEO passed.');
