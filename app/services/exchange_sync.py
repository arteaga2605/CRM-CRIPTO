"""
Conector de exchanges usando CCXT.
Sincroniza portafolio real con el CRM.
Ahora con soporte para API pública de Binance (sin keys).
"""
from typing import Dict, List, Optional
import ccxt
from decimal import Decimal
from datetime import datetime
from app.models import ClienteCripto, TipoInteraccion
from app.services.crm_service import CRMService

class ExchangeConnector:
    def __init__(self, api_key: str = None, secret: str = None, exchange_id: str = "binance"):
        """
        Si no se proporcionan api_key/secret, se usa el modo público (solo lectura de mercado).
        """
        exchange_class = getattr(ccxt, exchange_id)
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        if api_key and secret:
            config['apiKey'] = api_key
            config['secret'] = secret
        self.exchange = exchange_class(config)
        self.is_authenticated = bool(api_key and secret)

    def obtener_precio(self, symbol: str, vs_currency: str = "USDT") -> float:
        """
        Obtiene precio actual de una moneda en la moneda de cotización (ej: BTC/USDT).
        Modo público, sin necesidad de API key.
        """
        try:
            ticker = self.exchange.fetch_ticker(f"{symbol}/{vs_currency}")
            return ticker['last'] or ticker['close'] or 0.0
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return 0.0

    def obtener_ticker(self, symbol: str, vs_currency: str = "USDT") -> Dict:
        """
        Devuelve información completa del ticker (precio, cambio 24h, volumen, etc.)
        """
        try:
            ticker = self.exchange.fetch_ticker(f"{symbol}/{vs_currency}")
            return {
                "symbol": symbol,
                "last": ticker.get('last', 0),
                "bid": ticker.get('bid', 0),
                "ask": ticker.get('ask', 0),
                "change": ticker.get('change', 0),
                "percentage": ticker.get('percentage', 0),
                "volume": ticker.get('baseVolume', 0),
                "quoteVolume": ticker.get('quoteVolume', 0),
                "high": ticker.get('high', 0),
                "low": ticker.get('low', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error obteniendo ticker de {symbol}: {e}")
            return {}

    def obtener_velas(self, symbol: str, timeframe: str = "1h", limit: int = 100, vs_currency: str = "USDT") -> List[Dict]:
        """
        Obtiene velas (OHLCV) históricas.
        timeframe: '1m', '5m', '15m', '30m', '1h', '4h', '1d', etc.
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(f"{symbol}/{vs_currency}", timeframe=timeframe, limit=limit)
            velas = []
            for candle in ohlcv:
                velas.append({
                    "timestamp": candle[0],
                    "datetime": datetime.utcfromtimestamp(candle[0] / 1000).isoformat(),
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })
            return velas
        except Exception as e:
            print(f"Error obteniendo velas de {symbol}: {e}")
            return []

    def obtener_balance(self) -> Dict[str, float]:
        """Obtiene balance actual del exchange (solo si está autenticado)."""
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener balance.")
        balance = self.exchange.fetch_balance()
        return {
            k: float(v['total']) 
            for k, v in balance.items() 
            if isinstance(v, dict) and float(v.get('total', 0)) > 0
        }

    def obtener_historial_trades(self, symbol: str, limit: int = 100) -> List[dict]:
        """Obtiene historial de trades del exchange (solo autenticado)."""
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener historial de trades.")
        try:
            trades = self.exchange.fetch_my_trades(f"{symbol}/USDT", limit=limit)
            return trades
        except Exception as e:
            print(f"Error obteniendo trades de {symbol}: {e}")
            return []

    def sincronizar_portafolio(self, crm: CRMService):
        """
        Sincroniza portafolio real con el CRM (requiere autenticación).
        Registra monedas nuevas y actualiza precios.
        """
        if not self.is_authenticated:
            print("No autenticado. No se puede sincronizar portafolio.")
            return False

        balance = self.obtener_balance()
        for symbol, cantidad in balance.items():
            if symbol in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                continue
            if cantidad <= 0:
                continue
            precio = self.obtener_precio(symbol)
            if precio == 0:
                continue
            cliente = crm.obtener_cliente(symbol)
            if not cliente:
                cliente = crm.registrar_cliente(
                    symbol=symbol,
                    nombre=symbol,
                    categoria="exchange_sync",
                    exchange_principal=self.exchange.id,
                    cantidad_total=Decimal(str(cantidad))
                )
                print(f"[SYNC] Nuevo cliente registrado: {symbol}")
            crm.actualizar_precio_mercado(symbol, precio)
            if not cliente.interacciones:
                crm.crear_tarea(
                    symbol=symbol,
                    tipo="revision_inicial",
                    descripcion=f"{symbol} sincronizado desde exchange. Revisar costo promedio manualmente.",
                    dias=1,
                    prioridad=3
                )
        return True

    def importar_historial(self, crm: CRMService, symbol: str):
        """Importa trades historicos del exchange como interacciones (requiere autenticación)."""
        if not self.is_authenticated:
            raise ValueError("Se requiere autenticación para importar historial.")
        trades = self.obtener_historial_trades(symbol)
        for trade in trades:
            lado = trade.get('side', 'buy')
            tipo = TipoInteraccion.COMPRA if lado == 'buy' else TipoInteraccion.VENTA
            try:
                crm.registrar_interaccion(
                    symbol=symbol.replace('/USDT', ''),
                    tipo=tipo.value,
                    cantidad=trade['amount'],
                    precio=trade['price'],
                    fee=trade.get('fee', {}).get('cost', 0),
                    exchange=self.exchange.id,
                    notas=f"Importado desde exchange - Order: {trade.get('order', 'N/A')}"
                )
            except ValueError:
                pass
        return len(trades)