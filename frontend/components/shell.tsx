'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Activity, ArrowUpRight, GitCompareArrows, History, LayoutDashboard, LogOut, Plus, Sun} from 'lucide-react';
import {useState} from 'react';
import {api} from '@/lib/client';
import type {Profile} from '@/lib/contracts';

const links = [
  ['/', 'Genel bakış', LayoutDashboard],
  ['/yeni', 'Yeni simülasyon', Plus],
  ['/gecmis', 'Simülasyon geçmişi', History],
  ['/karsilastir', 'Karşılaştırma', GitCompareArrows],
] as const;

export function Shell({user,children}:{user:Profile;children:React.ReactNode}) {
  const path = usePathname();
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  async function logout() {
    setBusy(true);
    setError('');
    try {
      await api('session/logout',{method:'POST'});
      try {
        for(const key of Object.keys(sessionStorage)) {
          if(key.startsWith('ges-hours-') || key === 'ges-created') sessionStorage.removeItem(key);
        }
      } catch {}
      window.location.replace('/giris');
    } catch(err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }
  return <div className="shell">
    <aside className="sidebar">
      <Link href="/" className="brand"><span><Sun size={22}/></span>Helio</Link>
      <nav aria-label="Ana gezinme">{links.map(([href,label,Icon])=>{
        const active = path === href || (href === '/gecmis' && path.startsWith('/sonuclar/'));
        return <Link key={href} href={href} aria-current={active?'page':undefined}><Icon size={17}/><span>{label}</span></Link>;
      })}</nav>
      <div className="sidebar-foot"><Activity size={17}/> GES simülasyon çalışma alanı</div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span className="top-title">Enerji simülasyonu</span><div className="account">
        <span className="avatar" aria-hidden="true">{user.username.slice(0,2).toLocaleUpperCase('tr-TR')}</span>
        <div><strong>{user.full_name || user.username}</strong><small>{user.email || user.username}</small></div>
        <button type="button" className="icon-button" aria-label="Çıkış yap" title="Çıkış yap" onClick={logout} disabled={busy}><LogOut size={17}/></button>
      </div></header>
      {error && <div className="toast" role="alert">{error}</div>}
      <main className="content" key={path}>{children}</main>
    </div>
  </div>;
}
export function NewLink() {
  return <Link className="primary" href="/yeni"><Plus size={17}/> Yeni simülasyon <ArrowUpRight size={15}/></Link>;
}
