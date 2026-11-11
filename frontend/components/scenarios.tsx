'use client';
import Link from 'next/link';
import {useCallback,useMemo,useState,type FormEvent} from 'react';
import {ArrowUpRight, GitCompareArrows, Search} from 'lucide-react';
import {api} from '@/lib/client';
import {date,number,type Comparison,type Detail,type Envelope,type Summary} from '@/lib/contracts';
import {Chart,type Series} from './chart';
import {detail,Empty,Failure,list,Loading,useLoad} from './data';
import {energy} from './results';
import {NewLink} from './shell';

async function history() {
  const rows = await list();
  const output: {row:Summary; details?:Detail}[] = [];
  for(let offset=0; offset<rows.length; offset+=6) {
    const batch = rows.slice(offset,offset+6);
    const results = await Promise.allSettled(batch.map(row=>detail(row.id)));
    results.forEach((result,index)=>output.push({row:batch[index],details:result.status==='fulfilled'?result.value:undefined}));
  }
  return output;
}

export function History() {
  const query = useLoad(history);
  const [search,setSearch] = useState('');
  const [day,setDay] = useState('');
  const [order,setOrder] = useState('newest');
  const rows = useMemo(()=>query.data?.filter(({row})=>
    (!day || row.simulation_date===day) && [String(row.id),row.simulation_date,date(row.simulation_date)].some(value=>value.includes(search.trim().replace(/^#/,''))),
  ).sort((a,b)=>(order==='newest'?-1:1)*(a.row.simulation_date.localeCompare(b.row.simulation_date) || a.row.id-b.row.id)),[query.data,search,day,order]);
  return <><header className="page-head"><div><h1>Simülasyon geçmişi</h1><p>Kaydedilen günlük simülasyonları inceleyin.</p></div><NewLink/></header>
  {query.error ? <Failure message={query.error} retry={query.retry}/> : !rows ? <Loading/> : !query.data?.length ? <Empty/> : <section className="panel table-panel">
    <div className="filters"><label>Simülasyon ara<div className="search"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="ID veya tarih"/></div></label>
      <label>Simülasyon tarihi<input type="date" value={day} onChange={e=>setDay(e.target.value)}/></label>
      <label>Sıralama<select value={order} onChange={e=>setOrder(e.target.value)}><option value="newest">Yeni tarih önce</option><option value="oldest">Eski tarih önce</option></select></label>
    </div>
    {rows.length ? <div className="table-scroll" tabIndex={0} aria-label="Simülasyon kayıtları"><table><thead><tr>{['Kayıt','Tarih','İnvertör','EKK (kW)','Üretim (kWh)','Şebeke (kWh)','Kısılan (kWh)','Detay'].map(label=><th scope="col" key={label}>{label}</th>)}</tr></thead>
      <tbody>{rows.map(({row,details})=><tr key={row.id}><th scope="row">#{row.id}</th><td>{date(row.simulation_date)}</td><td>{row.inverter_count}</td><td>{details?number(details.ekk_active_power_limit_kw):'—'}</td><td>{number(row.total_inverter_energy_kwh)}</td><td>{number(row.total_grid_energy_kwh)}</td><td>{details?number(details.total_curtailed_energy_kwh):'—'}</td><td><Link href={'/sonuclar/'+row.id} aria-label={'Simülasyon '+row.id+' detayını görüntüle'} className="icon-button"><ArrowUpRight size={17}/></Link></td></tr>)}</tbody></table></div> : <p className="notice">Filtrelerle eşleşen kayıt bulunamadı.</p>}
    {rows.some(row=>!row.details) && <p className="notice">Bazı kayıtların EKK ve kısılan enerji bilgileri yüklenemedi. <button className="secondary" onClick={query.retry}>Yeniden dene</button></p>}
  </section>}</>;
}

export function Compare() {
  const query = useLoad(list);
  const [ids,setIds] = useState<[string,string]>();
  const [error,setError] = useState('');
  function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const a = String(form.get('a')), b = String(form.get('b'));
    if(a===b){setError('İki farklı simülasyon seçmelisiniz.');return;}
    setError('');
    setIds([a,b]);
  }
  return <><header className="page-head"><div><h1>Senaryo karşılaştırma</h1><p>İki simülasyonun yapılandırmasını, hava koşullarını ve enerji sonuçlarını inceleyin.</p></div></header>
    {query.error ? <Failure message={query.error} retry={query.retry}/> : !query.data ? <Loading/> : query.data.length<2 ? <Empty comparison/> : <form className="panel settings" onSubmit={submit}><div className="fields">{[['a','Referans senaryo'],['b','Karşılaştırılan senaryo']].map(([key,label])=><label key={key}>{label}<select name={key} required defaultValue=""><option value="" disabled>Simülasyon seçin</option>{query.data?.map(row=><option key={row.id} value={row.id}>#{row.id} ({date(row.simulation_date)})</option>)}</select></label>)}</div>{error && <p className="notice danger" role="alert">{error}</p>}<button className="primary"><GitCompareArrows size={16}/> Karşılaştır</button></form>}
    {ids && <ComparisonResults ids={ids}/>}</>;
}

function ComparisonResults({ids:[a,b]}:{ids:[string,string]}) {
  const load = useCallback(async()=>{
    const {data} = await api<Envelope<Comparison>>('inverter/simulations/compare?'+new URLSearchParams({simulation_id_1:a,simulation_id_2:b}));
    const runs = await Promise.all([detail(data.scenario_1.id),detail(data.scenario_2.id)]);
    return {runs,delta:data.comparison};
  },[a,b]);
  const query = useLoad(load);
  if(query.error) return <Failure message={query.error} retry={query.retry}/>;
  if(!query.data) return <Loading/>;
  const {runs,delta} = query.data;
  const hours = Array.from(new Set(runs.flatMap(run=>run.hourly_results.map(hour=>hour.hour.slice(0,5))))).sort();
  function series(key:'grid_power_kw'|'inverter_power_kw'|'irradiance_w_m2'|'ambient_temperature_c'):Series[] {
    return runs.map((run,index)=>{
      const values = new Map(run.hourly_results.map(hour=>[hour.hour.slice(0,5),hour[key]]));
      return {name:'#'+run.id,tone:index?'green':'amber',values:hours.map(hour=>values.get(hour)??null)};
    });
  }
  const metrics:[string,(run:Detail)=>string][] = [
    ['Tarih',run=>date(run.simulation_date)],['İnvertör sayısı',run=>number(run.inverter_count)],
    ['AC nominal güç',run=>number(run.inverter_ac_rated_kw)+' kW'],['DC nominal güç',run=>number(run.inverter_dc_rated_kw)+' kW'],
    ['EKK limiti',run=>number(run.ekk_active_power_limit_kw)+' kW'],
    ['Trafo verimi',run=>'%'+number(run.transformer_efficiency*100)],
    ...energy.map(([key,label]):[string,(run:Detail)=>string]=>[label,run=>number(run[key])+' kWh']),
  ];
  return <>
    <section className="panel table-panel"><h2>Senaryo özeti</h2><p className="muted">{delta.same_weather_date?'Simülasyon tarihleri aynı.':'Simülasyon tarihleri farklı. Enerji farkını değerlendirirken ışınımı ve sıcaklığı da inceleyin.'}</p>
      <dl className="facts"><div><dt>Şebeke enerjisi farkı (ikinci − birinci)</dt><dd>{number(delta.grid_energy_difference_kwh)} kWh</dd></div><div><dt>Referansa göre değişim</dt><dd>{delta.grid_energy_change_percent===null?'Referans enerji sıfır':'%'+number(delta.grid_energy_change_percent)}</dd></div></dl>
      <div className="table-scroll" tabIndex={0} aria-label="Senaryo özeti"><table><thead><tr><th scope="col">Ölçüm</th>{runs.map(run=><th key={run.id} scope="col"><Link href={'/sonuclar/'+run.id}>Simülasyon #{run.id}</Link></th>)}</tr></thead><tbody>{metrics.map(([label,format])=><tr key={label}><th scope="row">{label}</th>{runs.map(run=><td key={run.id}>{format(run)}</td>)}</tr>)}</tbody></table></div>
    </section>
    <div className="chart-grid">{([
      ['Saatlik invertör gücü','kW','inverter_power_kw'],['Saatlik şebeke gücü','kW','grid_power_kw'],
      ['Güneş ışınımı','W/m²','irradiance_w_m2'],['Ortam sıcaklığı','°C','ambient_temperature_c'],
    ] as const).map(([title,unit,key])=><Chart key={key} title={title} unit={unit} hours={hours} series={series(key)}/>)}</div>
  </>;
}
