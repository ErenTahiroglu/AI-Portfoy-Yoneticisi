description: BIST, TEFAS veya teknik analizörler üzerinde çalışırken tetiklenir
---

- Finansal hesaplamalarda `Decimal` tipi kullan, `float` hatalarından kaçın.
- Veri çekme işlemlerinde `backend/data/data_sources.py` yapısını kullan.
- Shadow PnL hesaplamalarında `shadow_pnl_tracker.py` içindeki geçmiş veri tutarlılığını koru.
- İslami finans filtreleri uygulanırken `islamic_analyzer.py` kurallarını temel al.
