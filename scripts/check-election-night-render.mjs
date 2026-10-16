import {createServer} from 'vite';import {createElement} from 'react';import {renderToStaticMarkup} from 'react-dom/server';import assert from 'node:assert/strict';
const server=await createServer({server:{middlewareMode:true},appType:'custom'});
try{
 const {default:Board}=await server.ssrLoadModule('/app/explore/us-night.tsx'),{defaultSenate}=await server.ssrLoadModule('/lib/senate.ts'),{emptyHouse}=await server.ssrLoadModule('/lib/house.ts');
 for(const [sp,hp] of [['D','D'],['R','R'],['D','R'],['R','D'],['','']]){
  const senate=defaultSenate(),house=emptyHouse();if(sp)for(const r of senate.races)r.results.called=r.candidates.find(c=>c.party===sp).id;if(hp)house.results[hp]=218;
  for(const chamber of ['senate','house']){
   const expected=(chamber==='senate'?sp:hp)==='D'?'blue':(chamber==='senate'?sp:hp)==='R'?'red':'neutral';const html=renderToStaticMarkup(createElement(Board,{senate,house,initialChamber:chamber}));assert.ok(html.includes('night-tone-'+expected));assert.equal((html.match(/class="desk-seat-bar"/g)||[]).length,1);assert.ok(!html.includes('night-tower'));assert.ok(!/PRIVATE NEWSROOM|Simulation only|editor\//.test(html));
   if(chamber==='house'){assert.ok(html.includes('House hemicycle'));assert.equal((html.match(/<circle /g)||[]).length,435);assert.ok(!html.includes('Senate race calls'));}else{assert.ok(html.includes('Selected state information'));assert.ok(html.includes('Senate race calls'));}
  }
 }
 const {default:Room}=await server.ssrLoadModule('/app/editor/election-night/workspace.tsx');const denied=renderToStaticMarkup(createElement(Room,{initialSenate:defaultSenate(),initialHouse:emptyHouse()}));assert.match(denied,/Moderator access required/);assert.ok(!denied.includes('Both blue'));assert.ok(!denied.includes('Simulation controls'));
 const {default:Frame}=await server.ssrLoadModule('/app/explore/frame.tsx');const desk=renderToStaticMarkup(await Frame({mode:'us-night'}));assert.ok(desk.includes('election-night-desk'));assert.ok(!desk.includes('Main navigation'));assert.ok(desk.includes('World of Elections'));assert.ok(desk.includes('Presents…'));assert.ok(desk.includes('Skip intro'));assert.ok(desk.includes('role="timer"'));
 console.log('Election desk render: edge-to-edge shell, single bar, 435 House seats, chamber-specific colours, intro/countdown and moderator guard passed.');
}finally{await server.close();}
