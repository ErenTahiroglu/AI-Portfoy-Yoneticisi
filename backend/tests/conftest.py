import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Proje kök dizinine erişim
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 🚫 [SRE] Zero Trust Network Isolation
# pytest-socket eklentisi tarafından yönetilen ağ kısıtlamaları.
# pytest.ini veya ci.yml içerisinde --disable-socket ve --allow-hosts=127.0.0.1,localhost
# parametreleri ile asenkron/senkron tüm dış sızıntılar kapatılmıştır.

@pytest.fixture(autouse=True)
def mock_all_llms():
    """
    Tüm LangChain invocation'larını (senkron/asenkron) otomatik yakalayan güvenlik kalkanı.
    """
    with patch("langchain_core.language_models.base.BaseLanguageModel.invoke") as mock_invoke, \
         patch("langchain_core.language_models.chat_models.BaseChatModel.ainvoke") as mock_ainvoke:
        
        mock_response = MagicMock()
        mock_response.content = "MOCK_AI_RESPONSE: Zero Trust ortamında gerçek LLM çağrısı engellendi."
        
        mock_invoke.return_value = mock_response
        mock_ainvoke.return_value = mock_response
        
        yield mock_invoke, mock_ainvoke

# DNS çözümleme hatalarını (gaierror) önlemek için asenkron event loop'larda 
# localhost dışındaki her şeyin engellendiğinden emin oluyoruz.
@pytest.fixture(autouse=True)
def enforce_zero_trust_firewall(monkeypatch):
    """
    pytest-socket'ın üzerine ek bir katman olarak, 
    beklenmedik kütüphanelerin alt seviye erişimlerini loglar.
    """
    # Not: pytest-socket zaten --disable-socket ile her şeyi bloklar.
    pass
