import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {setTimeout as delay} from 'node:timers/promises';
import puppeteer from 'puppeteer-core';

const hour = {
  hour:'12:00', irradiance_w_m2:700, ambient_temperature_c:24, inverter_power_kw:810,
  grid_power_kw:800, transformer_loss_kw:10, ekk_limit_exceeded:false,
};
const rows = [2,1].map(id=>({
  id, simulation_date:'2026-04-0'+id, created_at:'2026-04-04T12:00:00',
  inverter_count:3, processed_hours:24, total_inverter_energy_kwh:9000+id,
  total_grid_energy_kwh:8000+id, total_transformer_loss_kwh:1000,
}));
const details = rows.map(row=>({
  ...row, total_curtailed_energy_kwh:200, inverter_ac_rated_kw:900, inverter_dc_rated_kw:1000,
  ekk_active_power_limit_kw:800, transformer_efficiency:.988, hourly_results:[hour],
}));
const authToken = 'smoke-test-token';
let allowToken = true;
const paths = new Set();
const fixture = createServer(async (request,response)=>{
  const url = new URL(request.url,'http://localhost');
  const path = url.pathname;
  paths.add(path);
  const send = (status,body)=>response.writeHead(status,{'Content-Type':'application/json'}).end(JSON.stringify(body));
  const ok = data=>send(200,{success:true,data});
  const chunks = [];
  for await(const chunk of request) chunks.push(chunk);
  const body = Buffer.concat(chunks).toString();
  if(path === '/auth/token'){
    const form = new URLSearchParams(body);
    return request.headers['content-type']?.startsWith('application/x-www-form-urlencoded') && form.get('username')==='operator' && form.get('password')==='test-only'
      ? send(200,{access_token:authToken,username:'operator',token_type:'bearer'})
      : send(401,{error_description:'Şifre yanlış'});
  }
  if(!allowToken || request.headers.authorization !== 'Bearer '+authToken) return send(401,{detail:'Oturum geçersiz'});
  if(path === '/auth/users/me') return send(200,{username:'operator',full_name:'Test Operatörü',email:null,access_token:authToken});
  if(path === '/inverter/simulations') return ok({count:2,simulations:rows});
  if(path === '/inverter/simulations/compare') {
    if(url.searchParams.get('simulation_id_1')!=='1' || url.searchParams.get('simulation_id_2')!=='2') return send(422,{detail:'Beklenmeyen senaryo'});
    return ok({scenario_1:{id:1},scenario_2:{id:2},comparison:{grid_energy_difference_kwh:1,grid_energy_change_percent:.01,same_weather_date:false}});
  }
  if(path === '/inverter/daily'){
    const values = JSON.parse(body);
    if(values.simulation_date === '2026-04-03') return send(422,{detail:{message:'24 saatlik veri eksik.',missing_hours:['00:00']}});
    if(values.simulation_date !== '2026-04-02' || values.inverter_count !== 3 || values.inverter_ac_rated_kw !== 900 || values.inverter_dc_rated_kw !== 1000 || values.ekk_active_power_limit_kw !== 800) return send(422,{detail:'Beklenmeyen parametre'});
    return ok({simulation_id:2,hourly_results:[{...hour,available_active_power_kw:950,curtailed_power_kw:140}]});
  }
  const found = details.find(row=>path==='/inverter/simulations/'+row.id);
  return found ? ok(found) : send(404,{detail:'Kayıt bulunamadı'});
});

