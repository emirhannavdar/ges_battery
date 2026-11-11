'use client';
import Link from 'next/link';
import {useCallback,useEffect,useState} from 'react';
import {Activity, CalendarDays, ChevronLeft, CircuitBoard, Gauge, PlugZap, TrendingDown, Zap} from 'lucide-react';
import {date,number,type Detail,type Hour} from '@/lib/contracts';
import {Chart,type Series} from './chart';
import {detail,Empty,Failure,list,Loading,useLoad} from './data';
import {NewLink} from './shell';

export const energy = [
  ['total_inverter_energy_kwh','İnvertör enerjisi','amber',Zap],
  ['total_grid_energy_kwh','Şebeke enerjisi','green',PlugZap],
  ['total_transformer_loss_kwh','Trafo kaybı','blue',Activity],
  ['total_curtailed_energy_kwh','Kısılan enerji','red',TrendingDown],
] as const;

export function Dashboard() {
  const query = useLoad(latest);
  return <><header className="page-head"><div><h1>Üretim genel bakışı</h1><p>En son kaydedilen günlük simülasyon.</p></div><NewLink/></header>
    {query.error ? <Failure message={query.error} retry={query.retry}/> : query.data === undefined ? <Loading/> : query.data ? <Overview run={query.data}/> : <Empty/>}</>;
}
async function latest() {
  const [first] = await list();
  return first ? detail(first.id) : null;
}

export function Results({id}:{id:string}) {
  const load = useCallback(()=>detail(id),[id]);
  const query = useLoad(load);
  const [created,setCreated] = useState(false);
  useEffect(()=>{
    try {
      if(sessionStorage.getItem('ges-created') !== id) return;
      sessionStorage.removeItem('ges-created');
      const show = setTimeout(()=>setCreated(true),0);
      const hide = setTimeout(()=>setCreated(false),5000);
      return ()=>{clearTimeout(show);clearTimeout(hide);};
    } catch {}
  },[id]);
  return <><Link href="/gecmis" className="back"><ChevronLeft size={17}/> Simülasyon geçmişi</Link>
    <header className="page-head"><div><h1>Simülasyon #{id}</h1><p>Kaydedilen günlük üretim ve şebeke sonuçları.</p></div><NewLink/></header>
    {created && <div className="toast" role="status">Simülasyon kaydedildi.</div>}
    {query.error ? <Failure message={query.error} retry={query.retry}/> : query.data ? <Overview run={query.data} details/> : <Loading/>}</>;
}

function Overview({run,details=false}:{run:Detail;details?:boolean}) {
  const hours = run.hourly_results.map(hour=>hour.hour.slice(0,5));
  function line(key:keyof Hour,name:string,tone:Series['tone']):Series {
    return {name,tone,values:run.hourly_results.map(hour=>typeof hour[key]==='number'?hour[key]:null)};
  }
  const hasCurtailment = run.hourly_results.length>0 && run.hourly_results.every(hour=>hour.available_active_power_kw !== undefined && hour.curtailed_power_kw !== undefined);
  return <>
    <div className="run-strip"><span><CalendarDays size={16}/>{date(run.simulation_date)}</span><Link href={'/sonuclar/'+run.id}>Kayıt #{run.id}</Link><span>{run.processed_hours} saat işlendi</span></div>
    <div className="metrics">
      {energy.map(([key,label,tone,Icon])=><Metric key={key} icon={Icon} label={label} value={run[key]} unit="kWh" tone={tone}/>)}
      <Metric icon={CircuitBoard} label="İnvertör sayısı" value={run.inverter_count} unit="adet" tone="blue"/>
      <Metric icon={Gauge} label="EKK güç limiti" value={run.ekk_active_power_limit_kw} unit="kW" tone="amber"/>
    </div>
    {details && <section className="panel settings"><h2>İnvertör yapılandırması</h2><dl className="facts"><div><dt>AC nominal güç</dt><dd>{number(run.inverter_ac_rated_kw)} kW</dd></div><div><dt>DC nominal güç</dt><dd>{number(run.inverter_dc_rated_kw)} kW</dd></div><div><dt>Trafo verimi</dt><dd>%{number(run.transformer_efficiency*100)}</dd></div></dl></section>}
    <Chart title="Saatlik aktif güç" unit="kW" hours={hours} series={[line('inverter_power_kw','İnvertör','amber'),line('grid_power_kw','Şebeke','green')]}/>
    {hasCurtailment ? <Chart title="Kullanılabilir ve kısılan güç" unit="kW" hours={hours} series={[line('available_active_power_kw','Kullanılabilir güç','amber'),line('curtailed_power_kw','Kısılan güç','red')]}/> : <p className="notice">Kayıt detayında saatlik kullanılabilir ve kısılan güç serisi sunulmuyor.</p>}
    <div className="chart-grid"><Chart title="Güneş ışınımı" unit="W/m²" hours={hours} series={[line('irradiance_w_m2','Işınım','amber')]}/><Chart title="Ortam sıcaklığı" unit="°C" hours={hours} series={[line('ambient_temperature_c','Sıcaklık','blue')]}/></div>
    {details && <section className="panel table-panel"><h2>Saatlik kayıtlar</h2><div className="table-scroll" tabIndex={0} aria-label="Saatlik sonuç tablosu"><table><thead><tr>{['Saat','İnvertör (kW)','Şebeke (kW)','Trafo kaybı (kW)','Işınım (W/m²)','Sıcaklık (°C)','EKK limit aşımı'].map(label=><th key={label} scope="col">{label}</th>)}</tr></thead><tbody>{run.hourly_results.map(hour=><tr key={hour.hour}><th scope="row">{hour.hour.slice(0,5)}</th>{[hour.inverter_power_kw,hour.grid_power_kw,hour.transformer_loss_kw,hour.irradiance_w_m2,hour.ambient_temperature_c].map((value,index)=><td key={index}>{number(value)}</td>)}<td className={hour.ekk_limit_exceeded?'red':''}>{hour.ekk_limit_exceeded?'Var':'Yok'}</td></tr>)}</tbody></table></div></section>}
  </>;
}

function Metric({icon:Icon,label,value,unit,tone}:{icon:typeof Zap;label:string;value:number;unit:string;tone:string}) {
  return <article className="panel metric"><span className={tone}><Icon size={18}/></span><h2>{label}</h2><div><strong>{number(value)}</strong> <small>{unit}</small></div></article>;
}
