import {createServer} from 'vite';import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';import assert from 'node:assert/strict';
const server=await createServer({server:{middlewareMode:true},appType:'custom'});
try{
 const {default:Board}=await server.ssrLoadModule('/app/explore/us-night.tsx'),{defaultSenate}=await server.ssrLoadModule('/lib/senate.ts'),{emptyHouse}=await server.ssrLoadModule('/lib/house.ts');
 for(const [sp,hp,tone] of [['D','D','blue'],['R','R','red'],['D','R','purple'],['R','D','purple'],['','','neutral']]){
  const senate=defaultSenate(),house=emptyHouse();if(sp)for(const r of senate.races)r.results.called=r.candidates.find(c=>c.party===sp).id;if(hp)house.results[hp]=218;
  const html=renderToStaticMarkup(createElement(Board,{senate,house}));assert.ok(html.includes('night-tone-'+tone));assert.equal((html.match(/role="meter"/g)||[]).length,2);assert.ok(html.includes('Selected state information'));assert.ok(html.includes('Senate race calls'));assert.ok(!/PRIVATE NEWSROOM|Simulation only|editor\//.test(html));
 }
 const {default:Room}=await server.ssrLoadModule('/app/editor/election-night/workspace.tsx');const denied=renderToStaticMarkup(createElement(Room,{initialSenate:defaultSenate(),initialHouse:emptyHouse()}));assert.match(denied,/Moderator access required/);assert.ok(!denied.includes('Both blue'));assert.ok(!denied.includes('Simulation controls'));
 console.log('Election night render: all control tones, two accessible bars, map/state panel, public copy and unauthorised test-room denial passed.');
}finally{await server.close();}
