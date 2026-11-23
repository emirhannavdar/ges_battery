export const refreshSession = 'ges_refresh';
export const sessionOptions = {httpOnly:true, sameSite:'lax', path:'/'} as const;

export function tokenLifetime(token:string, fallback:number) {
  try {
    const {exp} = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    if(typeof exp === 'number' && Number.isFinite(exp)) {
      return Math.max(0,Math.floor(exp-Date.now()/1000));
    }
  } catch {}
  return fallback;
}

export async function upstream(path:string, init:RequestInit = {}) {
  return fetch((process.env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '') + path,{
    ...init,cache:'no-store',redirect:'error',signal:AbortSignal.timeout(120000),
  });
}
