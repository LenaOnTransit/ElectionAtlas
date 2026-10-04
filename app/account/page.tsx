import { getUser } from '../auth';
import { Header, Footer } from '../components';
import Account from './view';

export default async function Page({searchParams}:{searchParams:Promise<{returnTo?:string}>}) {
  const {returnTo} = await searchParams;
  const safe = returnTo?.startsWith('/') && !returnTo.startsWith('//') && !returnTo.includes('\\') ? returnTo : '/account';
  return <><Header/><main className="account"><div className="kicker">WORLD OF ELECTIONS</div><h1>Your account</h1><Account user={await getUser()} returnTo={safe}/><section className="account-privacy"><h2>Privacy requests</h2><p>For personal-data erasure, data portability, or a direct transfer to another controller, contact our privacy team at <a href="mailto:worldofelections@gmail.com">worldofelections@gmail.com</a>. You do not need an account to make a request.</p></section></main><Footer/></>;
}
