import fs from 'node:fs';
import ts from 'typescript';
import assert from 'node:assert/strict';
function moduleUrl(file, imports = {}) {
  let source = fs.readFileSync(file, 'utf8');
  for (const [from, to] of Object.entries(imports)) source = source.replaceAll("'" + from + "'", "'" + to + "'");
  return 'data:text/javascript;base64,' + Buffer.from(ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022}}).outputText).toString('base64');
}
const model = await import(moduleUrl('lib/world.ts', {'./house': moduleUrl('lib/house.ts'), './legitimacy': moduleUrl('lib/legitimacy.ts')}));
const base = 'scripts/czech-senate-2026-update/';
const records = JSON.parse(fs.readFileSync(base + 'records.json'));
const audit = JSON.parse(fs.readFileSync(base + 'audit.json'));
const previous = JSON.parse(fs.readFileSync(base + 'baseline.json')).find(r => r.id === records[0].id).data;
for (const e of records) model.validateWorldElection(e);
const [overview, runoff, ...districts] = records;
assert.equal(overview.totalSeats, 81);
assert.deepEqual(overview.results, previous.results);
assert.deepEqual(overview.legitimacy, previous.legitimacy);
assert.equal(districts.length, 27);
assert.equal(districts.flatMap(d => d.results).length, audit.candidates);
assert.equal(districts.flatMap(d => d.results).reduce((n, r) => n + (r.votes || 0), 0), audit.validVotes);
assert.equal(districts.flatMap(d => d.results).filter(r => r.winner).length, audit.officialFirstRoundWinners);
assert.equal(overview.linkedElectionIds.length, 28);
assert.equal(runoff.seriesId, overview.seriesId);
assert.equal(runoff.status, 'scheduled');
assert.equal(overview.live.updated, audit.timestamp);
assert.equal(overview.live.reporting, Math.round(audit.reportedPrecincts / audit.totalPrecincts * 10000) / 100);
for (const d of districts) {
  assert.equal(d.totalSeats, 1);
  assert.equal(d.overviewId, overview.id);
  assert.equal(d.resultCoverage, 'partial');
  assert.ok(d.results.every(r => r.seats === (r.winner ? 1 : 0)));
}
console.log('Czech Senate: 29 valid records; 27 districts and 154 candidates reconciled with official totals; 81-seat overview and existing party metadata preserved.');
