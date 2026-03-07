from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Portfolio Analysis Platform"
    ENVIRONMENT: str = "production"
    
    # API Keys
    ALPHA_VANTAGE_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Network & Security
    SSL_VERIFY: bool = True
    REQUEST_TIMEOUT: int = 15
    GEMINI_TIMEOUT: int = 30
    
    # Cache
    CACHE_TTL_SECONDS: int = 300
    
    # Rate Limiting
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global settings instance
settings = Settings()

# Check environment for SSL bypass
if settings.ENVIRONMENT.lower() == "development":
    settings.SSL_VERIFY = False
