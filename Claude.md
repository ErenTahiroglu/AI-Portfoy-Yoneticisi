# CLAUDE.md — AI Portföy Yöneticisi AI Dispatcher

Sen bu projenin ana mimarısın. Herhangi bir kod yazmadan önce bu dosyayı ve `ARCHITECTURE.md` dosyasını referans almalısın.

## Proje Amacı

Ajan tabanlı (agentic), çok kriterli (BIST, Teknik, İslami) bir portföy yönetim ve analiz sistemi.

## Skill Yönlendirmeleri

Yaptığın işe göre şu "Yetenek" dosyalarını belleğe yükle:

1. Genel Python ve FastAPI geliştirmeleri için: `docs/skills/python-backend-standards.md`
2. LangGraph ve Ajan mantığı (Execution Engine) için: `docs/skills/agentic-workflow-rules.md`
3. Market verisi, scrapers ve analizörler için: `docs/skills/market-analysis-logic.md`

## AI Davranış Kuralları

- **Finansal Hassasiyet:** Hatalı bir PnL hesaplaması veya yanlış piyasa verisi işleme sistemin güvenilirliğini yıkar. Emin olmadığında soru sor.
- **Ajan Akışı:** LangGraph düğümlerini değiştirirken mevcut state yapısını bozmadığından emin ol.
- **Paralel Sorgu:** İşlem yaparken token maliyetini düşürmek için terminalde `/btw` komutuyla benden anlık yönlendirme isteyebilirsin.
- **Dil:** Teknik açıklamalar ve sorular her zaman Türkçe olmalıdır.

## Soru Sorma Prosedürü

Karmaşık mimari kararlarda veya veri kaynağı değişikliklerinde şu formatı kullan:
`❓ [Modül Adı]: [Problem]`
`Seçenek A: ...`
`Seçenek B: ...`
