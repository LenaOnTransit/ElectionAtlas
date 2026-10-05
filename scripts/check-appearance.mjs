import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import ts from 'typescript';
import {renderToStaticMarkup} from 'react-dom/server';
import {createElement} from 'react';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const folder=await fs.mkdtemp(path.join(root,'scripts','.appearance-check-'));
try{
 const source=await fs.readFile(path.join(root,'app/appearance.tsx'),'utf8');
 const compiled=ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
 const file=path.join(folder,'appearance.mjs');await fs.writeFile(file,compiled);const appearance=await import(pathToFileURL(file));
 const listeners={};const media={matches:true,addEventListener:(event,fn)=>listeners['media-'+event]=fn};
 globalThis.document={documentElement:{dataset:{}}};globalThis.window={matchMedia:()=>media,addEventListener:(event,fn)=>listeners[event]=fn};
 const storage=new Map();globalThis.localStorage={getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)};
 appearance.initializeAppearance();assert.equal(document.documentElement.dataset.theme,'dark');
 storage.set('woe-theme','light');listeners.storage();assert.equal(document.documentElement.dataset.theme,'light');
 media.matches=false;listeners['media-change']();assert.equal(document.documentElement.dataset.theme,'light');
 storage.delete('woe-theme');media.matches=true;listeners['media-change']();assert.equal(document.documentElement.dataset.theme,'dark');
 globalThis.localStorage={getItem:()=>{throw Error('blocked')}};appearance.initializeAppearance();assert.equal(document.documentElement.dataset.theme,'dark');
 assert.equal(appearance.senateColour('D','safe','#123456','standard'),'#123456');assert.notEqual(appearance.senateColour('D','safe','blue','accessible'),appearance.senateColour('R','safe','red','accessible'));
 const svg=renderToStaticMarkup(createElement(appearance.MapPatternDefs,{prefix:'test',count:20}));assert.equal((svg.match(/<pattern /g)||[]).length,20);assert.equal(new Set([...svg.matchAll(/id="([^"]+)"/g)].map(m=>m[1])).size,20);
 assert.match(renderToStaticMarkup(createElement(appearance.MapSwatch,{index:8,original:'#112233',palette:'accessible'})),/repeating-linear-gradient/);
 assert.doesNotMatch(renderToStaticMarkup(createElement(appearance.MapSwatch,{index:8,original:'#112233',palette:'accessible',patterns:false})),/repeating-linear-gradient/);
 console.log('Appearance: device theme, saved choice, system changes, blocked storage, standard party colours and distinct patterned keys passed.');
}finally{await fs.rm(folder,{recursive:true,force:true})}
