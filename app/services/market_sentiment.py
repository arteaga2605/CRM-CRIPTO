"""
Servicio de sentimiento de mercado y tendencia usando datos de Binance.
"""
import requests
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class MarketSentimentService:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"

    def obtener_tendencia(self, symbol: str = "BTCUSDT") -> Dict[str, any]:
        """
        Calcula la tendencia basada en el precio actual vs media móvil simple de 20 períodos.
        Retorna: {'tendencia': 'alcista'|'bajista'|'neutral', 'porcentaje': float, 'descripcion': str}
        """
        try:
            # Obtener velas de 1 hora para los últimos 20 períodos
            url = f"{self.base_url}/klines"
            params = {
                "symbol": symbol,
                "interval": "1h",
                "limit": 20
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if not data:
                return {"tendencia": "neutral", "porcentaje": 0, "descripcion": "No hay datos suficientes"}
            
            precios_cierre = [float(candle[4]) for candle in data]
            precio_actual = precios_cierre[-1]
            media_movil = sum(precios_cierre) / len(precios_cierre)
            
            diferencia_pct = ((precio_actual - media_movil) / media_movil) * 100
            
            if diferencia_pct > 1.5:
                tendencia = "alcista"
                descripcion = "Precio por encima de la media móvil (1h)"
            elif diferencia_pct < -1.5:
                tendencia = "bajista"
                descripcion = "Precio por debajo de la media móvil (1h)"
            else:
                tendencia = "neutral"
                descripcion = "Precio cerca de la media móvil"
            
            return {
                "tendencia": tendencia,
                "porcentaje": round(diferencia_pct, 2),
                "descripcion": descripcion,
                "precio_actual": precio_actual,
                "media_movil_20": round(media_movil, 2)
            }
        except Exception as e:
            return {"tendencia": "neutral", "porcentaje": 0, "descripcion": f"Error: {str(e)}"}

    def obtener_sentimiento(self, symbol: str = "BTCUSDT") -> Dict[str, any]:
        """
        Calcula un sentimiento basado en el cambio de precio 24h, volumen y variación.
        Retorna: {'sentimiento': 'positivo'|'negativo'|'neutral', 'puntaje': float, 'descripcion': str}
        """
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {"symbol": symbol}
            response = requests.get(url, params=params)
            data = response.json()
            
            cambio_pct = float(data.get("priceChangePercent", 0))
            volumen = float(data.get("quoteVolume", 0))
            cambios_altos_bajos = float(data.get("highPrice", 0)) - float(data.get("lowPrice", 0))
            
            # Puntaje de sentimiento: -100 a 100
            puntaje = cambio_pct  # base: cambio porcentual
            # Si volumen es alto, amplifica la confianza
            if volumen > 1_000_000_000:  # más de 1B USD
                puntaje = puntaje * 1.5 if puntaje > 0 else puntaje * 1.2
            # Limitar
            puntaje = max(-100, min(100, puntaje))
            
            if puntaje > 5:
                sentimiento = "positivo"
                descripcion = f"Mercado con fuerte impulso alcista (+{cambio_pct:.1f}%)"
            elif puntaje < -5:
                sentimiento = "negativo"
                descripcion = f"Mercado con presión bajista ({cambio_pct:.1f}%)"
            else:
                sentimiento = "neutral"
                descripcion = f"Mercado lateral (variación {cambio_pct:.1f}%)"
            
            return {
                "sentimiento": sentimiento,
                "puntaje": round(puntaje, 2),
                "descripcion": descripcion,
                "cambio_24h": cambio_pct,
                "volumen_24h_usd": round(volumen, 2)
            }
        except Exception as e:
            return {"sentimiento": "neutral", "puntaje": 0, "descripcion": f"Error: {str(e)}"}

    def obtener_indicador_flecha(self, symbol: str = "BTCUSDT") -> Dict[str, any]:
        """
        Devuelve la flecha según la tendencia y el cambio 24h.
        """
        tendencia = self.obtener_tendencia(symbol)
        sentimiento = self.obtener_sentimiento(symbol)
        
        flecha = "➡️"
        if tendencia["tendencia"] == "alcista" and sentimiento["sentimiento"] == "positivo":
            flecha = "🔼"
        elif tendencia["tendencia"] == "bajista" and sentimiento["sentimiento"] == "negativo":
            flecha = "🔽"
        elif tendencia["tendencia"] == "alcista":
            flecha = "↗️"
        elif tendencia["tendencia"] == "bajista":
            flecha = "↙️"
        
        color = "🟢" if "alcista" in tendencia["tendencia"] or sentimiento["sentimiento"] == "positivo" else "🔴" if "bajista" in tendencia["tendencia"] else "🟡"
        
        return {
            "flecha": f"{color} {flecha}",
            "tendencia": tendencia["tendencia"],
            "sentimiento": sentimiento["sentimiento"],
            "descripcion": f"{tendencia['descripcion']} | {sentimiento['descripcion']}"
        }