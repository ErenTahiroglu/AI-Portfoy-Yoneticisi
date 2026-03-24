# AI Workspace Rules & Tech Stack

## 🛠 Proje Teknoloji Yığını (Tech Stack)

### Backend
- **Dil/Çerçeve**: Python + FastAPI
- **Veri Tabanı & Geçişler**: Alembic + SQLAlchemy (Öngörülen)
- **Modüller**: 
  - Veri Çekme: `yahooquery`, `tefas`, `yfinance`
  - Analitik: `pandas`, `numpy`
  - AI Destekli: `langchain-core`, `google-genai`
- **Sunucu**: Uvicorn

### Frontend
- **Model**: Vanilla HTML5 / CSS3 / ES6+ JavaScript
- **Tür**: Progressive Web App (PWA) (`manifest.json`, `sw.js` mevcut)
- **Mimari**: Modüler ES6 JS Yapısı
- **Tasarım**: Responsive, Mobile-First

---

## 🎨 Arayüz (UI/UX) Standartları ve Kurallar

Tüm yeni arayüz geliştirmelerinde ve değişikliklerinde aşağıdaki kurallara **kesinlikle uyulmalıdır**:

### 1. Görsel Mükemmellik (Premium Aesthetics)
- **Ucuz AI Çıktısı Görüntüsü Yasaktır**: Sadece düz renkler (`#ff0000`, `#0000ff`) veya standart tarayıcı fontları (Times New Roman vb.) kullanılmaz.
- **Renk Teorisi**: Harmonik, modern ve göz yormayan paletler (örneğin HSL tailored veya sleek dark mode renkleri) kullanılmalıdır.
- **Tipografi**: Modern web fontları (örn. Inter, Outfit, Roboto) kullanılmalı, hiyerarşi (H1-H6) net olmalıdır.
- **Görsel Efektler**: Akıcı degrade (gradient) geçişleri, camlaştırma (glassmorphism) gibi modern tasarım trendleri duruma göre uygulanmalıdır.

### 2. Akıcı ve Dinamik Deneyim (Dynamic UX)
- **Mikro Etkileşimler**: Butonlar, linkler ve kartlar için hover/active efektleri tanımlanmalıdır.
- **Animasyonlar**: Sayfa geçişleri ve veri yüklemeleri için akıcı CSS animasyonları kullanılmalıdır.
- **Yükleme Durumları (Loaders)**: Veri beklenen yerlerde şık loader'lar veya iskelet ekranlar (skeleton screens) yer almalıdır.

### 3. Esneklik ve Standartlar (Responsiveness)
- **Sıfır Hata Toleransı**: Taşan içerikler, kayan div'ler veya okunması imkansız küçük metinler kabul edilemez.
- **Mobil Öncelikli (Mobile-First)**: Tasarımlar önce mobil ekranlarda test edilmeli, ardından geniş ekranlara uyarlanmalıdır.

---

## 🛑 Kesin Mimari Kısıtlamalar (Strict Architectural Constraints)

Tüm kodlama ve tasarım süreçlerinde aşağıdaki kurallar **HİÇBİR TAVİZ VERİLMEKSİZİN** uygulanacaktır:

### 1. CSS Framework Yasağı (Strict Vanilla CSS)
- **KURAL**: UI/UX geliştirmelerinde HTML içine **Tailwind CSS**, **Bootstrap** veya herhangi bir harici CSS framework CDN'i ENJEKTE ETMEK **KESİNLİKLE YASAKTIR**.
- **UYGULAMA**: Tüm stiller sadece ve sadece projenin kendi `frontend/styles.css` dosyası üzerinden, modüler ve Vanilla CSS kurallarıyla yazılmalıdır.

### 2. Three-Tier Mimari İhlali Yasağı (No Direct Database Access)
- **KURAL**: Frontend (İstemci) kodları **KESİNLİKLE** doğrudan veritabanına veri yazma/okuma isteği atamaz.
- **UYGULAMA**: Tüm frontend API çağrıları (Fetch/Ajax), `frontend/js/api.js` üzerinden Render'daki Backend API rotalarına (`/api/...`) yönlendirilmelidir. Arayüz yenilenirken bu iletişim sacayağı bozulamaz.

### 3. Backend İş Mantığı Dokunulmazlığı (Backend Freeze)
- **KURAL**: UI (Arayüz) görevleri sırasında, kullanıcının izni olmadan `backend/api/`, `backend/core/` veya `backend/analyzers/` dizinlerindeki Python dosyalarında hiçbir mantıksal değişiklik yapılamaz.
- **UYGULAMA**: Frontend tasarımı veya basit UI ihtiyaçları için Backend rotaları feda edilemez veya değiştirilemez.

---

## 🤖 Otonom Çalışma Kuralları

- Değişiklikler yapıldıktan sonra **Puppeteer** (veya benzeri bir bot) çalıştırılarak ekran görüntüsü alınmalı, arayüzde kırılma/kapanma olup olmadığı sistem tarafından analiz edilmelidir.
- Herhangi bir bileşen animasyonluysa, ekran görüntüsü öncesi `delay` (gecikme) süresi tanınmalıdır.
- Bulunan görsel hatalar, kullanıcının müdahalesine gerek kalmadan otonom olarak düzeltilmelidir.

> [!IMPORTANT]
> Tüm UI kodlamalarında `brand_assets` klasöründe tanımlanan (veya kullanıcı tarafından eklenen) logonun, renk paletinin ve font kurallarının dışına çıkmak yasaktır.
