# Helio GES Simülasyon

Node.js 20.9 veya üzeri gerekir. FastAPI'yi mevcut yönteminizle ayrı başlatın.

```powershell
cd frontend
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

Tarayıcıda http://localhost:3000 adresini açın. `BACKEND_URL` sunucu tarafında kullanılır ve FastAPI'nin gerçek adresi olmalıdır. Örnekteki `127.0.0.1:8000`, yerel varsayılan kabulüdür. HTTPS sonlandıran ters vekil arkasında `FRONTEND_ORIGIN` değişkenine kullanıcının gördüğü HTTPS kökenini yazın. `SESSION_COOKIE_SECURE=true`, Secure çerez işaretini ayrıca zorunlu kılar.

| İşlem | FastAPI |
| --- | --- |
| Giriş | `POST /auth/token` (URL encoded form) |
| Kullanıcı | `GET /auth/users/me` |
| Günlük simülasyon | `POST /inverter/daily` |
| Geçmiş | `GET /inverter/simulations` |
| Kayıt detayı | `GET /inverter/simulations/{simulation_id}` |
| Karşılaştırma | `GET /inverter/simulations/compare?simulation_id_1=…&simulation_id_2=…` |

Next.js, JWT'yi 30 dakikalık HttpOnly ve SameSite=Lax çerezde tutar. Tarayıcı yalnızca Next.js'e bağlanır. Next.js, aktif kullanıcı doğrulaması ve simülasyon çağrıları için Bearer token ile FastAPI'ye bağlanır. Çıkışta oturum çerezi silinir.

Liste ve karşılaştırmanın eksik alanları kayıt detayından tamamlanır. Günlük POST yanıtında bulunan saatlik kullanılabilir ve kısılan güç, aynı sekmede yeni çalıştırılan kayıt için gösterilir. Saklanan kayıt detayında bu seriler sunulmadığında arayüz bunun bilgisini gösterir.

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run start
```

Üretim derlemesinden sonra `node test/smoke.mjs` ile geçici bir API test sunucusuna karşı Chrome'da akışları kontrol edebilirsiniz. Gerekirse `CHROME_PATH` ile Chrome konumunu ayarlayın. Test gerçek FastAPI veya PostgreSQL bağlantısı kullanmaz.

