# AI-Portfoy-Yoneticisi Geliştirme Kuralları

- **Mimari:** Backend Python/FastAPI, Frontend sadece Vanilla JS, HTML ve CSS.
- **Yasaklar:** React, Vue, Tailwind, Bootstrap veya başka harici CSS/JS framework'leri KULLANMA.
- **Frontend Konumu:** Tüm frontend kodları `frontend/` klasöründedir.
- **DOM Bütünlüğü:** `frontend/js/` altındaki JS dosyaları (`app.js`, `api.js`, `charts.js` vb.) belirli HTML ID ve class'larına bağımlıdır. HTML yapısını modernize ederken mevcut `id="..."` ve `data-*="..."` attribute'larını ASLA silme, değiştirme veya yapısını bozma.
- **Tasarım Dili:** `frontend/logo.png` referans alınarak, kripto/borsa takip araçlarına uygun, modern, profesyonel ve karanlık (dark) tema odaklı bir finansal dashboard görünümü inşa edilmelidir.