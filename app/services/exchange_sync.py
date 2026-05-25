"""
Conector de exchanges usando CCXT.
Sincroniza portafolio real con el CRM.
"""
from typing import Dict, List
import ccxt
from decimal import Decimal
from app.models import ClienteCripto, TipoInteraccion
from app.services.crm_service import CRMService

class ExchangeConnector:
    def __init__(self, api_key: str, secret: str, exchange_id: str = "binance"):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

    def obtener_balance(self) -> Dict[str, float]:
        """Obtiene balance actual del exchange"""
        balance = self.exchange.fetch_balance()
        return {
            k: float(v['total']) 
            for k, v in balance.items() 
            if isinstance(v, dict) and float(v.get('total', 0)) > 0
        }

    def obtener_precio(self, symbol: str) -> float:
        """Obtiene precio actual de una moneda en USDT"""
        try:
            ticker = self.exchange.fetch_ticker(f"{symbol}/USDT")
            return ticker['last']
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return 0.0

    def obtener_historial_trades(self, symbol: str, limit: int = 100) -> List[dict]:
        """Obtiene historial de trades del exchange"""
        try:
            trades = self.exchange.fetch_my_trades(f"{symbol}/USDT", limit=limit)
            return trades
        except Exception as e:
            print(f"Error obteniendo trades de {symbol}: {e}")
            return []

    def sincronizar_portafolio(self, crm: CRMService):
        """
        Sincroniza portafolio real con el CRM.
        Registra monedas nuevas y actualiza precios.
        """
        balance = self.obtener_balance()

        for symbol, cantidad in balance.items():
            if symbol in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                continue  # Skip stablecoins como clientes

            if cantidad <= 0:
                continue

            precio = self.obtener_precio(symbol)
            if precio == 0:
                continue

            # Verificar si existe en CRM
            cliente = crm.obtener_cliente(symbol)
            if not cliente:
                # Registrar nueva moneda
                cliente = crm.registrar_cliente(
                    symbol=symbol,
                    nombre=symbol,
                    categoria="exchange_sync",
                    exchange_principal=self.exchange.id,
                    cantidad_total=Decimal(str(cantidad))
                )
                print(f"[SYNC] Nuevo cliente registrado: {symbol}")

            # Actualizar precio y metricas
            crm.actualizar_precio_mercado(symbol, precio)

            # Crear tarea de revision si es nueva
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
        """Importa trades historicos del exchange como interacciones"""
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
                pass  # Cliente no existe, saltar

        return len(trades)
