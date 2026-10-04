import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
const compiled=ts.transpileModule(fs.readFileSync('lib/moderator-access.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {createModeratorAccess}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));

test('Editor links require verified moderator membership; readers and lookup errors stay hidden',async()=>{
 for(const [user,expected]of [[null,false],[{role:'reader'},false],[{role:'admin'},true]]){
  const states=[];const access=createModeratorAccess(async()=>user,state=>states.push(state));
  await access.refresh();assert.equal(states[0],false);assert.equal(states.at(-1),expected);
  access.invalidate();assert.equal(states.at(-1),false);
 }
 const states=[];await createModeratorAccess(async()=>{throw Error('Unavailable');},s=>states.push(s)).refresh();
 assert.equal(states.at(-1),false);
});
test('Signing out or changing account prevents an old moderator lookup from revealing links',async()=>{
 let complete;const states=[];
 const access=createModeratorAccess(()=>new Promise(resolve=>{complete=resolve;}),s=>states.push(s));
 const pending=access.refresh();access.invalidate();complete({role:'admin'});await pending;
 assert.deepEqual(states,[false,false]);
 const second=access.refresh();access.dispose();complete({role:'admin'});await second;
 assert.equal(states.at(-1),false);
});
test('A newer reader check wins even if a moderator check finishes later',async()=>{
 const pending=[],states=[];const access=createModeratorAccess(()=>new Promise(resolve=>pending.push(resolve)),s=>states.push(s));
 const moderator=access.refresh(),reader=access.refresh();
 pending[1]({role:'reader'});await reader;pending[0]({role:'admin'});await moderator;
 assert.equal(states.at(-1),false);assert.ok(!states.includes(true));
});
