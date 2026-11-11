import {redirect} from 'next/navigation';
import {profile} from '@/lib/backend';
import {Shell} from '@/components/shell';

export default async function Layout({children}:{children:React.ReactNode}) {
  const user = await profile();
  if(!user) redirect('/giris');
  return <Shell user={user}>{children}</Shell>;
}
