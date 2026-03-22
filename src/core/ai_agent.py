from langchain_google_genai import ChatGoogleGenerativeAI

def generate_report(ticker, data, api_key, model_name, check_islamic=True, check_financials=True, fin_data=None, market="US", lang="tr", system_errors: dict = None, ml_prediction: dict = None):
    """Gemini API'sini kullanarak seçili oranlara göre finansal rapor üretir."""
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1, google_api_key=api_key)

    is_etf = data.get("is_etf", False) if data else False
    
    islamic_context = ""
    financial_context = ""
    requirements = []
    
    if check_islamic and data:
        if is_etf:
            islamic_context = f"""
            Hesaplanan ETF Ağırlıklı (İslami Uygunluk) Verileri:
            - Ağırlıklı Arındırma Oranı: %{data.get('purification_ratio', 0):.2f} (Sınır %5)
            - Ağırlıklı Borçluluk Oranı: %{data.get('debt_ratio', 0):.2f} (Sınır %30)
            - AAOIFI Sonucu: {data.get('status', 'Bilinmiyor')}
            - Fonun İçindeki Ana Şirketlerin Oranları: {data.get('holdings_str', '')}
            """
            requirements.append("1. **⚖️ İslami Uygunluk (ETF):** (ETF içindeki şirketlerin dağılımı oranında fonun arındırma ve borçluluk hesaplarının AAOIFI standartlarına göre net değerlendirilmesi. Sıfır laf kalabalığı.)")
        else:
            currency = 'TRY' if market == 'TR' else 'USD'
            islamic_context = f"""
            İslami Uygunluk (AAOIFI) Verileri:
            - Bilanço Tarihi: {data.get('bal_date', '')} | Gelir Tablosu: {data.get('inc_date', '')}
            - Toplam Gelir: {data.get('revenue', 0):,.0f} {currency} | Faiz Geliri: {data.get('interest', 0):,.0f} {currency}
            - Toplam Varlık: {data.get('assets', 0):,.0f} {currency} | Toplam Borç: {data.get('debt', 0):,.0f} {currency}
            - Arındırma (Yasaklı Gelir) Oranı: %{data.get('purification_ratio', 0):.2f} (Sınır %5)
            - Borçluluk Oranı: %{data.get('debt_ratio', 0):.2f} (Sınır %30)
            - AAOIFI Sonucu: {data.get('status', 'Bilinmiyor')}
            """
            requirements.append("1. **⚖️ İslami Uygunluk Analizi:** (Şirketin gelir ve bilançosu baz alınarak AAOIFI faiz geliri ve borçluluk eşiklerinin aşılıp aşılmadığının net, rakamsal özetini yapın.)")
            
    if check_financials and fin_data:
        s5 = fin_data.get('s5')
        s5_str = f"%{s5:.2f}" if s5 is not None else "Veri Yok"
        yt = fin_data.get('yt', {})
        div = "Yok"
        if yt:
            years = sorted(yt.keys(), reverse=True)
            if years: div = f"%{yt[years[0]]:.2f}"
        
        # Risk metrikleri
        risk = fin_data.get('risk', {})
        sharpe_str = f"{risk.get('sharpe_ratio', 'N/A')}" if risk else "Veri Yok"
        mdd_str = f"%{risk.get('max_drawdown', 'N/A')} ({risk.get('max_drawdown_tarih', '')})" if risk else "Veri Yok"
            
        market_label = "Türkiye (TR) Reel Enflasyon Düzeltmeli Getirisi" if market == 'TR' else "ABD Reel Enflasyon Düzeltmeli Getiri"
            
        financial_context = f"""
        Finansal ve Geçmiş Performans Verileri:
        - Son 5 Yıllık Reel (Enflasyondan Arındırılmış) Toplam Getiri: {s5_str}
        - Son Yılın Temettü Verimi: {div}
        - Sharpe Ratio (Risk/Getiri Oranı): {sharpe_str}
        - Maximum Drawdown (En Büyük Düşüş): {mdd_str}
        """
        requirements.append(f"{len(requirements)+1}. **📈 Finansal Getiri Performansı:** (Şirketin 5 yıllık {market_label} oranını, varsa son temettü oranını ve risk metriklerini (Sharpe Ratio, Max Drawdown) değerlendir.)")
    
    # Metrik bazlı kısa içgörüler (Frontend modal için)
    requirements.append(f"{len(requirements)+1}. **🔍 Metrik İçgörüleri:** Her bir finansal metrik (P/E, P/B, Beta, Sharpe vb.) için sadece o metriğe özel, 1-2 cümlelik çok kısa profesyonel bir yorum hazırla.")

    ml_context = ""
    if ml_prediction:
        ml_context = f"""
        MAKİNE ÖĞRENİMİ 7 GÜNLÜK TAHMİNİ:
        - Yön (Trend): {ml_prediction.get('direction', 'Bilinmiyor')}
        - Güven Skoru (Confidence): {ml_prediction.get('confidence', 0)}
        - 7 Günlük Hedef Fiyat: {ml_prediction.get('target_7d', 'Bilinmiyor')} (Değişim: %{ml_prediction.get('change_pct', 0)})
        """

    if len(requirements) == 0:
        return "Gerekli analiz verisi seçilmediği için yorum üretilemedi."
        
    system_errors_text = ""
    if system_errors:
        errors_list = "\n".join([f"- {k}: {v}" for k, v in system_errors.items()])
        system_errors_text = f"⚠️ SİSTEM UYARILARI VE EKSİK VERİ BEYANI: Aşağıdaki modüllerde API kesintisi veya veri eksikliği yaşanmıştır:\n{errors_list}\n"
        
    lang_instruction = "Generate the response entirely in English." if lang == "en" else "Sonuçları daima Türkçe üret."
    prompt = f"""
    Sen teknik ve veriye odaklı konuşan kıdemli bir nicel finansal analistisin.
    Görev: {ticker} {"(ETF/Fon)" if is_etf else "(Hisse)"} sembolü için gereksiz giriş cümleleri KULLANMADAN aşağıdaki özellikleri inceleyip kısa net bir analiz çıkartmak. Piyasası: {"Türk Piyasası (BIST/TEFAS)" if market == "TR" else "ABD Piyasası"}.
    {lang_instruction}
    
    {system_errors_text}
    MEVCUT SIFILTRENMİŞ VERİLER:
    {islamic_context}
    {financial_context}
    {ml_context}
    
    Aşağıdaki başlık formatlarını kullanarak kısa, net ve gereksiz cümlesiz bir rapor hazırla:
    {chr(10).join(requirements)}
    
    ÖNEMLİ: Raporun en sonuna, KESİNLİKLE başka bir metin eklemeden, aşağıdaki JSON formatında bir gizli blok ekle (bu veriler metrik kutularına tıklandığında gösterilecek):
    <!--METRIC_INSIGHTS:
    {{
      "pe": "P/E oranı hakkında kısa yorum",
      "pb": "P/B oranı hakkında kısa yorum",
      "beta": "Beta hakkında kısa yorum",
      "sharpe": "Sharpe rasyosu yorumu",
      "max_dd": "Max Drawdown yorumu",
      "div": "Temettü verimi yorumu",
      "s5": "5 yıllık getiri yorumu"
    }}
    -->
    
    ÖNEMLİ KURALLAR:
    1. İstenmeyen şeyleri yorumlamayın! (Sadece size verilen İslami veya Finansal verilere odaklanın).
    2. "Sayın Yatırımcı", "Özetle" tarzı doldurma sözcükler YASAKTIR.
    3. Çıktında KESİNLİKLE "$" (dolar) sembolü kullanma, yerine 'USD' veya 'TL' gibi ifadeler kullan. Markdown formatını bozmamaya dikkat et.
    4. Gereksiz bir övgü yapma.
    5. HALÜSİNASYON YASAKTIR: Eğer sana verilen verilerde veya 'Sistem Uyarıları' bölümünde bir API çökmesi veya eksik veri raporlanmışsa, kesinlikle değer uydurma. Raporunda 'Şu teknik nedenden ötürü ([Hata Sebebi]) bu metrik değerlendirilememiştir' diyerek şeffaf ol. Zorunlu JSON bloğunda (METRIC_INSIGHTS) eksik kalan metriklerin karşılığına değer olarak 'Veri yetersizliği nedeniyle hesaplanamadı' yaz.
    6. Eğer sana Makine Öğrenimi tahmini sunulmuşsa, nihai değerlendirmeni ve fiyat/trend öngörülerini yaparken bu algoritmik veriyi referans al. '%X güven skoruyla Y yönünde bir trend öngörülmektedir' şeklinde doğrudan modelin tahminine atıfta bulun.
    """
    
    try:
        response = llm.invoke(prompt)
        return str(response.content)
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            return "⚠️ **Kota Sınırı Aşıldı (Kullanım Limiti)**<br>Seçtiğiniz Gemini modelinin ücretsiz sürüm kotası dolmuştur. Lütfen 1-2 dakika bekleyip tekrar deneyin veya ayarlar menüsünden `gemini-2.5-flash` modeline geçiş yapın."
        return f"Gemini Yanıt Hatası: {error_msg}"


