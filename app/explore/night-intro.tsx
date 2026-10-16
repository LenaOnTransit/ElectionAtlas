import {useEffect,useState} from 'react';
export default function NightIntro({onDone}:{onDone:()=>void}){
 const [scene,setScene]=useState(0);
 useEffect(()=>{if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){onDone();return;}const second=setTimeout(()=>setScene(1),2800),end=setTimeout(onDone,5600);return()=>{clearTimeout(second);clearTimeout(end)}},[onDone]);
 return <div className="desk-intro" role="dialog" aria-modal="true" aria-label="Election Night introduction" onKeyDown={e=>{if(e.key==='Escape')onDone()}}><div className="desk-intro-copy" key={scene}>{scene===0?<><strong>World of Elections</strong><span>Presents…</span></>:<><span className="desk-intro-eyebrow">THE 2026 U.S. MIDTERMS</span><strong>Election Night Desk</strong></>}</div><button autoFocus onClick={onDone}>Skip intro →</button></div>;
}
