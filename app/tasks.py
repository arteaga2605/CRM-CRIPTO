"""
Tareas en background con Celery.
Ejecuta: celery -A app.tasks worker --beat --loglevel=info
"""
from celery import Celery
from sqlalchemy.orm import sessionmaker
from app.models import engine, ClienteCripto, EstadoCliente, Tarea
from app.services.crm_service import CRMService
from datetime import datetime, timedelta

app = Celery('crypto_crm', broker='redis://localhost:6379/0')

SessionLocal = sessionmaker(bind=engine)

@app.task
def verificar_alertas_programadas():
    """Revisa cada hora si algun cliente necesita atencion"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        
        # Generar alertas inteligentes
        from app.services.analytics import AnalyticsService
        analytics = AnalyticsService(db)
        alertas = analytics.alertas_inteligentes()
        
        # Crear tareas automaticas basadas en alertas
        for alerta in alertas:
            if alerta["nivel"] in ["CRITICO", "ADVERTENCIA"]:
                # Verificar si ya existe tarea similar pendiente
                existente = db.query(Tarea).filter(
                    Tarea.tipo_tarea == alerta["accion_sugerida"],
                    Tarea.completada == False
                ).join(ClienteCripto).filter(ClienteCripto.symbol == alerta["symbol"]).first()
                
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
    """Actualiza precios de mercado (requiere conector configurado)"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        clientes = db.query(ClienteCripto).filter(ClienteCripto.cantidad_total > 0).all()
        
        # Nota: En produccion usarias CCXT aqui
        # Por ahora, simplemente marca que necesitan actualizacion
        for cliente in clientes:
            crm.crear_tarea(
                symbol=cliente.symbol,
                tipo="actualizar_precio",
                descripcion=f"Actualizar precio de mercado de {cliente.symbol}",
                dias=0,
                prioridad=3
            )
        
        return f"Sincronizacion programada para {len(clientes)} clientes"
    finally:
        db.close()

@app.task
def reporte_diario():
    """Genera reporte diario del portafolio"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        resumen = crm.resumen_portafolio()
        
        # En produccion, enviarias esto por email/Telegram
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