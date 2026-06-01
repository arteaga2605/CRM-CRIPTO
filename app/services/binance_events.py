"""
Servicio para detectar eventos de Binance (Launchpool, Megadrop, nuevos listados)
mediante web scraping controlado. Sin datos ficticios.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import BinanceEvent

class BinanceEventScraper:
    """Extrae eventos recientes de la página de anuncios de Binance."""
    
    ANNOUNCEMENT_URL = "https://www.binance.com/en/support/announcement/c-48?c=48&navId=48"
    
    @staticmethod
    def fetch_events() -> List[Dict[str, Any]]:
        """
        Realiza scraping de la página de anuncios y devuelve eventos reales.
        Si no encuentra ninguno, devuelve lista vacía.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        events = []
        
        try:
            resp = requests.get(BinanceEventScraper.ANNOUNCEMENT_URL, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'lxml')
                # Buscar elementos que contengan anuncios. La estructura actual puede usar clases como:
                # .css-1ej4pfo, .css-1h1rkxh, .announcement-item, etc.
                # Buscamos enlaces que contengan títulos de anuncios
                # Una estrategia más robusta: buscar todos los enlaces que estén dentro de <h2> o <div> con texto largo
                for link in soup.find_all('a', href=True):
                    # Buscar el texto del enlace (puede estar dentro de un <div> o <span>)
                    title = link.get_text(strip=True)
                    # Filtrar por longitud y palabras clave
                    if len(title) > 20 and any(kw in title.lower() for kw in ['launchpool', 'megadrop', 'listing', 'list', 'launch', 'new']):
                        url = link['href']
                        if not url.startswith('http'):
                            url = "https://www.binance.com" + url
                        # Determinar tipo
                        event_type = "announcement"
                        if "launchpool" in title.lower():
                            event_type = "launchpool"
                        elif "megadrop" in title.lower():
                            event_type = "megadrop"
                        elif "listing" in title.lower() or "list" in title.lower():
                            event_type = "new_listing"
                        events.append({
                            "title": title,
                            "description": "",
                            "event_type": event_type,
                            "url": url,
                            "event_date": None
                        })
                # Eliminar duplicados (por título)
                unique = {}
                for ev in events:
                    if ev["title"] not in unique:
                        unique[ev["title"]] = ev
                events = list(unique.values())
                # Limitar a los 15 más recientes (aproximadamente)
                events = events[:15]
            else:
                print(f"Error HTTP {resp.status_code} al acceder a Binance")
        except Exception as e:
            print(f"Error scraping eventos reales: {e}")
        
        # No se añaden eventos ficticios
        return events

class BinanceEventService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_events(self) -> int:
        """Actualiza la base de datos con eventos reales. Retorna número de nuevos eventos guardados."""
        new_events = BinanceEventScraper.fetch_events()
        saved_count = 0
        for ev in new_events:
            exists = self.db.query(BinanceEvent).filter(BinanceEvent.title == ev["title"]).first()
            if not exists:
                event = BinanceEvent(
                    title=ev["title"],
                    description=ev.get("description", ""),
                    event_type=ev["event_type"],
                    url=ev.get("url"),
                    event_date=ev.get("event_date"),
                    is_active=True
                )
                self.db.add(event)
                saved_count += 1
        self.db.commit()
        return saved_count
    
    def get_active_events(self, limit: int = 20) -> List[BinanceEvent]:
        return self.db.query(BinanceEvent)\
            .filter(BinanceEvent.is_active == True)\
            .order_by(BinanceEvent.detected_at.desc())\
            .limit(limit).all()
    
    def mark_event_inactive(self, event_id: int):
        event = self.db.query(BinanceEvent).filter_by(id=event_id).first()
        if event:
            event.is_active = False
            self.db.commit()