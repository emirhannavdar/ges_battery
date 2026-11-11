'use client';
import {useState,type FormEvent} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowRight, Play, SlidersHorizontal} from 'lucide-react';
import {daily,type Envelope,type Hour} from '@/lib/contracts';
import {api} from '@/lib/client';

export function Login({expired}:{expired:boolean}) {
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const form = new FormData(event.currentTarget);
      await api('session/login',{method:'POST',body:new URLSearchParams({
        username:String(form.get('username')),password:String(form.get('password')),
      })});
      window.location.replace('/');
    } catch(err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }
  return <form className="login-form" method="post" action="/api/session/login" onSubmit={submit}>
    <h2>Oturum aç</h2><p>Simülasyon çalışma alanınıza giriş yapın.</p>
    {expired && <p role="status" className="notice">Oturumunuz sona erdi. Yeniden giriş yapın.</p>}
    <label>Kullanıcı adı<input name="username" autoComplete="username" required placeholder="Kullanıcı adınız"/></label>
    <label>Parola<input name="password" type="password" autoComplete="current-password" required placeholder="Parolanız"/></label>
    {error && <p role="alert" className="notice danger">{error}</p>}
    <button className="primary" disabled={busy}>{busy?'Giriş yapılıyor…':'Giriş yap'}<ArrowRight size={18}/></button>
  </form>;
}

const fields = [
  ['inverter_count','İnvertör sayısı',3,'1','100','1'],
  ['inverter_ac_rated_kw','İnvertör AC nominal gücü (kW)',900,'0',undefined,'any'],
  ['inverter_dc_rated_kw','İnvertör DC nominal gücü (kW)',1000,'0',undefined,'any'],
  ['ekk_active_power_limit_kw','EKK aktif güç limiti (kW)',800,'0',undefined,'any'],
] as const;

export function SimulationForm() {
  const router = useRouter();
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const parsed = daily.safeParse({
      simulation_date:values.get('simulation_date'),
      ...Object.fromEntries(fields.map(([key])=>[key,Number(values.get(key))])),
    });
    if(!parsed.success) {
      setError(parsed.error.issues[0]?.path[0] === 'simulation_date' ? 'Geçerli bir tarih seçin.' : 'İnvertör sayısı 1–100 arasında tam sayı olmalı. AC ve DC gücü pozitif, EKK limiti sıfır veya pozitif olmalı.');
      return;
    }
    setError('');
    setBusy(true);
    try {
      const {data} = await api<Envelope<{simulation_id:number;hourly_results:Hour[]}>>('inverter/daily',{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(parsed.data),
      });
      try {
        sessionStorage.setItem('ges-hours-' + data.simulation_id,JSON.stringify(data.hourly_results));
        sessionStorage.setItem('ges-created',String(data.simulation_id));
      } catch {
        // Storage restrictions must not hide a successful saved run.
      }
      router.push('/sonuclar/' + data.simulation_id);
    } catch(err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }
  return <form className="panel settings" onSubmit={submit}>
    <h2><SlidersHorizontal size={19}/> Santral yapılandırması</h2>
    <fieldset disabled={busy} className="fields">
      <label>Simülasyon tarihi<input type="date" name="simulation_date" required/></label>
      {fields.map(([key,label,initial,min,max,step])=><label key={key}>{label}<input name={key} type="number" defaultValue={initial} min={min} max={max} step={step} required/></label>)}
    </fieldset>
    <p className="muted">Seçilen günün her saati için ışınım ve sıcaklık kaydı gerekir.</p>
    {error && <p role="alert" className="notice danger">{error}</p>}
    <button className="primary" disabled={busy}><Play size={16}/>{busy?'Simülasyon çalışıyor…':'Simülasyonu başlat'}</button>
  </form>;
}
