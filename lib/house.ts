export const HOUSE_SEATS=435, HOUSE_MAJORITY=218;
export const houseRatings=[['safeD','Safe Democratic','#174a9c'],['likelyD','Likely Democratic','#4a80c4'],['leanD','Lean Democratic','#98b8df'],['tossup','Tossup','#dfd1a7'],['leanR','Lean Republican','#e8a5ab'],['likelyR','Likely Republican','#cf626d'],['safeR','Safe Republican','#aa202a'],['other','Other','#88539f']] as const;
export type HouseRating=typeof houseRatings[number][0];
export type HouseParty='D'|'R'|'O';
export type HouseRace={id:string;district:string;incumbent:HouseParty;rating:HouseRating;call:HouseParty|'';candidates:{name:string;party:HouseParty;poll:number|null;votes:number|null}[];notes:string};
export type HouseOverview={updated:string;notes:string;source:string;forecast:{model?:'ratings'|'manual';ratingChances?:{safe:number;likely:number;lean:number};ratings:Record<HouseRating,number>;probabilityD:number|null;genericD:number|null;genericR:number|null;demMin:number|null;demMax:number|null};results:{D:number;R:number;O:number;called:HouseParty|'';status:'provisional'|'final';voteD:number|null;voteR:number|null};previous:{D:number|null;R:number|null;O:number|null};races:HouseRace[]};
export function emptyHouse():HouseOverview{return {updated:'',notes:'',source:'',forecast:{model:'ratings',ratingChances:{safe:99,likely:85,lean:65},ratings:Object.fromEntries(houseRatings.map(([k])=>[k,0])) as Record<HouseRating,number>,probabilityD:null,genericD:null,genericR:null,demMin:null,demMax:null},results:{D:0,R:0,O:0,called:'',status:'provisional',voteD:null,voteR:null},previous:{D:null,R:null,O:null},races:[]};}
export function houseTotals(h:HouseOverview,mode:'polling'|'results'){const D=mode==='results'?h.results.D:h.forecast.ratings.safeD+h.forecast.ratings.likelyD+h.forecast.ratings.leanD,R=mode==='results'?h.results.R:h.forecast.ratings.safeR+h.forecast.ratings.likelyR+h.forecast.ratings.leanR,O=mode==='results'?h.results.O:h.forecast.ratings.other;return {D,R,O,remaining:HOUSE_SEATS-D-R-O,uncategorized:mode==='results'?HOUSE_SEATS-D-R-O:HOUSE_SEATS-Object.values(h.forecast.ratings).reduce((a,b)=>a+b,0)};}
export function validateHouse(h:HouseOverview){
 const fail=(s:string):never=>{throw Error(s);};const count=(n:unknown)=>typeof n==='number'&&Number.isInteger(n)&&n>=0&&n<=435;const optional=(n:unknown,max=100,integer=false)=>n===null||typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=max&&(!integer||Number.isInteger(n));const text=(s:unknown,max:number)=>typeof s==='string'&&s.length<=max;
 if(!h||!h.forecast||!h.results||!h.previous||!Array.isArray(h.races)||h.races.length>435||!text(h.updated,100)||!text(h.source,2000)||!text(h.notes,10000))fail('Check House overview fields.');
 if(h.forecast.model!==undefined&&!['ratings','manual'].includes(h.forecast.model))fail('Choose a House probability model.');
 if(h.forecast.ratingChances){const c=h.forecast.ratingChances;if(![c.safe,c.likely,c.lean].every(n=>typeof n==='number'&&Number.isFinite(n)&&n>=50&&n<=100)||c.safe<c.likely||c.likely<c.lean)fail('House rating probabilities must be ordered safe ≥ likely ≥ lean and between 50 and 100.');}
 if(!h.forecast.ratings||houseRatings.some(([k])=>!count(h.forecast.ratings[k]))||Object.values(h.forecast.ratings).reduce((a,b)=>a+b,0)>435)fail('Forecast categories must total no more than 435 seats.');
 for(const k of ['probabilityD','genericD','genericR'] as const)if(!optional(h.forecast[k]))fail('Forecast percentages must be between 0 and 100.');
 for(const k of ['demMin','demMax'] as const)if(!optional(h.forecast[k],435,true))fail('Seat ranges must be whole numbers between 0 and 435.');
 if((h.forecast.demMin===null)!==(h.forecast.demMax===null)||h.forecast.demMin!==null&&h.forecast.demMax!==null&&h.forecast.demMin>h.forecast.demMax)fail('Enter both range endpoints, with the minimum first.');
 if((h.forecast.genericD??0)+(h.forecast.genericR??0)>100||(h.results.voteD??0)+(h.results.voteR??0)>100)fail('Party vote percentages cannot total more than 100%.');
 if(!optional(h.results.voteD)||!optional(h.results.voteR)||!['provisional','final'].includes(h.results.status))fail('Check result percentages and status.');
 for(const p of ['D','R','O'] as const)if(!count(h.results[p])||!optional(h.previous[p],435,true))fail('Check seats won and previous seats.');
 if(houseTotals(h,'results').remaining<0)fail('Results cannot exceed 435 seats.');
 if(!['','D','R','O'].includes(h.results.called)||h.results.called&&h.results[h.results.called]<218)fail('A control call requires at least 218 seats won by that party.');
 if(h.results.status==='final'&&houseTotals(h,'results').remaining!==0)fail('Final national results require all 435 seats entered.');
 if(Object.values(h.previous).reduce<number>((n,x)=>n+(x??0),0)>435)fail('Previous seats cannot exceed 435.');
 const ids=new Set(),districts=new Set();for(const r of h.races){if(!r||!text(r.id,100)||ids.has(r.id)||!text(r.district,30)||!r.district.trim()||districts.has(r.district.trim().toUpperCase())||!['D','R','O'].includes(r.incumbent)||!['','D','R','O'].includes(r.call)||!houseRatings.some(([k])=>k===r.rating)||!text(r.notes,5000)||!Array.isArray(r.candidates)||r.candidates.length>20)fail('Check race names, ratings and calls; districts must be unique.');ids.add(r.id);districts.add(r.district.trim().toUpperCase());for(const c of r.candidates)if(!text(c.name,200)||!['D','R','O'].includes(c.party)||!optional(c.poll)||!optional(c.votes,1e12,true))fail('Check candidate polling and votes.');if(r.candidates.reduce((n,c)=>n+(c.poll??0),0)>100)fail('District polling cannot exceed 100%.');}
}

