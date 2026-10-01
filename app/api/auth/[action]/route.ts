import { cookies } from 'next/headers';
import { SESSION_COOKIE } from '../../../auth';
import { createSession, deleteSession, login, register, limit, normalizeEmail, SESSION_AGE } from '../../../../lib/auth-core.mjs';
export const runtime = 'nodejs';
export async function POST(request:Request, context:{params:Promise<{action:string}>}) {
  const {action} = await context.params;
  const configured = process.env.APP_ORIGIN;
  if (process.env.NODE_ENV === 'production' && !configured) return Response.json({error:'Account service is not configured.'},{status:503});
  const expected = configured || new URL(request.url).origin;
  if (request.headers.get('origin') !== expected) return Response.json({error:'Invalid request origin.'},{status:403});
  if (!['login','register','logout'].includes(action)) return Response.json({error:'Not found.'},{status:404});
  const jar = await cookies();
  if (action === 'logout') {
    deleteSession(jar.get(SESSION_COOKIE)?.value);
    jar.set(SESSION_COOKIE,'',{httpOnly:true,sameSite:'strict',secure:process.env.NODE_ENV==='production',path:'/',maxAge:0});
    return Response.json({ok:true});
  }
  if (!request.headers.get('content-type')?.startsWith('application/json')) return Response.json({error:'JSON required.'},{status:415});
  try {
    const raw = await request.text();
    if (raw.length > 4096) return Response.json({error:'Request too large.'},{status:413});
    const input = JSON.parse(raw);
    if (!input || typeof input.email !== 'string' || typeof input.password !== 'string' || input.email.length > 254 || input.password.length > 128) throw Error('Enter your email and password.');
    if (!limit('global:'+action,action==='register'?30:300) || !limit(action+':'+normalizeEmail(input.email),action==='register'?5:10)) return Response.json({error:'Too many attempts. Try again in 15 minutes.'},{status:429,headers:{'Retry-After':'900'}});
    const user = action === 'register' ? await register(input) : await login(input.email,input.password);
    deleteSession(jar.get(SESSION_COOKIE)?.value);
    jar.set(SESSION_COOKIE,createSession(user.userId),{httpOnly:true,sameSite:'strict',secure:process.env.NODE_ENV==='production',path:'/',maxAge:SESSION_AGE});
    return Response.json({user},{headers:{'Cache-Control':'no-store'}});
  } catch (error) {
    const message = error instanceof Error ? error.message : '';
    const allowed = /^(Enter a valid|Username must|Password must|That email|Email or password|Enter your email)/.test(message);
    return Response.json({error:allowed?message:'Could not complete this request. Please try again.'},{status:400});
  }
}
