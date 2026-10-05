import {WorldElection,WorldResult} from './world';
export const majority=(e:WorldElection)=>e.majorityThreshold|| (e.totalSeats?Math.floor(e.totalSeats/2)+1:null);
export const seatTotal=(e:WorldElection)=>e.results.reduce((n,r)=>n+(r.seats??0),0);
export function comparable(a:WorldElection,b:WorldElection){return a.id!==b.id&&a.countryId===b.countryId&&a.type===b.type&&a.body.trim().toLowerCase()===b.body.trim().toLowerCase()&&a.round.trim().toLowerCase()===b.round.trim().toLowerCase();}
export function metric(r:WorldResult|undefined,m:string){if(!r)return null;return m==='share'?r.share:m==='votes'?r.votes:m==='seats'?r.seats:r.electoralVotes;}

export function coalitionEligible(e:WorldElection){return e.type==='parliamentary'&&e.totalSeats!==null&&e.results.some(r=>r.seats!==null)&&!(e.countryId==='us'&&(/senate/i.test(e.body)||e.seriesId?.startsWith('us-senate')||e.id.startsWith('world-us-senate-')))&&!(e.countryId==='cn'&&e.seriesId==='cn-npc');}
