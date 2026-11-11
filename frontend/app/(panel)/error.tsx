'use client';
import Link from 'next/link';
export default function ErrorPage({reset}:{reset:()=>void}) {
  return <main className="standalone"><section className="panel empty"><h1>Çalışma alanı açılmadı</h1><p>FastAPI bağlantısını kontrol edip yeniden deneyin.</p><button className="primary" onClick={reset}>Yeniden dene</button><Link href="/giris">Giriş ekranına dön</Link></section></main>;
}
