import {useEffect,useState} from 'react';
import ElectionGeography from './view';
import {validateGeographyDataset,type GeographyDataset} from '../../lib/election-geography.mjs';

// Native engine datasets load directly. Legacy assets may supply an adapter.
export default function GeographyLoader({asset,title,initialElectionId,adapt=validateGeographyDataset}:{asset:string;title:string;initialElectionId?:string;adapt?:(source:unknown)=>GeographyDataset}){
 const [data,setData]=useState<GeographyDataset|null>(null),[error,setError]=useState('');
 useEffect(()=>{setData(null);setError('');const controller=new AbortController();fetch(import.meta.env.BASE_URL+asset,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json();}).then(source=>setData(validateGeographyDataset(adapt(source)))).catch(e=>{if(e.name!=='AbortError')setError('Election geography results are temporarily unavailable. Please reload to try again.');});return()=>controller.abort();},[asset,adapt]);
 if(!data)return <main className="world-main"><h1>{title}</h1><p role="status">{error||'Loading official area results…'}</p>{error&&<button onClick={()=>window.location.reload()}>Retry</button>}</main>;
 return <ElectionGeography key={data.id} data={data} initialElectionId={initialElectionId}/>;
}
