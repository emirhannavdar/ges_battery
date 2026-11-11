import {NextRequest, NextResponse} from 'next/server';
import {session, upstream} from '@/lib/backend';
import {daily} from '@/lib/contracts';

const error = (status:number, detail:string) => NextResponse.json({detail},{status});
const options = {httpOnly:true, sameSite:'lax', path:'/'} as const;
type Context = {params:Promise<{path:string[]}>};

async function handle(request:NextRequest, context:Context) {
  const path = (await context.params).path.join('/');
  const post = request.method === 'POST';
  const origin = process.env.FRONTEND_ORIGIN || request.nextUrl.protocol + '//' + request.headers.get('host');
  const secure = process.env.SESSION_COOKIE_SECURE === 'true' || origin.startsWith('https://');
  if(post && request.headers.get('origin') !== origin) {
    return error(403,'İstek kaynağı doğrulanamadı.');
  }
  try {
    if(post && path === 'session/logout') {
      const result = NextResponse.json({success:true});
      result.cookies.set(session,'',{...options, secure, maxAge:0});
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
      const response = await upstream('/auth/token', {method:'POST',body:new URLSearchParams({username,password})});
      const body = await response.json();
      if(!response.ok) return NextResponse.json(body,{status:response.status});
      if(typeof body.access_token !== 'string') return error(502,'Giriş yanıtı geçersiz.');
      const result = NextResponse.json({username:body.username});
      result.cookies.set(session,body.access_token,{...options,secure,maxAge:1800});
      return result;
    }
    const allowed = post ? path === 'inverter/daily' : /^inverter\/simulations(?:\/(?:[1-9]\d*|compare))?$/.test(path);
    if(!allowed) return error(404,'İşlem bulunamadı.');
    const token = request.cookies.get(session)?.value;
    if(!token) return error(401,'Oturumunuz sona erdi.');
    const init:RequestInit = {};
    if(post) {
      const parsed = daily.safeParse(await request.json().catch(()=>null));
      if(!parsed.success) return error(422,parsed.error.issues.map(issue=>issue.message).join(' '));
      Object.assign(init,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(parsed.data)});
    }
    const response = await upstream('/' + path + request.nextUrl.search,init,token);
    const body = await response.json().catch(()=>({detail:'Sunucudan geçerli yanıt alınamadı.'}));
    const result = NextResponse.json(body,{status:response.status, headers:{'Cache-Control':'no-store'}});
    if(response.status === 401) result.cookies.set(session,'',{...options,secure,maxAge:0});
    return result;
  } catch {
    return error(502,'FastAPI bağlantısı kurulamadı veya yanıt zaman aşımına uğradı.');
  }
}
export {handle as GET, handle as POST};
