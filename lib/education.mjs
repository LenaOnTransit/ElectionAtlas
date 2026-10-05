export const educationCategories=[
 {id:'elections-voting',name:'Elections & voting',description:'How votes become results: electoral systems, proportional representation, first-past-the-post, runoffs, primaries, preferential voting, thresholds, turnout and ballots.'},
 {id:'maps-districts',name:'Maps & districts',description:'Explore districts, gerrymandering, redistricting, malapportionment, geographic polarization, swing and margins—and why votes and seats can tell different stories.'},
 {id:'parties-ideology',name:'Parties & ideology',description:'Understand political spectra, ideology families, party systems, Overton windows, horseshoe theory and its criticisms, and how parties change over time.'},
 {id:'polling-forecasting',name:'Polling & forecasting',description:'Read polls and probabilities: sampling, margins of error, likely-voter models, house effects, averages, undecideds, MRP, correlated errors and forecast uncertainty.'},
 {id:'government-institutions',name:'Government & institutions',description:'How power is organized: coalitions, minority governments, confidence and supply, parliamentary and presidential systems, bicameralism, courts and federalism.'}
];
export const educationCategory=id=>educationCategories.find(c=>c.id===id);
export const educationalRoute=id=>'/education/'+id;
export function newEducational(id='educational-'+crypto.randomUUID()){
 const now=new Date(),date=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
 return {id,articleType:'educational',educationCategory:'elections-voting',category:'Elections & voting',title:'',summary:'',body:'',sections:[],sources:[],author:'World of Elections',date,status:'draft'};
}
export function readingMinutes(article){const words=[article.body,...(article.sections||[]).map(s=>s.title+' '+s.body)].filter(Boolean).join(' ').trim().split(/\s+/).filter(Boolean).length;return Math.max(1,Math.ceil(words/220));}
export function publicEducation(articles,now=Date.now()){
 return articles.filter(a=>a.articleType==='educational'&&educationCategory(a.educationCategory)&&a.status==='published'&&!a.archived&&(!a.publishAt||Date.parse(a.publishAt)<=now)).sort((a,b)=>(b.date||'').localeCompare(a.date||'')||a.title.localeCompare(b.title));
}
export function validateEducational(a){
 const text=(x,max)=>typeof x==='string'&&x.length<=max,fail=message=>{throw Error(message);};
 if(!a||!['draft','published'].includes(a.status)||a.archived!==undefined&&typeof a.archived!=='boolean'||a.archived===true&&a.status!=='draft'||a.articleType!=='educational'||!text(a.id,100)||!/^educational-[a-zA-Z0-9-]+$/.test(a.id)||!text(a.title,200)||!a.title.trim()||!educationCategory(a.educationCategory)||!text(a.category,100)||!text(a.summary,2000)||!text(a.body,100000)||!text(a.author,200)||!a.author.trim())fail('Check the educational title, category, author and text fields.');
 if(!text(a.date,10)||!/^\d{4}-\d{2}-\d{2}$/.test(a.date)||!Number.isFinite(Date.parse(a.date+'T12:00:00Z'))||new Date(a.date+'T12:00:00Z').toISOString().slice(0,10)!==a.date)fail('Choose a valid article date.');
 if(!Array.isArray(a.sections)||a.sections.length>50)fail('Use at most 50 sections.');
 const ids=new Set();for(const s of a.sections){if(!s||!text(s.id,100)||!s.id||ids.has(s.id)||!text(s.title,200)||!text(s.body,30000)||a.status==='published'&&(!s.title.trim()||!s.body.trim()))fail('Each section needs a unique ID, heading and text.');ids.add(s.id);}
 if(!Array.isArray(a.sources)||a.sources.length>30)fail('Use at most 30 sources.');for(const s of a.sources){if(!s||!text(s.label,300)||!s.label.trim()||!text(s.url,2000))fail('Every source needs a name and HTTPS URL.');let url;try{url=new URL(s.url);}catch{fail('Use a valid HTTPS source URL.');}if(url.protocol!=='https:'||url.username||url.password)fail('Use HTTPS source URLs without credentials.');}
 if(a.status==='published'&&(!a.summary.trim()||!a.body.trim()&&!a.sections.length))fail('Published educationals need a summary and lesson text.');
}
