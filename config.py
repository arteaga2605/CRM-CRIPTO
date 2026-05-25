"""
Configuracion del CRM Crypto.
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./crypto_crm.db"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Exchange (opcional - para sincronizacion)
    EXCHANGE_ID: str = "binance"
    EXCHANGE_API_KEY: Optional[str] = None
    EXCHANGE_API_SECRET: Optional[str] = None

    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Alertas
    ALERTA_PERDIDA_PORCENTAJE: float = 20.0
    ALERTA_GANANCIA_PORCENTAJE: float = 50.0
    ALERTA_CONCENTRACION_MAX: float = 30.0
    DIAS_CLIENTE_DORMIDO: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