import json

def generate_wizard_portfolio(prompt_text: str, api_key: str, model_name: str = "gemini-2.5-flash", lang: str = "tr") -> list:
    """Kullanıcının metin girişini analiz edip ticker ve ağırlık öneren JSON döndürür."""
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2, google_api_key=api_key)
    
    sys_prompt = f"""
    Sen US ve TR piyasalarına hakim profesyonel bir nicel yatırım yöneticisisin. 
    Kullanıcının aşağıda belirttiği profile, risk algısına veya temaya uygun olarak, BIST (TR) veya ABD (US) borsalarından en mantıklı 3 ile 8 arası hisse veya fon (ETF/TEFAS) barındıran bir portföy öner.
    
    Kullanıcı talebi: "{prompt_text}"
    
    Dil talimatı: { "Analyze the user request and respond in English if possible (JSON keys must remain English)." if lang == "en" else "Kullanıcının isteğini yanıtla (JSON keyleri daima İngilizce olsun)." }
    
    DİKKAT: YALNIZCA geçerli bir JSON array döndür. Yorum, giriş veya markdown backtick (```json) KULLANMA.
    Format Örneği:
    [
        {{"ticker": "AAPL", "weight": 40.0, "reason": "Güçlü bilanço ve nakit akışı"}},
        {{"ticker": "THYAO", "weight": 30.0, "reason": "Sektör lideri ve istikrarlı büyüme"}}
    ]
    Ağırlıklar (weight) toplamda her zaman tam 100 olmalıdır.
    """
    
    try:
        response = llm.invoke(sys_prompt)
        content = str(response.content).strip()
        
        # Temizle (markdown backticks bazen sızabiliyor)
        if content.startswith("```json"): content = content[7:]
        elif content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        data = json.loads(content.strip())
        return data
    except Exception as e:
        raise ValueError(f"AI yanıtı çözümlenemedi veya kota aşıldı: {str(e)}")

