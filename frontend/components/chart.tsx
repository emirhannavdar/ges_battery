'use client';
import {useEffect,useRef} from 'react';
import {init,use as registerComponents} from 'echarts/core';
import {LineChart} from 'echarts/charts';
import {AriaComponent,GridComponent,LegendComponent,TooltipComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';

registerComponents([LineChart,AriaComponent,GridComponent,LegendComponent,TooltipComponent,CanvasRenderer]);

export type Series = {name:string;values:(number|null)[];tone:'amber'|'green'|'red'|'blue'};
export function Chart({title,unit,hours,series,description}:{title:string;unit:string;hours:string[];series:Series[];description?:string}) {
  const node = useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const element = node.current;
    if(!element || !hours.length) return;
    const styles = getComputedStyle(element);
    const token = (name:string) => styles.getPropertyValue('--' + name).trim();
    const chart = init(element);
    chart.setOption({
      animation:!matchMedia('(prefers-reduced-motion: reduce)').matches,
      aria:{enabled:true},
      textStyle:{fontFamily:styles.fontFamily},
      color:series.map(line=>token(line.tone)),
      grid:{left:56,right:20,top:series.length>1?56:32,bottom:32},
      tooltip:{trigger:'axis',confine:true,backgroundColor:token('surface'),borderColor:token('border'),textStyle:{color:token('ink')},valueFormatter:(value:unknown)=>typeof value==='number'?value.toLocaleString('tr-TR')+' '+unit:'—'},
      legend:{show:series.length>1,textStyle:{color:token('muted')},top:0,type:'scroll'},
      xAxis:{type:'category',boundaryGap:false,data:hours,axisTick:{show:false},axisLabel:{color:token('muted'),hideOverlap:true},axisLine:{lineStyle:{color:token('border')}}},
      yAxis:{type:'value',name:unit,nameTextStyle:{color:token('muted')},axisLabel:{color:token('muted'),formatter:(value:number)=>value.toLocaleString('tr-TR')},splitLine:{lineStyle:{color:token('border'),type:'dashed'}}},
      series:series.map((line,index)=>({name:line.name,type:'line',data:line.values,showSymbol:false,symbolSize:6,lineStyle:{width:2.5,type:index?'dashed':'solid'},areaStyle:index===0?{opacity:.07}:undefined})),
    });
    const observer = new ResizeObserver(()=>chart.resize());
    observer.observe(element);
    return ()=>{observer.disconnect();chart.dispose();};
  },[hours,series,unit]);
  return <section className="panel chart-panel"><header className="chart-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><span className="unit-label">{unit}</span></header>{hours.length?<div ref={node} className="chart" role="img" aria-label={title+' ('+unit+')'}/>:<p className="muted">Saatlik kayıt bulunamadı.</p>}</section>;
}
