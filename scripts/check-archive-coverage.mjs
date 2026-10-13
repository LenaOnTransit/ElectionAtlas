import assert from 'node:assert/strict';
import {test} from 'node:test';
import {archiveCoverage} from '../lib/archive-coverage.mjs';
const record=(id,extra={})=>({id,countryId:'xx',publication:'published',status:'held',results:[],...extra});
test('coverage includes separate state and electoral-college tables once per election',()=>{
 const elections=[record('national',{results:[{seats:1}]}),record('states',{contests:[{results:[]},{results:[{votes:10}]}]}),record('overview'),record('college',{overviewId:'overview',results:[{votes:4}]}),record('missing'),record('related',{linkedElectionIds:['national']}),record('empty-state',{contests:[{results:[]}]}),record('future',{status:'scheduled',results:[{}]}),record('private',{publication:'draft',results:[{}]})];
 const before=JSON.stringify(elections),c=archiveCoverage(elections);
 assert.equal(c.total,7);assert.equal(c.withTables,4);assert.equal(c.countries,1);
 assert.deepEqual(c.missing.map(e=>e.id),['missing','related','empty-state']);assert.equal(JSON.stringify(elections),before);
});
test('private or future children and orphaned links do not manufacture coverage',()=>{
 const c=archiveCoverage([record('parent'),record('draft',{overviewId:'parent',publication:'draft',results:[{}]}),record('future',{overviewId:'parent',status:'scheduled',results:[{}]}),record('orphan',{overviewId:'absent',results:[{}]})]);
 assert.equal(c.withTables,1);assert.deepEqual(c.missing.map(e=>e.id),['parent']);
 assert.deepEqual(archiveCoverage([]),{total:0,countries:0,withTables:0,missing:[]});
});
