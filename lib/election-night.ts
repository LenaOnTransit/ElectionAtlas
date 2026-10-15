import {calledCandidate,type Senate} from './senate';
import {HOUSE_MAJORITY,HOUSE_SEATS,type HouseOverview} from './house';
export type NightControl='D'|'R'|'unresolved';
export type NightBalance={D:number;R:number;other:number;baselineD:number;baselineR:number;uncalled:number;total:number;thresholdD:number;thresholdR:number;control:NightControl};
export function senateNightBalance(s:Senate):NightBalance{
 const baselineD=s.baseline.D+(s.baseline.independentCaucus==='D'?s.baseline.I:0),baselineR=s.baseline.R+(s.baseline.independentCaucus==='R'?s.baseline.I:0);
 let D=baselineD,R=baselineR,other=s.baseline.independentCaucus==='I'?s.baseline.I:0,called=0;
 for(const race of s.races){const winner=calledCandidate(race);if(!winner)continue;called++;const caucus=winner.party==='I'?race.independentCaucus:winner.party;if(caucus==='D')D++;else if(caucus==='R')R++;else other++;}
 const thresholdD=s.tieBreaker==='D'?50:51,thresholdR=s.tieBreaker==='R'?50:51;
 return {D,R,other,baselineD,baselineR,uncalled:s.races.length-called,total:100,thresholdD,thresholdR,control:D>=thresholdD?'D':R>=thresholdR?'R':'unresolved'};
}
export function houseNightBalance(h:HouseOverview):NightBalance{
 const {D,R,O:other}=h.results;
 // National totals already cover district calls. Never add selected races twice.
 return {D,R,other,baselineD:0,baselineR:0,uncalled:HOUSE_SEATS-D-R-other,total:HOUSE_SEATS,thresholdD:HOUSE_MAJORITY,thresholdR:HOUSE_MAJORITY,control:D>=HOUSE_MAJORITY?'D':R>=HOUSE_MAJORITY?'R':'unresolved'};
}
export function congressNightTone(senate:NightControl,house:NightControl){
 if(senate==='unresolved'||house==='unresolved')return 'neutral';
 return senate===house?(senate==='D'?'blue':'red'):'purple';
}
export function setSimulatedSenateCall(s:Senate,raceId:string,candidateId:string):Senate{
 return {...s,races:s.races.map(r=>r.id===raceId?{...r,results:{...r.results,called:r.candidates.some(c=>c.id===candidateId)?candidateId:''}}:r)};
}
export function addSimulatedHouseCall(h:HouseOverview,party:'D'|'R'|'O',state:string):HouseOverview{
 if(h.results.D+h.results.R+h.results.O>=HOUSE_SEATS)return h;
 const id='test-'+(h.races.length+1);
 return {...h,results:{...h.results,[party]:h.results[party]+1,called:'',status:'provisional'},races:[...h.races,{id,district:state+'-TEST-'+(h.races.length+1),incumbent:'O',rating:'tossup',call:party,candidates:[],notes:'Simulated district for this private test session.'}]};
}
