from typing import Dict, List, Optional
import time
import ccxt
from decimal import Decimal
from datetime import datetime
from app.models import ClienteCripto, TipoInteraccion
from app.services.crm_service import CRMService


class ExchangeConnector:
    """
    NOTA DE OPTIMIZACION:
    Antes cada precio/ticker generaba una llamada de red nueva a Binance,
    y actualizar el portafolio completo hacia una llamada POR CADA moneda,
    una detras de otra (serial). Eso es lo que hacia lenta cada carga.

    Cambios aplicados:
    1) Cache en memoria con TTL corto (por defecto 20s) para precio/ticker
       individuales: si la misma moneda se pide varias veces en poco tiempo
       (por ejemplo por refrescos de Streamlit), no se vuelve a golpear la API.
    2) Nuevo metodo obtener_precios_batch() que usa fetch_tickers() de ccxt,
       trayendo TODOS los precios pedidos en una sola llamada HTTP, en vez de
       una llamada por simbolo. Esto es lo que hay que usar para refrescar
       el portafolio completo (ver main.py).
    """

    def __init__(self, api_key: str = None, secret: str = None,
                 exchange_id: str = "binance", cache_ttl_seconds: int = 20):
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
        self.cache_ttl_seconds = cache_ttl_seconds
        self._precio_cache: Dict[str, tuple] = {}   # symbol -> (precio, timestamp)
        self._ticker_cache: Dict[str, tuple] = {}    # symbol -> (ticker_dict, timestamp)

    def _cache_vigente(self, cache: dict, key: str) -> Optional[any]:
        entry = cache.get(key)
        if not entry:
            return None
        valor, ts = entry
        if time.time() - ts < self.cache_ttl_seconds:
            return valor
        return None

    def obtener_precio(self, symbol: str, vs_currency: str = "USDT") -> float:
        cache_key = f"{symbol}/{vs_currency}"
        cacheado = self._cache_vigente(self._precio_cache, cache_key)
        if cacheado is not None:
            return cacheado
        try:
            ticker = self.exchange.fetch_ticker(cache_key)
            precio = ticker['last'] or ticker['close'] or 0.0
            self._precio_cache[cache_key] = (precio, time.time())
            return precio
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return 0.0

    def obtener_precios_batch(self, symbols: List[str], vs_currency: str = "USDT") -> Dict[str, float]:
        """
        Trae el precio de VARIOS simbolos en UNA sola llamada de red.
        Usar esto en vez de llamar obtener_precio() en un loop.
        """
        if not symbols:
            return {}

        pares = [f"{s}/{vs_currency}" for s in symbols]
        resultado: Dict[str, float] = {}
        pares_a_pedir = []

        # Reusar cache vigente donde exista
        for symbol, par in zip(symbols, pares):
            cacheado = self._cache_vigente(self._precio_cache, par)
            if cacheado is not None:
                resultado[symbol] = cacheado
            else:
                pares_a_pedir.append(par)

        if pares_a_pedir:
            try:
                tickers = self.exchange.fetch_tickers(pares_a_pedir)
                ahora = time.time()
                for par, ticker in tickers.items():
                    symbol = par.split("/")[0]
                    precio = ticker.get('last') or ticker.get('close') or 0.0
                    self._precio_cache[par] = (precio, ahora)
                    resultado[symbol] = precio
            except Exception as e:
                print(f"Error obteniendo precios en lote: {e}")
                # Fallback: si el exchange no soporta fetch_tickers con lista,
                # se completa uno por uno solo para lo que falto.
                for par in pares_a_pedir:
                    symbol = par.split("/")[0]
                    if symbol not in resultado:
                        resultado[symbol] = self.obtener_precio(symbol, vs_currency)

        return resultado

    def obtener_ticker(self, symbol: str, vs_currency: str = "USDT") -> Dict:
        cache_key = f"{symbol}/{vs_currency}"
        cacheado = self._cache_vigente(self._ticker_cache, cache_key)
        if cacheado is not None:
            return cacheado
        try:
            ticker = self.exchange.fetch_ticker(cache_key)
            data = {
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
            self._ticker_cache[cache_key] = (data, time.time())
            return data
        except Exception as e:
            print(f"Error obteniendo ticker de {symbol}: {e}")
            return {}

    def obtener_velas(self, symbol: str, timeframe: str = "1h", limit: int = 100, vs_currency: str = "USDT") -> List[Dict]:
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
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener balance.")
        balance = self.exchange.fetch_balance()
        return {
            k: float(v['total'])
            for k, v in balance.items()
            if isinstance(v, dict) and float(v.get('total', 0)) > 0
        }

    def obtener_historial_trades(self, symbol: str, limit: int = 100) -> List[dict]:
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener historial de trades.")
        try:
            trades = self.exchange.fetch_my_trades(f"{symbol}/USDT", limit=limit)
            return trades
        except Exception as e:
            print(f"Error obteniendo trades de {symbol}: {e}")
            return []

    def sincronizar_portafolio(self, crm: CRMService):
        if not self.is_authenticated:
            print("No autenticado. No se puede sincronizar portafolio.")
            return False
        balance = self.obtener_balance()

        simbolos = [s for s in balance.keys()
                    if s not in ['USDT', 'USDC', 'BUSD', 'FDUSD'] and balance[s] > 0]
        precios = self.obtener_precios_batch(simbolos)

        for symbol in simbolos:
            cantidad = balance[symbol]
            precio = precios.get(symbol, 0.0)
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
