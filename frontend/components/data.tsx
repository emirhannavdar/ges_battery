'use client';
import {useEffect,useState} from 'react';
import {Database, TriangleAlert} from 'lucide-react';
import {api} from '@/lib/client';
import {type Detail,type Envelope,type Summary,type Hour} from '@/lib/contracts';
import {NewLink} from './shell';

export function list() {
  return api<Envelope<{count:number;simulations:Summary[]}>>('inverter/simulations').then(result=>result.data.simulations);
}
export async function detail(id:number|string) {
  const {data} = await api<Envelope<Detail>>('inverter/simulations/' + id);
  try {
    const saved = sessionStorage.getItem('ges-hours-' + id);
    if(!saved) return data;
    const hours:Hour[] = JSON.parse(saved);
    const byHour = new Map(hours.map(hour=>[hour.hour,hour]));
    return {...data,hourly_results:data.hourly_results.map(hour=>({...byHour.get(hour.hour.slice(0,5)),...hour}))};
  } catch {
    return data;
  }
}

export function useLoad<T>(load:()=>Promise<T>) {
  const [result,setResult] = useState<{load:typeof load; data?:T; error?:string}>();
  const [attempt,retry] = useState(0);
  useEffect(()=>{
    let active = true;
    load().then(data=>{if(active) setResult({load,data});},err=>{
      if(active) setResult({load,error:err.message});
    });
    return ()=>{active=false;};
  },[load,attempt]);
  return {...(result?.load === load ? result : undefined),retry:()=>{setResult(undefined);retry(value=>value+1);}};
}

export function Loading() {
  return <div className="loading-grid" role="status" aria-label="Simülasyon verileri yükleniyor"><div className="skeleton"/><div className="skeleton"/><div className="skeleton"/></div>;
}
export function Failure({message,retry}:{message:string;retry:()=>void}) {
  return <section className="panel empty"><TriangleAlert size={28}/><h2>Veriler alınamadı</h2><p role="alert">{message}</p><button className="secondary" onClick={retry}>Yeniden dene</button></section>;
}
export function Empty({comparison=false}:{comparison?:boolean}) {
  return <section className="panel empty"><Database size={30}/><h2>{comparison?'İki kayıt gerekiyor':'Henüz simülasyon yok'}</h2><p>{comparison?'Karşılaştırmak için en az iki günlük simülasyon oluşturun.':'İlk günlük simülasyonunuzu çalıştırarak üretim ve şebeke verilerini görüntüleyin.'}</p><NewLink/></section>;
}
