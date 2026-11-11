import {ArrowUpRight, Sun, Zap} from 'lucide-react';
import {Login} from '@/components/forms';

export default async function Page({searchParams}:{searchParams:Promise<{oturum?:string}>}) {
  const expired = (await searchParams).oturum === 'bitti';
  return <main className="login">
    <section className="login-visual">
      <div className="brand"><span><Sun size={22}/></span>Helio</div>
      <div className="solar-grid" aria-hidden="true"/>
      <div className="login-intro"><Zap size={28}/><h1>GES Simülasyon<br/>Platformu</h1><p>Günlük üretimi simüle edin ve şebeke çıkışını senaryolar arasında karşılaştırın.</p></div>
      <div className="login-foot"><span>Üretim planlama ve analiz</span><ArrowUpRight size={17}/></div>
    </section>
    <section className="login-content"><Login expired={expired}/></section>
  </main>;
}