export function houseControl(h:HouseOverview){
 const t=houseTotals(h,'polling'),configured=435-t.uncategorized;
 if(h.forecast.model==='manual'){const p=h.forecast.probabilityD;return p===null?null:{D:p/100,R:1-p/100,other:0,expectedD:null,expectedR:null,configured,unrated:t.uncategorized,manual:true};}
 if(!configured||t.uncategorized<0)return null;
 const chances=h.forecast.ratingChances??{safe:99,likely:85,lean:65},r=h.forecast.ratings;
 const categories:[number,number][]=[[r.safeD,chances.safe/100],[r.likelyD,chances.likely/100],[r.leanD,chances.lean/100],[r.tossup+t.uncategorized,.5],[r.leanR,1-chances.lean/100],[r.likelyR,1-chances.likely/100],[r.safeR,1-chances.safe/100]];
 let dist=[1],expectedD=0;
 for(const [count,p]of categories){expectedD+=count*p;for(let i=0;i<count;i++){const next=Array(dist.length+1).fill(0);for(let d=0;d<dist.length;d++){next[d]+=dist[d]*(1-p);next[d+1]+=dist[d]*p;}dist=next;}}
 const contested=435-r.other;let D=0,R=0,other=0;
 for(let d=0;d<dist.length;d++){if(d>=218)D+=dist[d];else if(contested-d>=218)R+=dist[d];else other+=dist[d];}
 return {D,R,other,expectedD,expectedR:contested-expectedD,configured,unrated:t.uncategorized,manual:false};
}
