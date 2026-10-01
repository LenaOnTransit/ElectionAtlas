import {getWorld} from '../../../db/world';import {getSenate} from '../../../db/senate';
export async function GET(){try{return Response.json({data:await getWorld(),senate:await getSenate()},{headers:{'Cache-Control':'no-store'}})}catch{return Response.json({error:'Updates unavailable. Your last loaded figures remain on screen.'},{status:503})}}
