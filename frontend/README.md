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
| Oturum yenileme | `POST /auth/refresh-access-token` (`X-Refresh-Token` başlığı) |
| Kullanıcı | `GET /auth/users/me` |
| Günlük simülasyon | `POST /inverter/daily` |
| Geçmiş | `GET /inverter/simulations` |
| Kayıt detayı | `GET /inverter/simulations/{simulation_id}` |
| Karşılaştırma | `GET /inverter/simulations/compare?simulation_id_1=…&simulation_id_2=…` |

Access token yalnızca tarayıcıdaki JavaScript modülünün belleğinde tutulur. Tarayıcı Next.js'e, Next.js de FastAPI'ye bu token'ı `Authorization: Bearer …` başlığında gönderir. Access token çereze, localStorage'a veya sessionStorage'a yazılmaz. Refresh token HttpOnly ve SameSite=Lax çerezde tutulur, süresi JWT içindeki `exp` değerinden belirlenir. Next.js refresh token'ı FastAPI'ye `X-Refresh-Token` başlığında iletir.

Sayfa yenilenince bellek sıfırlanır. İstemci oturum katmanı `POST /api/session/refresh` ile yeni access token alır ve `GET /api/session/user` üzerinden kullanıcıyı doğruladıktan sonra çalışma alanını açar. Korumalı veriler API'nin Bearer doğrulamasıyla korunur. Normal istek 401 döndürürse istemci token'ı yenileyip isteği bir kez tekrarlar. Eşzamanlı istekler tek yenilemeyi bekler. 403 yetki hatası yenileme başlatmaz. Geçici bağlantı ve servis hatalarında refresh çerezi korunur. Refresh token geçersizse veya süresi dolmuşsa yeniden giriş gerekir. Çıkışta bellek token'ı ve refresh çerezi temizlenir.

Bu güncellemeden sonra bir kez yeniden giriş yapın. Önceki access çerezi giriş, yenileme veya çıkış sırasında silinir. `npm.cmd start` kullanıyorsanız önce `npm.cmd run build` çalıştırıp Next.js sürecini yeniden başlatın.

Liste ve karşılaştırmanın eksik alanları kayıt detayından tamamlanır. Kayıt detayı, veritabanında saklanan saatlik kullanılabilir güç, kısılan güç ve kısılan enerji alanlarını döndürür. Böylece bu grafikler sayfa yeniden açıldığında da görüntülenir. Eski kayıtlarda alanlar boşsa arayüz veri durumunu belirtir.

Sonuç sayfasındaki CSV indirme, saatlik ölçümleri dışa aktarır. Yeni simülasyon formu, girilen parametrelerden toplam AC/DC kapasiteyi ve DC/AC oranını gösterir. Grafikler ve ölçümler kaydedilen simülasyona aittir.

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npm.cmd run start
```

Üretim derlemesinden sonra `node test/smoke.mjs` ile geçici bir API test sunucusuna karşı Chrome'da akışları kontrol edebilirsiniz. Gerekirse `CHROME_PATH` ile Chrome konumunu ayarlayın. Test gerçek FastAPI veya PostgreSQL bağlantısı kullanmaz.

