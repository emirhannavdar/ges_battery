import {NextRequest, NextResponse} from 'next/server';
import {refreshSession,sessionOptions,tokenLifetime,upstream} from '@/lib/backend';
import {daily} from '@/lib/contracts';

const options = sessionOptions;
const error = (status:number,detail:string) => NextResponse.json({detail},{
  status,headers:{'Cache-Control':'no-store'},
});
type Context = {params:Promise<{path:string[]}>};

async function handle(request:NextRequest, context:Context) {
  const path = (await context.params).path.join('/');
  const post = request.method === 'POST';
  const origin = process.env.FRONTEND_ORIGIN || request.nextUrl.protocol + '//' + request.headers.get('host');
  const secure = process.env.SESSION_COOKIE_SECURE === 'true' || origin.startsWith('https://');
  if(post && request.headers.get('origin') !== origin) {
    return error(403,'İstek kaynağı doğrulanamadı.');
  }
  // Remove the previous implementation's cookie during migration.
  function clearLegacyCookie(response:NextResponse) {
    response.cookies.set('ges_session','',{...options,secure,maxAge:0});
    return response;
  }

  const clientIp = request.headers.get('x-forwarded-for');

  function backend(path: string, init: RequestInit = {}) {
    const headers = new Headers(init.headers);

    if (clientIp) {
      headers.set('X-Forwarded-For', clientIp);
    }

    return upstream(path, {
      ...init,
      headers,
    });
  }

  try {
    if(post && path === 'session/logout') {
      const result = clearLegacyCookie(NextResponse.json({success:true},{headers:{'Cache-Control':'no-store'}}));
      result.cookies.set(refreshSession,'',{...options,secure,maxAge:0});
      return result;
    }
    if(post && path === 'session/login') {
      const form = await request.formData().catch(()=>null);
      if(!form) return error(422,'Giriş isteği form biçiminde olmalı.');
      const username = form.get('username');
      const password = form.get('password');
      if(typeof username !== 'string' || !username || typeof password !== 'string' || !password) {
        return error(422,'Kullanıcı adı ve parola gerekli.');
      }
      const response = await backend('/auth/token',{method:'POST',body:new URLSearchParams({username,password})});
      const body = await response.json();
      if(!response.ok) return error(response.status,body.error_description ?? body.detail ?? body.message ?? 'Giriş yapılamadı.');
      if(typeof body.access_token !== 'string' || !body.access_token || typeof body.refresh_token !== 'string' || !body.refresh_token) {
        return error(502,'Giriş yanıtı geçersiz.');
      }
      const result = clearLegacyCookie(NextResponse.json({
        access_token:body.access_token,token_type:'bearer',
      },{headers:{'Cache-Control':'no-store'}}));
      result.cookies.set(refreshSession,body.refresh_token,{
        ...options,secure,maxAge:tokenLifetime(body.refresh_token,7*24*60*60),
      });
      return result;
    }
    if(post && path === 'session/refresh') {
      const token = request.cookies.get(refreshSession)?.value;
      if(!token) return clearLegacyCookie(error(401,'Oturumunuz sona erdi.'));
      const response = await backend('/auth/refresh-access-token',{
        method:'POST',headers:{'X-Refresh-Token':token},
      });
      if(!response.ok) {
        const expired = response.status === 401 || response.status === 403;
        const result = clearLegacyCookie(error(expired?401:response.status,
          expired?'Oturumunuz sona erdi. Yeniden giriş yapın.':'Oturum yenilenemedi. Lütfen tekrar deneyin.'));
        if(expired) result.cookies.set(refreshSession,'',{...options,secure,maxAge:0});
        return result;
      }
      const body = await response.json();
      if(typeof body.access_token !== 'string' || !body.access_token) return error(502,'Token yenileme yanıtı geçersiz.');
      return clearLegacyCookie(NextResponse.json({
        access_token:body.access_token,token_type:'bearer',
      },{headers:{'Cache-Control':'no-store'}}));
    }
    const allowed = post ? path === 'inverter/daily'
      : path === 'session/user' || /^inverter\/simulations(?:\/(?:[1-9]\d*|compare))?$/.test(path);
    if(!allowed) return error(404,'İşlem bulunamadı.');
    const authorization = request.headers.get('authorization');
    if(!authorization || !/^Bearer\s+\S+$/i.test(authorization)) {
      return error(401,'Access token gerekli.');
    }
    const init:RequestInit = {headers:{Authorization:authorization}};
    if(post) {
      const parsed = daily.safeParse(await request.json().catch(()=>null));
      if(!parsed.success) return error(422,parsed.error.issues.map(issue=>issue.message).join(' '));
      Object.assign(init,{
        method:'POST',headers:{Authorization:authorization,'Content-Type':'application/json'},
        body:JSON.stringify(parsed.data),
      });
    }
    const target = path === 'session/user' ? '/auth/users/me' : '/' + path + request.nextUrl.search;
    const response = await backend(target,init);
    let body = await response.json().catch(()=>({detail:'Sunucudan geçerli yanıt alınamadı.'}));
    if(path === 'session/user' && response.ok) {
      const {username,full_name,email} = body;
      body = {username,full_name,email};
    }
    return NextResponse.json(body,{status:response.status,headers:{'Cache-Control':'no-store'}});
  } catch {
    return error(502,'FastAPI bağlantısı kurulamadı veya yanıt zaman aşımına uğradı.');
  }
}
export {handle as GET, handle as POST};
