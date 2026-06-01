"""
Tareas en background con Celery.
Ejecuta: celery -A app.tasks worker --beat --loglevel=info
"""
from celery import Celery
from sqlalchemy.orm import sessionmaker
from app.models import engine, ClienteCripto, EstadoCliente, Tarea
from app.services.crm_service import CRMService
from app.services.analytics import AnalyticsService
from app.services.exchange_sync import ExchangeConnector
from app.services.binance_events import BinanceEventService
from datetime import datetime, timedelta

app = Celery('crypto_crm', broker='redis://localhost:6379/0')

SessionLocal = sessionmaker(bind=engine)

@app.task
def verificar_alertas_programadas():
    """Revisa cada hora si algun cliente necesita atencion"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        analytics = AnalyticsService(db)

        alertas = analytics.alertas_inteligentes()

        for alerta in alertas:
            if alerta["nivel"] in ["CRITICO", "ADVERTENCIA"]:
                existente = db.query(Tarea).filter(
                    Tarea.cliente.has(symbol=alerta["symbol"]),
                    Tarea.tipo_tarea == alerta["accion_sugerida"],
                    Tarea.completada == False
                ).first()

                if not existente:
                    crm.crear_tarea(
                        symbol=alerta["symbol"],
                        tipo=alerta["accion_sugerida"],
                        descripcion=alerta["mensaje"],
                        dias=0 if alerta["nivel"] == "CRITICO" else 1,
                        prioridad=1 if alerta["nivel"] == "CRITICO" else 2
                    )

        return f"Alertas verificadas: {len(alertas)} generadas"
    finally:
        db.close()

@app.task
def sincronizar_precios():
    """
    Actualiza precios de mercado para todos los clientes con cantidad > 0
    usando la API pública de Binance.
    """
    db = SessionLocal()
    try:
        crm = CRMService(db)
        connector = ExchangeConnector()
        clientes = db.query(ClienteCripto).filter(ClienteCripto.cantidad_total > 0).all()

        actualizados = 0
        for cliente in clientes:
            precio = connector.obtener_precio(cliente.symbol)
            if precio > 0:
                crm.actualizar_precio_mercado(cliente.symbol, precio)
                actualizados += 1
            else:
                print(f"No se pudo obtener precio para {cliente.symbol}")

        return f"Precios actualizados para {actualizados} de {len(clientes)} clientes"
    finally:
        db.close()

@app.task
def reporte_diario():
    """Genera reporte diario del portafolio"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        resumen = crm.resumen_portafolio()

        reporte = f"""
📊 REPORTE DIARIO CRM CRYPTO
━━━━━━━━━━━━━━━━━━━━━━
Clientes activos: {resumen['clientes_activos']}
VIP: {resumen['clientes_vip']} | Peligro: {resumen['clientes_peligro']}
PnL Total: ${resumen['pnl_total']}
ROI: {resumen['roi_porcentaje']}%
Tareas pendientes: {resumen['tareas_pendientes']}
Oportunidades abiertas: {resumen['oportunidades_abiertas']}
━━━━━━━━━━━━━━━━━━━━━━
        """
        return reporte
    finally:
        db.close()

@app.task
def fetch_binance_events():
    """Tarea programada para buscar eventos nuevos de Binance (cada 6 horas)."""
    db = SessionLocal()
    try:
        service = BinanceEventService(db)
        saved = service.update_events()
        return f"Se encontraron {saved} nuevos eventos de Binance."
    except Exception as e:
        return f"Error actualizando eventos de Binance: {e}"
    finally:
        db.close()