def generate_chat_response(messages: list, context: dict, api_key: str, model_name: str = "gemini-2.5-flash", lang: str = "tr") -> str:
    """Yüzen Chatbot (Copilot) için kullanıcının portföy verisi üzerinden konuşma tabanlı (conversational) yanıt üretir."""
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3, google_api_key=api_key)
    
    # Portföy bağlamını temiz bir string'e dönüştür
    portfolio_summary = json.dumps(context, indent=2, ensure_ascii=False)
    
    system_instruction = f"""
    Sen, bu uygulamanın (Portföy Analiz Platformu) içine entegre edilmiş, profesyonel ama dost canlısı bir "Yapay Zeka Portföy Asistanı"sın (AI Copilot).
    Kullanıcı sana portföyü hakkında sorular soracak veya analiz isteyecek.
    Aşağıda kullanıcının ŞU AN EKRANINDA GÖRDÜĞÜ portföyünün arka plan (JSON) analizi ve verileri bulunuyor:
    
    === PORTFÖY VERİLERİ ===
    {portfolio_summary}
    ========================
    
    KURALLAR:
    1. Kullanıcının sorusuna doğrudan ve net yanıt ver. Sadece elindeki verileri (JSON) referans al.
    2. Cevapların kısa, güven verici ve teknik olarak doğru olsun (Markdown formatı kullan; kalın metinler, listeler vs.).
    3. Kullanıcı "en riskli hissem hangisi" diye sorarsa, P/E oranı, Beta değeri veya Drawdown oranlarına bakarak mantıklı bir çıkarım yap.
    4. Sektör dağılımını veya ağırlıkları sormadan pat diye listeleme, sadece sorulana cevap ver.
    5. Dil: {"Cevaplarını her zaman İngilizce üret" if lang == "en" else "Cevaplarını her zaman Türkçe dilinde üret"}.
    """
    
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    
    langchain_msgs = [SystemMessage(content=system_instruction)]
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            langchain_msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_msgs.append(AIMessage(content=content))
            
    try:
        response = llm.invoke(langchain_msgs)
        return str(response.content)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "Kota sınırı aşıldı. Lütfen birkaç dakika bekleyin."
        return f"Üzgünüm, şu an bağlantı kuramıyorum (Hata: {error_msg})"

