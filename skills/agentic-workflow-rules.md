description: LangGraph, ajan düğümleri (nodes) ve state yönetimi üzerinde çalışırken tetiklenir
---

- `backend/engine/graph.py` içindeki grafik yapısını bozma.
- Yeni bir ajan düğümü eklerken `AgentState` yapısına sadık kal.
- Karar mekanizmalarında deterministik olmayan çıktılar için her zaman bir fallback planı oluştur.
- Ajanlar arası veri aktarımında (message passing) şeffaf ve izlenebilir ol.