const chrome = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
assert.ok(existsSync(chrome),'Set CHROME_PATH to an installed Chrome or Chromium executable');
await new Promise(resolve=>fixture.listen(0,'127.0.0.1',resolve));
const origin = 'http://127.0.0.1:'+(process.env.SMOKE_PORT || '3219');
const app = spawn(process.execPath,['node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port',new URL(origin).port],{
  stdio:'inherit',env:{...process.env,BACKEND_URL:'http://127.0.0.1:'+fixture.address().port,NEXT_TELEMETRY_DISABLED:'1'},
});
let browser;
try {
  let ready = false;
  for(let attempt=0;attempt<60 && !ready;attempt++){
    ready = await fetch(origin+'/giris').then(response=>response.ok).catch(()=>false);
    if(!ready) await delay(500);
  }
  assert.ok(ready,'Production server failed to start');
  browser = await puppeteer.launch({executablePath:chrome,headless:true});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror',error=>errors.push(error.message));
  const contains = async text=>{
    try {
      await page.waitForFunction(value=>document.body.innerText.includes(value),{timeout:10000},text);
    } catch(error) {
      const visible = await page.evaluate(()=>document.body.innerText.slice(0,500));
      throw new Error('Expected '+text+' at '+page.url()+', got '+visible,{cause:error});
    }
  };
  const go = route=>page.goto(origin+route);
  const post = (path,body)=>page.evaluate(async (path,body)=>{
    const response=await fetch('/api/'+path,{method:'POST',body});
    return {status:response.status,body:await response.json()};
  },path,body);
  await go('/');
  assert.equal(new URL(page.url()).pathname,'/giris');
  await page.type('[name=username]','operator');
  await page.type('[name=password]','wrong');
  await page.click('.login-form button');
  await contains('Şifre yanlış');
  await page.$eval('[name=password]',input=>{input.value='';});
  await page.type('[name=password]','test-only');
  await Promise.all([page.waitForNavigation(),page.click('.login-form button')]);
  await contains('Test Operatörü');
  await contains('8.002');
  assert.equal(await page.evaluate(()=>document.cookie.includes('ges_session')),false);
  const cookie = (await browser.defaultBrowserContext().cookies()).find(item=>item.name==='ges_session');
  assert.ok(cookie?.httpOnly);
  assert.equal(cookie.sameSite,'Lax');
  for(const width of [375,768,1440]){
    await page.setViewport({width,height:850});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  }
  await go('/gecmis');
  await contains('8.001');
  await page.type('.search input','1');
  await page.waitForFunction(()=>document.querySelectorAll('tbody tr').length===1);
  await go('/karsilastir');
  await page.waitForSelector('[name=a]');
  await page.select('[name=a]','1');
  await page.select('[name=b]','2');
  await page.click('form button');
  await contains('Senaryo özeti');
  await contains('Simülasyon tarihleri farklı.');
  await go('/yeni');
  await page.$eval('[name=simulation_date]',input=>{input.value='2026-04-03';});
  await page.click('form button');
  await contains('24 saatlik veri eksik.');
  await page.$eval('[name=simulation_date]',input=>{input.value='2026-04-02';});
  await page.click('form button');
  await contains('Kullanılabilir ve kısılan güç');
  assert.equal(new URL(page.url()).pathname,'/sonuclar/2');
  await page.click('button[aria-label="Çıkış yap"]');
  await page.waitForSelector('.login-form');
  assert.equal((await post('inverter/daily','{}')).status,401);
  assert.ok(paths.has('/inverter/daily'));
  const login = await post('session/login','username=operator&password=test-only');
  // The login route requires a form content type, so log in again through the UI.
  assert.notEqual(login.status,200);
  await page.type('[name=username]','operator');
  await page.type('[name=password]','test-only');
  await Promise.all([page.waitForNavigation(),page.click('.login-form button')]);
  allowToken = false;
  await page.evaluate(()=>fetch('/api/inverter/simulations'));
  const session = (await browser.defaultBrowserContext().cookies()).find(item=>item.name==='ges_session');
  assert.equal(session,undefined);
  assert.deepEqual(errors,[]);
  console.log('Smoke passed: protected routes, login, HttpOnly session, history, comparison, daily validation/save, logout, expired token, responsive widths.');
} finally {
  await browser?.close();
  app.kill();
  fixture.close();
}

