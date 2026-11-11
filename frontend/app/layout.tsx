import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata = {title:'Helio | GES Simülasyon',description:'Günlük güneş enerjisi simülasyonu ve senaryo analizi'};
export default function Layout({children}:{children:React.ReactNode}) {
  return <html lang="tr"><body>{children}</body></html>;
}
