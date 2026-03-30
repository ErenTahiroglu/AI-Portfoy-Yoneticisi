description: Backend dizinindeki Python kodları, FastAPI endpoint'leri ve genel mantık geliştirilirken tetiklenir
---

- PEP 8 standartlarına kesinlikle uy.
- Tüm fonksiyonlarda tip ipuçlarını (Type Hinting) kullan.
- Asenkron programlama (async/await) kurallarına sadık kal, bloklayıcı I/O işlemlerinden kaçın.
- SQLAlchemy modelleri ve sorgularında performans odaklı ol (n+1 problemlerinden kaçın).
- Hata yönetiminde merkezi bir logger kullan (`backend/utils/logger.py`).
