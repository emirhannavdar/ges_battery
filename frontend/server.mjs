import { createServer } from 'node:http';
import next from 'next';

const dev = process.argv.includes('--dev');
process.env.NODE_ENV ??= dev ? 'development' : 'production';

const app = next({
  dev,
  hostname: '0.0.0.0',
  port: 3000,
});

const handle = app.getRequestHandler();

await app.prepare();

createServer((request, response) => {
  // IP'yi doğrudan bağlantıdan al.
  // Kullanıcının gönderdiği aynı isimli başlığın üzerine yaz.
  request.headers['x-forwarded-for'] =
    request.socket.remoteAddress;

  handle(request, response);
}).listen(3000, '0.0.0.0', () => {
  console.log('Frontend 3000 portunda çalışıyor.');
});