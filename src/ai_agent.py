from langchain_google_genai import ChatGoogleGenerativeAI

def generate_report(ticker, data, api_key, model_name, check_islamic=True, check_financials=True, fin_data=None, market="US"):
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
    
    if len(requirements) == 0:
        return "Gerekli analiz verisi seçilmediği için yorum üretilemedi."
        
    prompt = f"""
    Sen teknik ve veriye odaklı konuşan kıdemli bir nicel finansal analistisin.
    Görev: {ticker} {"(ETF/Fon)" if is_etf else "(Hisse)"} sembolü için gereksiz giriş cümleleri KULLANMADAN aşağıdaki özellikleri inceleyip kısa net bir analiz çıkartmak. Piyasası: {"Türk Piyasası (BIST/TEFAS)" if market == "TR" else "ABD Piyasası"}.
    
    MEVCUT SIFILTRENMİŞ VERİLER:
    {islamic_context}
    {financial_context}
    
    Aşağıdaki başlık formatlarını kullanarak kısa, net ve gereksiz cümlesiz bir rapor hazırla:
    {chr(10).join(requirements)}
    
    ÖNEMLİ KURALLAR:
    1. İstenmeyen şeyleri yorumlamayın! (Sadece size verilen İslami veya Finansal verilere odaklanın).
    2. "Sayın Yatırımcı", "Özetle" tarzı doldurma sözcükler YASAKTIR.
    3. Çıktında KESİNLİKLE "$" (dolar) sembolü kullanma, yerine 'USD' veya 'TL' gibi ifadeler kullan. Markdown formatını bozmamaya dikkat et.
    4. Gereksiz bir övgü yapma.
    """
    
    try:
        response = llm.invoke(prompt)
        return str(response.content)
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            return "⚠️ **Kota Sınırı Aşıldı (Kullanım Limiti)**<br>Seçtiğiniz Gemini modelinin ücretsiz sürüm kotası dolmuştur. Lütfen 1-2 dakika bekleyip tekrar deneyin veya ayarlar menüsünden `gemini-2.5-flash` modeline geçiş yapın."
        return f"Gemini Yanıt Hatası: {error_msg}"