def generate_macro_advice(portfolio_data: dict, api_key: str, model_name: str = "gemini-2.5-flash", lang: str = "tr"):
    """
    Tüm portföyün makro analizini (Riskler, Korelasyon, Dengeleme) streaming (generator) olarak döndürür.
    """
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3, google_api_key=api_key)
    
    # Portföy özetini sıkıştır
    summary_str = json.dumps(portfolio_data, indent=2, ensure_ascii=False)
    
    prompt = f"""
    Sen, büyük bir varlık yönetimi şirketinde çalışan Baş Yatırım Stratejistisin (CIO).
    Görev: Aşağıda verilen portföy özetini (hisseler, ağırlıklar, rasyolar, korelasyonlar ve sektörler) inceleyip makro seviyede stratejik öneriler sunmak.
    
    === PORTFÖY ÖZETİ (JSON) ===
    {summary_str}
    ============================
    
    Lütfen yanıtını KESİNLİKLE aşağıdaki 3 ana başlık altında topla. Saygılı, teknik jargon içeren ama anlaşılır konuş. Giriş veya doldurma cümleleri YASAKTIR.
    
    ### 1. 🔍 Portföydeki Makro Riskler ve Yığılmalar
    - Sektörel yığılma var mı? (Örn: Aşırı teknoloji veya sanayi ağırlığı)
    - Ortalama Beta durumu ve piyasa hassasiyeti.
    - Varsa yüksek faizli borç veya pahalı değerleme uyarıları.
    
    ### 2. ⚡ Korelasyon ve Çeşitlendirme (Diversification) Analizi
    - Portföydeki varlıklar birbirini hedge ediyor mu, yoksa aynı yöne mi hareket ediyorlar?
    - Riskleri optimize etmek için eksik kalan pazar veya varlık sınıfı önerisi (Örn: Altın, tahvil vb.).
    
    ### 3. ⚖️ Yeniden Dengeleme (Rebalancing) Önerileri
    - Hangi varlığın ağırlığı aşırı yüksek/riskli, hangisi makul?
    - Kısa ve net aksiyon maddeleri (Action Items) sunun.
    
    Dil talimatı: { "Respond entirely in English using beautiful Markdown formatting." if lang == "en" else "Sonuçları her zaman Türkçe üret ve Markdown formatını güzel kullan." }
    """
    
    try:
        for chunk in llm.stream(prompt):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            yield "Kota sınırı aşıldı. Lütfen birkaç dakika bekleyin."
        else:
            yield f"Makro analiz akış hatası: {error_msg}"

def analyze_news_sentiment(news_data: list, check_islamic: bool, api_key: str, model_name: str = "gemini-2.5-flash", lang: str = "tr") -> dict:
    """Haber başlıkları ve özetlerini analiz edip Duyarlılık Skoru ve İslami Risk döner."""
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2, google_api_key=api_key)
    
    news_context = []
    for i, item in enumerate(news_data[:5]):
        title = item.get("title", "Başlık yok")
        summary = item.get("summary", "Özet yok")
        news_context.append(f"[{i}] BAŞLIK: {title} | ÖZET: {summary}")
        
    context_str = "\n".join(news_context) if news_context else "Haber bulunamadı."
    
    islamic_prompt = "Ayrıca haberleri İslami finans ilkelerine (helal kazanç, faizsizlik vb.) aykırı bir 'risk' teşkil edip etmediği açısından incele. 'islamic_risk_flag' ve 'risk_reason' değerlerini buna göre belirle." if check_islamic else "İslami kontrol kapalıdır, 'islamic_risk_flag' false ve 'risk_reason' 'Kontrol kapalı' bırakabilirsiniz."

    sys_prompt = f"""
    Sen finansal haberleri ve piyasa duyarlılığını analiz eden bir AI asistanısın.
    Aşağıda belirli bir şirket için yayınlanan son haberler bulunmaktadır:
    
    ====================
    {context_str}
    ====================
    
    GÖREVİN:
    1. Bu haberlerin genel duyarlılık skorunu hesapla (0-100 arası). 
       Skala: 0-35 (Korku), 36-65 (Nötr), 66-100 (Açgözlülük).
    2. En uygun duyarlılık etiketini belirle (Korku / Nötr / Açgözlülük).
    3. {islamic_prompt}
    
    DİKKAT: YALNIZCA aşağıdaki JSON formatında bir veri döndür. Backticks (```json) veya açıklama ekleme!
    {{
      "score": 75, 
      "sentiment_label": "Açgözlülük", 
      "islamic_risk_flag": false, 
      "risk_reason": "Haberlerde helal uygunluğu bozacak bir unsur bulunamadı."
    }}
    """
    
    try:
        response = llm.invoke(sys_prompt)
        content = str(response.content).strip()
        
        if content.startswith("```json"): content = content[7:]
        elif content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        return json.loads(content.strip())
    except Exception as e:
        return {
            "score": 50,
            "sentiment_label": "Hata",
            "islamic_risk_flag": False,
            "risk_reason": f"AI Analiz Hatası: {str(e)}"
        }