import type {WorldElection} from './world';
export function parliamentGroups(e:WorldElection){
  if(e.type!=='parliamentary')return null;
  const valid=(n:unknown):n is number=>typeof n==='number'&&Number.isInteger(n)&&n>=0&&n<=10000;
  if(e.results.some(r=>r.seats!=null&&!valid(r.seats))||e.totalSeats!=null&&!valid(e.totalSeats))return null;
  const groups=e.results.filter(r=>r.seats!=null).map(r=>({id:r.id,name:r.name,color:r.color,seats:r.seats!}));
  const entered=groups.reduce((n,r)=>n+r.seats,0);
  if(!entered||entered>10000||e.totalSeats!=null&&entered>e.totalSeats)return null;
  const total=e.totalSeats??entered;
  if(total>entered)groups.push({id:'unassigned-seats',name:'Not entered',color:'#cbd5e1',seats:total-entered});
  return {groups,entered,total,missing:e.results.some(r=>r.seats==null),knownTotal:e.totalSeats!=null};
}
export function hemicycleLayout(total:number){
  if(!Number.isInteger(total)||total<0||total>10000)throw new Error('Invalid seat count');
  if(!total)return [];
  const rows=Math.max(1,Math.ceil(Math.sqrt(total)/3));
  const radii=Array.from({length:rows},(_,i)=>rows===1?270:270*(.48+.52*i/(rows-1)));
  const weight=radii.reduce((a,b)=>a+b,0),quotas=radii.map(r=>total*r/weight),counts=quotas.map(Math.floor);
  const order=quotas.map((q,i)=>({i,f:q-counts[i]})).sort((a,b)=>b.f-a.f);
  for(let i=0,left=total-counts.reduce((a,b)=>a+b,0);i<left;i++)counts[order[i].i]++;
  const spacing=Math.min(...radii.map((r,i)=>counts[i]>1?2*r*Math.sin(Math.PI/(2*counts[i])):r));
  const size=Math.min(14,spacing*.38,rows>1?(radii[1]-radii[0])*.37:14);
  return radii.flatMap((r,i)=>Array.from({length:counts[i]},(_,j)=>{const angle=(j+.5)*Math.PI/counts[i];return {x:300-r*Math.cos(angle),y:305-r*Math.sin(angle),radius:size,angle,row:i};})).sort((a,b)=>a.angle-b.angle||a.row-b.row);
}
