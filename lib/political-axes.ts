import type {WorldResult} from './world';
export const politicalAxes=[
 ['socialistCapitalist','Socialist','Capitalist'],['libertarianAuthoritarian','Libertarian','Authoritarian'],
 ['progressiveConservative','Progressive','Conservative'],['pacifistInterventionist','Pacifist','Interventionist'],
 ['democracyAutocracy','Democracy','Autocracy'],['plannedFreeMarket','Planned economy','Free market'],
 ['irreligiousReligious','Irreligious','Religious'],['globalismProtectionism','Globalism','Protectionism'],
 ['bioconservativeTechprogressive','Bioconservative','Techprogressive']
] as const;
export type Axis=typeof politicalAxes[number][0];
export type AxisScores=Partial<Record<Axis,number>>;
export type IdeologyScores={ideology_id:string;scores:AxisScores};
export function validateScores(scores:AxisScores){if(!scores||typeof scores!=='object'||Array.isArray(scores)||Object.entries(scores).some(([key,value])=>!politicalAxes.some(a=>a[0]===key)||typeof value!=='number'||!Number.isFinite(value)||value < -10||value > 10))throw Error('Axis values must be between -10 and 10. Leave unassessed axes blank.');}
export type AxisSide='negative'|'neutral'|'positive'|'unassessed';
export type ParliamentPosition={result_id:string;side:AxisSide};
export function classifyByAxes(rows:WorldResult[],axes:Axis[],scores:IdeologyScores[],reverse=false):ParliamentPosition[]{
 const values=new Map(scores.map(s=>[s.ideology_id,s.scores]));
 const positions=rows.map((r,index)=>{const perAxis=axes.map(a=>{const v=(r.ideologyIds||[]).map(id=>values.get(id)?.[a]).filter((v):v is number=>typeof v==='number');return v.length?v.reduce((n,v)=>n+v,0)/v.length:null;});return {id:r.id,index,value:axes.length&&perAxis.every(v=>v!==null)?perAxis.reduce<number>((n,v)=>n+v!,0)/axes.length:null};});
 return positions.sort((a,b)=>a.value===null?(b.value===null?a.index-b.index:1):b.value===null?-1:(reverse?-1:1)*(a.value-b.value)||a.index-b.index).map(r=>({result_id:r.id,side:r.value===null?'unassessed':r.value<0?'negative':r.value>0?'positive':'neutral'}));
}
export function orderByAxes(rows:WorldResult[],axes:Axis[],scores:IdeologyScores[],reverse=false):string[]{return classifyByAxes(rows,axes,scores,reverse).map(r=>r.result_id);}
