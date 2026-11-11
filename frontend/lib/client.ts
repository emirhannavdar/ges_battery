export async function api<T>(path:string, init?:RequestInit):Promise<T> {
  const response = await fetch('/api/' + path, {...init, cache:'no-store'});
  const body = await response.json();
  if(response.ok) return body;
  if(response.status === 401 && !path.startsWith('session/')) {
    window.location.replace('/giris?oturum=bitti');
  }
  const detail = body.detail ?? body.error_description ?? body.message ?? body.error?.message;
  const message = Array.isArray(detail)
    ? detail.map(item=>[item.loc?.at(-1),item.msg].filter(Boolean).join(' — ')).join(' ')
    : typeof detail === 'object' && detail
      ? [detail.message,detail.missing_hours?.join(', ')].filter(Boolean).join(' ')
      : detail;
  throw new Error(message || (response.status === 403 ? 'Bu işlem için yetkiniz yok.' : 'İşlem tamamlanamadı.'));
}
