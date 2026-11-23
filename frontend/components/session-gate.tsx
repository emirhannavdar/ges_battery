'use client';

import type {Profile} from '@/lib/contracts';
import {api} from '@/lib/client';
import {Failure,Loading,useLoad} from './data';
import {Shell} from './shell';

const loadProfile = () => api<Profile>('session/user');

export function SessionGate({children}:{children:React.ReactNode}) {
  const query = useLoad(loadProfile);
  if(query.error) {
    return <main className="standalone"><Failure message={query.error} retry={query.retry}/></main>;
  }
  if(!query.data) {
    return <main className="standalone"><Loading/></main>;
  }
  return <Shell user={query.data}>{children}</Shell>;
}
