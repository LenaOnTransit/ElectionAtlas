import { getUser } from '../auth';
import { Header, Footer } from '../components';
import Account from './view';

export default async function Page({searchParams}:{searchParams:Promise<{returnTo?:string}>}) {
  const {returnTo} = await searchParams;
  const safe = returnTo?.startsWith('/') && !returnTo.startsWith('//') && !returnTo.includes('\\') ? returnTo : '/account';
  return <><Header/><main className="account"><div className="kicker">THE ELECTION ATLAS</div><h1>Your account</h1><Account user={await getUser()} returnTo={safe}/></main><Footer/></>;
}
