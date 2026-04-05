import os
from langchain_core.language_models.chat_models import BaseChatModel

def get_quick_think_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.2, max_tokens: int = 500, api_key: str = None) -> BaseChatModel:
    """
    Yüksek hızlı, düşük maliyetli LLM. Analiz özetleme, veri toparlama, hızlı tartışma dönüşleri için.
    """
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        
    if "llama" in model_name.lower() or "mixtral" in model_name.lower():
        from langchain_groq import ChatGroq
        effective_api_key = api_key or os.getenv("GROQ_API_KEY") or ""
        return ChatGroq(model=model_name, temperature=temperature, api_key=effective_api_key, max_tokens=max_tokens)
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=temperature, 
        google_api_key=api_key or os.getenv("GOOGLE_API_KEY") or "", 
        max_output_tokens=max_tokens
    )

def get_deep_think_llm(model_name: str = "gemini-2.5-pro", temperature: float = 0.1, max_tokens: int = 1500, api_key: str = None) -> BaseChatModel:
    """
    Derin muhakeme yeteneğine sahip, sentezci ve yönetici (CIO/PM/Judge) ajanlar için ağır model.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if "llama" in model_name.lower() or "mixtral" in model_name.lower():
        from langchain_groq import ChatGroq
        effective_api_key = api_key or os.getenv("GROQ_API_KEY") or ""
        return ChatGroq(model=model_name, temperature=temperature, api_key=effective_api_key, max_tokens=max_tokens)
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=temperature, 
        google_api_key=api_key or os.getenv("GOOGLE_API_KEY") or "", 
        max_output_tokens=max_tokens
    )
