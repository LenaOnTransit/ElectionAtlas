import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { sessionUser } from '../lib/auth-core.mjs';
export const SESSION_COOKIE = 'electionatlas_session';
export async function getUser() { return sessionUser((await cookies()).get(SESSION_COOKIE)?.value); }
export async function requireUser(returnTo: string) {
  const user = await getUser();
  if (!user) redirect('/account?returnTo='+encodeURIComponent(returnTo));
  return user;
}
