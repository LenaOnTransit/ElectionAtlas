import fs from 'node:fs';import ts from 'typescript';import assert from 'node:assert/strict';
const js=ts.transpileModule(fs.readFileSync('lib/publication.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const p=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
process.env.TZ='Europe/Amsterdam';
assert.equal(p.scheduledInstant('2026-10-03T10:30'),'2026-10-03T08:30:00.000Z');
assert.equal(p.localDateTime('2026-10-03T08:30:00.000Z'),'2026-10-03T10:30');
assert.equal(p.scheduledInstant('2026-12-03T10:30'),'2026-12-03T09:30:00.000Z');
assert.throws(()=>p.scheduledInstant('2027-03-28T02:30')); // Missing hour during DST switch.
assert.throws(()=>p.scheduledInstant('2026-02-30T10:00'));
assert.throws(()=>p.scheduledInstant(''));
const future={status:'published',publishAt:'2026-10-03T08:30:00.000Z'};
assert.equal(p.publicationLabel(future,Date.parse('2026-10-03T08:29:59Z')),'Scheduled');
assert.equal(p.publicationLabel(future,Date.parse(future.publishAt)),'Published');
assert.equal(p.publicationLabel({...future,status:'draft'},Date.parse('2026-10-04')),'Draft');
p.validatePublication(future);p.validatePublication({status:'published'});
for(const publishAt of ['tomorrow','2026-10-03T08:30:00','infinity',null,123])assert.throws(()=>p.validatePublication({status:'published',publishAt}));
assert.throws(()=>p.validatePublication({...future,archived:true}));
console.log('Publication: local time, DST, invalid dates, release boundary and cancellation labels passed.');
