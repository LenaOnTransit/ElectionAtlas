// This controls visibility only. Editor pages and Supabase still enforce access.
export function createModeratorAccess(resolve:()=>Promise<{role:string}|null>,publish:(allowed:boolean)=>void){
 let revision=0,active=true;
 return {
  async refresh(){
   const current=++revision;if(!active)return;publish(false);
   try{const user=await resolve();if(active&&current===revision)publish(user?.role==='admin');}
   catch{if(active&&current===revision)publish(false);}
  },
  invalidate(){revision++;if(active)publish(false);},
  dispose(){revision++;active=false;}
 };
}
