# app/services/crypto_news_service.py
import requests
from typing import List, Dict, Any

class CryptoNewsAPI:
    """Servicio para interactuar con la API gratuita de noticias crypto."""
    BASE_URL = "https://cryptocurrency.cv/api"

    @staticmethod
    def fetch_binance_news(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene las últimas noticias del mundo crypto y filtra las relevantes para Binance.
        """
        news_articles = []
        try:
            # 1. Obtener últimas noticias generales
            response = requests.get(f"{CryptoNewsAPI.BASE_URL}/news?limit=50", timeout=15)
            if response.status_code == 200:
                data = response.json()
                all_articles = data.get("articles", [])
                
                # 2. Palabras clave para detectar eventos de Binance
                keywords = [
                    "binance", "launchpool", "megadrop", "new listing", 
                    "will list", "new token", "launch", "will be listed"
                ]
                
                # 3. Filtrar noticias que contengan las palabras clave en el título o descripción
                for article in all_articles:
                    title = article.get("title", "").lower()
                    description = article.get("description", "").lower()
                    if any(kw in title or kw in description for kw in keywords):
                        # 4. Determinar el tipo de evento
                        event_type = "announcement"
                        if "launchpool" in title:
                            event_type = "launchpool"
                        elif "megadrop" in title:
                            event_type = "megadrop"
                        elif "new listing" in title or "will list" in title:
                            event_type = "new_listing"
                        
                        news_articles.append({
                            "title": article.get("title", "Sin título"),
                            "description": article.get("description", ""),
                            "event_type": event_type,
                            "url": article.get("url", "#"),
                            "published_at": article.get("published_at")
                        })
                # Devolver solo los 'limit' más recientes
                return news_articles[:limit]
            else:
                print(f"Error al obtener noticias: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error en la conexión con CryptoNewsAPI: {e}")
            return []