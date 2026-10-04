import type {WorldElection} from './world';
import type {AxisSide} from './political-axes';
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
// Paint a band for each seating row so even seats sharing an angle stay on
// their own side. Boundaries follow seat allocation, not the SVG midpoint.
export function spectrumGeometry(dots:ReturnType<typeof hemicycleLayout>,sides:AxisSide[],reverse=false){
 if(dots.length!==sides.length)throw new Error('Every seat needs a classification');
 const rows=[...new Set(dots.map(d=>d.row))].sort((a,b)=>a-b).map(row=>dots.map((d,index)=>({...d,index})).filter(d=>d.row===row));
 const point=(r:number,a:number)=>[300-r*Math.cos(a),305-r*Math.sin(a)];
 const xy=(r:number,a:number)=>point(r,a).map(n=>n.toFixed(3)).join(' ');
 const bands:{side:AxisSide;path:string;row:number;start:number;end:number}[]=[];
 const cuts=sides.flatMap((side,i)=>i>0&&side!==sides[i-1]?[{index:i,zero:side!=='unassessed'&&sides[i-1]!=='unassessed'}]:[]);
 // A chamber entirely on one pole still has a zero boundary, at its edge.
 if(!cuts.some(c=>c.zero)){
  const first=sides.findIndex(s=>s==='negative'||s==='positive');
  if(first>=0){const side=sides[first],last=sides.lastIndexOf(side)+1;cuts.push({index:(side==='negative')!==reverse?last:first,zero:true});}
 }
 const borders=cuts.map(c=>({...c,points:[] as string[]}));
 rows.forEach((row,ri)=>{
  const r=Math.hypot(row[0].x-300,row[0].y-305);
  const prev=ri?Math.hypot(rows[ri-1][0].x-300,rows[ri-1][0].y-305):r-2*row[0].radius-8;
  const next=ri+1<rows.length?Math.hypot(rows[ri+1][0].x-300,rows[ri+1][0].y-305):r+2*row[0].radius+8;
  const inner=(prev+r)/2,outer=(next+r)/2;
  const edge=(count:number)=>count===0?0:count===row.length?Math.PI:(row[count-1].angle+row[count].angle)/2;
  let start=0;
  for(let j=1;j<=row.length;j++)if(j===row.length||sides[row[j].index]!==sides[row[start].index]){
   const a=edge(start),b=edge(j),large=b-a>Math.PI?1:0;
   bands.push({side:sides[row[start].index],row:row[0].row,start:a,end:b,path:`M ${xy(inner,a)} L ${xy(outer,a)} A ${outer} ${outer} 0 ${large} 1 ${xy(outer,b)} L ${xy(inner,b)} A ${inner} ${inner} 0 ${large} 0 ${xy(inner,a)} Z`});start=j;
  }
  borders.forEach(c=>{const angle=edge(row.filter(d=>d.index<c.index).length);if(!ri)c.points.push(xy(inner,angle));c.points.push(xy(r,angle));if(ri===rows.length-1)c.points.push(xy(outer,angle));});
 });
 return {bands,borders:borders.map(c=>({zero:c.zero,path:'M '+c.points.join(' L ')}))};
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
