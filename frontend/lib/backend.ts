import {cookies} from 'next/headers';
import type {Profile} from './contracts';

export const session = 'ges_session';

export async function upstream(path:string, init:RequestInit = {}, token?:string) {
  const headers = new Headers(init.headers);
  if(token) headers.set('Authorization', 'Bearer ' + token);
  return fetch((process.env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '') + path, {
    ...init, headers, cache:'no-store', redirect:'error', signal:AbortSignal.timeout(120000),
  });
}

export async function profile():Promise<Profile|null> {
  const token = (await cookies()).get(session)?.value;
  if(!token) return null;
  const response = await upstream('/auth/users/me', {}, token);
  if(response.status === 401 || response.status === 403) return null;
  if(!response.ok) throw new Error('Kullanıcı bilgileri alınamadı.');
  const {username, full_name, email} = await response.json();
  return {username, full_name, email};
}
