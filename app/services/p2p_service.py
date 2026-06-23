"""
Servicio para consultar el mercado P2P de Binance.
Obtiene anuncios de compra y venta, y calcula spreads.
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class P2PService:
    """Servicio para interactuar con la API pública de Binance P2P."""
    
    # Endpoint público (no requiere API key)
    P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Monedas y fiats soportados
    SUPPORTED_ASSETS = ["USDT", "BTC", "ETH", "BNB"]
    SUPPORTED_FIATS = ["ARS", "MXN", "COP", "PEN", "CLP", "BRL", "VES", "USD"]
    
    @staticmethod
    def get_orders(asset: str = "USDT", fiat: str = "ARS", trade_type: str = "BUY", rows: int = 20) -> List[Dict]:
        """
        Obtiene anuncios de Binance P2P para un par dado.
        trade_type: "BUY" (anuncios donde el usuario QUIERE COMPRAR cripto) 
                    "SELL" (anuncios donde el usuario QUIERE VENDER cripto)
        """
        if asset not in P2PService.SUPPORTED_ASSETS:
            asset = "USDT"
        if fiat not in P2PService.SUPPORTED_FIATS:
            fiat = "ARS"
        
        payload = {
            "asset": asset,
            "fiat": fiat,
            "tradeType": trade_type,
            "page": 1,
            "rows": rows,
            "payTypes": []
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        try:
            resp = requests.post(P2PService.P2P_URL, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "000000" and "data" in data:
                    return data["data"]
                else:
                    logger.error(f"Error en respuesta P2P: {data}")
                    return []
            else:
                logger.error(f"HTTP {resp.status_code} en P2P")
                return []
        except Exception as e:
            logger.error(f"Excepción en P2P: {e}")
            return []
    
    @staticmethod
    def get_best_prices(asset: str = "USDT", fiat: str = "ARS") -> Dict[str, Any]:
        """
        Obtiene los mejores precios de compra y venta para un par.
        
        - buy_price: mejor precio al que PODEMOS COMPRAR cripto (anuncios SELL, el más bajo)
        - sell_price: mejor precio al que PODEMOS VENDER cripto (anuncios BUY, el más alto)
        - spread = sell_price - buy_price (positivo = oportunidad de arbitraje)
        """
        # Anuncios de venta (ellos venden, nosotros compramos) - nos interesa el precio más bajo
        sell_orders = P2PService.get_orders(asset, fiat, "SELL", rows=5)
        # Anuncios de compra (ellos compran, nosotros vendemos) - nos interesa el precio más alto
        buy_orders = P2PService.get_orders(asset, fiat, "BUY", rows=5)
        
        # El mejor precio para comprar es el más bajo de los anuncios SELL
        best_buy_price = min([float(o["adv"]["price"]) for o in sell_orders]) if sell_orders else 0.0
        # El mejor precio para vender es el más alto de los anuncios BUY
        best_sell_price = max([float(o["adv"]["price"]) for o in buy_orders]) if buy_orders else 0.0
        
        spread_abs = best_sell_price - best_buy_price
        spread_pct = (spread_abs / best_buy_price * 100) if best_buy_price > 0 else 0.0
        
        return {
            "asset": asset,
            "fiat": fiat,
            "buy_price": best_buy_price,   # Precio al que podemos comprar (más bajo)
            "sell_price": best_sell_price, # Precio al que podemos vender (más alto)
            "spread_abs": round(spread_abs, 2),
            "spread_pct": round(spread_pct, 2),
            "buy_orders": buy_orders[:5],   # Anuncios de compra (para mostrar)
            "sell_orders": sell_orders[:5], # Anuncios de venta (para mostrar)
            "timestamp": datetime.utcnow().isoformat()
        }