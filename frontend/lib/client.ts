'use client';

let accessToken:string|null = null;
let refreshPromise:Promise<void>|null = null;
let sessionGeneration = 0;
const publicPaths = new Set(['session/login','session/logout','session/refresh']);

function clearAccessToken() {
  sessionGeneration++;
  accessToken = null;
  refreshPromise = null;
}

function expired() {
  clearAccessToken();
  window.location.replace('/giris?oturum=bitti');
}

async function refreshAccessToken() {
  if(refreshPromise) return refreshPromise;
  const generation = sessionGeneration;
  const pending = (async()=>{
    const response = await fetch('/api/session/refresh',{
      method:'POST',credentials:'same-origin',cache:'no-store',
    });
    if(generation !== sessionGeneration) throw new Error('Oturum değişti. Lütfen tekrar deneyin.');
    if(response.status === 401) {
      expired();
      throw new Error('Oturumunuz sona erdi.');
    }
    if(!response.ok) throw new Error('Oturum yenilenemedi. Lütfen tekrar deneyin.');
    const body = await response.json();
    if(generation !== sessionGeneration) throw new Error('Oturum değişti. Lütfen tekrar deneyin.');
    if(typeof body.access_token !== 'string' || !body.access_token) throw new Error('Token yenileme yanıtı geçersiz.');
    accessToken = body.access_token;
  })();
  refreshPromise = pending;
  try {
    await pending;
  } finally {
    if(refreshPromise === pending) refreshPromise = null;
  }
}

export async function api<T>(path:string, init?:RequestInit):Promise<T> {
  const protectedRequest = !publicPaths.has(path);
  if(path === 'session/logout') clearAccessToken();
  let renewed = false;
  if(protectedRequest && !accessToken) {
    await refreshAccessToken();
    renewed = true;
  }
  const generation = sessionGeneration;
  async function send() {
    const headers = new Headers(init?.headers);
    if(protectedRequest && accessToken) headers.set('Authorization','Bearer '+accessToken);
    return fetch('/api/'+path,{...init,headers,credentials:'same-origin',cache:'no-store'});
  }
  const sentToken = accessToken;
  let response = await send();
  if(protectedRequest && response.status === 401 && !renewed) {
    if(generation !== sessionGeneration) throw new Error('Oturum değişti.');
    // Another request may have already replaced the rejected token.
    if(accessToken === sentToken) await refreshAccessToken();
    if(generation !== sessionGeneration) throw new Error('Oturum değişti.');
    response = await send();
  }
  if(protectedRequest && generation !== sessionGeneration) throw new Error('Oturum değişti.');
  if(protectedRequest && response.status === 401) expired();
  const body = await response.json();
  if(response.ok) {
    if(path === 'session/login') {
      if(typeof body.access_token !== 'string' || !body.access_token) throw new Error('Giriş yanıtı geçersiz.');
      clearAccessToken();
      accessToken = body.access_token;
    }
    return body as T;
  }
  const detail = body.detail ?? body.error_description ?? body.message ?? body.error?.message;
  const message = Array.isArray(detail)
    ? detail.map(item=>[item.loc?.at(-1),item.msg].filter(Boolean).join(' — ')).join(' ')
    : typeof detail === 'object' && detail
      ? [detail.message,detail.missing_hours?.join(', ')].filter(Boolean).join(' ')
      : detail;
  throw new Error(message || (response.status===403?'Bu işlem için yetkiniz yok.':'İşlem tamamlanamadı.'));
}
