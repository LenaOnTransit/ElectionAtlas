/** Count public held records with their own or explicitly nested result tables.
 * A table's presence does not imply complete or certified coverage. Related
 * elections are not substitutes for a record's results (e.g. a linked runoff).
 */
export function archiveCoverage(elections) {
  const held = elections.filter(e => e.publication === 'published' && e.status === 'held');
  const ownTables = new Set(held.filter(e => e.results?.length || e.contests?.some(c => c.results?.length)).map(e => e.id));
  const parentsWithTables = new Set(held.filter(e => e.overviewId && ownTables.has(e.id)).map(e => e.overviewId));
  const withTables = held.filter(e => ownTables.has(e.id) || parentsWithTables.has(e.id));
  return {total: held.length, countries: new Set(held.map(e => e.countryId)).size,
    withTables: withTables.length, missing: held.filter(e => !ownTables.has(e.id) && !parentsWithTables.has(e.id))};
}
