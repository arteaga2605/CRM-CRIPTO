"""
Servicio para detectar eventos de Binance (Launchpool, Megadrop, nuevos listados)
mediante el feed RSS oficial (estable y sin bloqueo).
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import BinanceEvent

class BinanceEventScraper:
    """Extrae eventos de Binance desde el feed RSS oficial."""
    
    RSS_URL = "https://www.binance.com/en/support/announcement/rss?c=48"
    
    @staticmethod
    def fetch_events() -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        events = []
        try:
            resp = requests.get(BinanceEventScraper.RSS_URL, headers=headers, timeout=15)
            if resp.status_code == 200:
                # Parsear XML
                root = ET.fromstring(resp.content)
                # Namespace del feed RSS de Atom (usado por Binance)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                # Buscar todas las entradas <entry>
                entries = root.findall('.//atom:entry', ns)
                for entry in entries:
                    title_elem = entry.find('atom:title', ns)
                    link_elem = entry.find('atom:link', ns)
                    date_elem = entry.find('atom:updated', ns)
                    if title_elem is not None and link_elem is not None:
                        title = title_elem.text
                        link = link_elem.get('href')
                        if not link.startswith('http'):
                            link = "https://www.binance.com" + link
                        event_date = None
                        if date_elem is not None and date_elem.text:
                            try:
                                date_str = date_elem.text.replace('Z', '+00:00')
                                event_date = datetime.fromisoformat(date_str)
                            except:
                                pass
                        # Determinar tipo de evento por palabras clave
                        event_type = "announcement"
                        title_lower = title.lower()
                        if "launchpool" in title_lower:
                            event_type = "launchpool"
                        elif "megadrop" in title_lower:
                            event_type = "megadrop"
                        elif "listing" in title_lower or "will list" in title_lower:
                            event_type = "new_listing"
                        events.append({
                            "title": title,
                            "description": "",
                            "event_type": event_type,
                            "url": link,
                            "event_date": event_date
                        })
                # Limitar a los 20 más recientes (el feed ya viene ordenado)
                events = events[:20]
            else:
                print(f"Error HTTP {resp.status_code} al acceder al feed RSS de Binance.")
        except Exception as e:
            print(f"Error al procesar el feed RSS: {e}")
        return events

class BinanceEventService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_events(self) -> int:
        """Actualiza la base de datos con eventos reales del feed RSS."""
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