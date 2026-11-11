import {notFound} from 'next/navigation';
import {Results} from '@/components/results';
export default async function Page({params}:{params:Promise<{id:string}>}){
  const {id}=await params;
  if(!/^[1-9]\d*$/.test(id)) notFound();
  return <Results id={id}/>;
}
