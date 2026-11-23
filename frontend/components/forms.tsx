'use client';
import {useState,type FormEvent} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowRight, CalendarDays, Check, CircuitBoard, Eye, EyeOff, Info, Play, SlidersHorizontal} from 'lucide-react';
import {daily,number,type Envelope,type Hour} from '@/lib/contracts';
import {api} from '@/lib/client';

export function Login({expired}:{expired:boolean}) {
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [visible,setVisible] = useState(false);
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
    <label>Parola<div className="password-field"><input name="password" type={visible?'text':'password'} autoComplete="current-password" required placeholder="Parolanız"/><button type="button" aria-label={visible?'Parolayı gizle':'Parolayı göster'} aria-pressed={visible} onClick={()=>setVisible(value=>!value)}>{visible?<EyeOff size={18}/>:<Eye size={18}/>}</button></div></label>
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
  const [config,setConfig] = useState({inverter_count:3,inverter_ac_rated_kw:900,inverter_dc_rated_kw:1000,ekk_active_power_limit_kw:800});
  const totalAc = config.inverter_count*config.inverter_ac_rated_kw;
  const totalDc = config.inverter_count*config.inverter_dc_rated_kw;
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
  return <div className="simulation-layout">
    <form className="panel simulation-form" onSubmit={submit} aria-busy={busy}>
      <fieldset disabled={busy}>
        <section className="form-section">
          <header><CalendarDays size={20}/><div><h2>Simülasyon günü</h2><p>Hava durumu kayıtlarının kullanılacağı tarihi seçin.</p></div></header>
          <label>Simülasyon tarihi<input type="date" name="simulation_date" required aria-describedby="weather-note"/></label>
          <p id="weather-note" className="field-hint">Günün 24 saati için ışınım ve sıcaklık verisi gerekir.</p>
        </section>
        <section className="form-section">
          <header><CircuitBoard size={20}/><div><h2>İnvertör yapılandırması</h2><p>Nominal güç değerleri her bir invertör için uygulanır.</p></div></header>
          <div className="fields">{fields.slice(0,3).map(([key,label,initial,min,max,step])=><label key={key}>{label}<input name={key} type="number" defaultValue={initial} min={min} max={max} step={step} required onChange={event=>setConfig(previous=>({...previous,[key]:Number(event.target.value)}))}/></label>)}</div>
        </section>
        <section className="form-section">
          <header><SlidersHorizontal size={20}/><div><h2>Şebeke güç sınırı</h2><p>EKK kontrolünde uygulanacak aktif güç limiti.</p></div></header>
          <label>EKK aktif güç limiti (kW)<input name="ekk_active_power_limit_kw" type="number" defaultValue={800} min={0} step="any" required onChange={event=>setConfig(previous=>({...previous,ekk_active_power_limit_kw:Number(event.target.value)}))}/></label>
        </section>
      </fieldset>
      <footer className="form-footer">
        {error && <p role="alert" className="notice danger">{error}</p>}
        <div><p>{busy?'Saatlik sonuçlar hesaplanıyor. Bu işlem tamamlandığında sonuç ekranı açılacak.':'Sonuçlar simülasyon geçmişinize kaydedilir.'}</p><button className="primary" disabled={busy}><Play size={16}/>{busy?'Simülasyon çalışıyor…':'Simülasyonu başlat'}</button></div>
      </footer>
    </form>
    <aside className="configuration-preview">
      <section className="panel plant-summary"><header><h2>Yapılandırma özeti</h2><CircuitBoard size={18}/></header>
        <dl className="parameter-list">
          <div><dt>İnvertör sayısı</dt><dd>{number(config.inverter_count)} <small>adet</small></dd></div>
          <div><dt>Toplam AC kapasite</dt><dd>{number(totalAc)} <small>kW</small></dd></div>
          <div><dt>Toplam DC kapasite</dt><dd>{number(totalDc)} <small>kW</small></dd></div>
          <div><dt>DC / AC oranı</dt><dd>{totalAc>0?number(totalDc/totalAc):'—'}</dd></div>
          <div><dt>EKK güç limiti</dt><dd>{number(config.ekk_active_power_limit_kw)} <small>kW</small></dd></div>
        </dl>
      </section>
      <div className="form-guidance"><Info size={18}/><div><h3>Başlamadan önce</h3><p>Seçilen güne ait hava kayıtları eksikse simülasyon oluşturulamaz.</p><p><Check size={14}/> Parametreler mevcut günlük hesaplama motoruna gönderilir.</p></div></div>
    </aside>
  </div>;
}
