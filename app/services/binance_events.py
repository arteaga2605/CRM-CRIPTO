"""
Servicio para eventos de Binance – versión simplificada.
No se realiza scraping; se muestra un enlace manual en el dashboard.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import BinanceEvent

class BinanceEventScraper:
    @staticmethod
    def fetch_events() -> List[Dict[str, Any]]:
        """Devuelve lista vacía. No se obtienen eventos automáticamente."""
        return []

class BinanceEventService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_events(self) -> int:
        """No guarda eventos. Siempre retorna 0."""
        return 0
    
    def get_active_events(self, limit: int = 20) -> List[BinanceEvent]:
        """Devuelve lista vacía (no hay eventos almacenados)."""
        return []
    
    def mark_event_inactive(self, event_id: int):
        pass