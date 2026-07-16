from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import os
import shutil
from fastapi.responses import FileResponse

from app.models import init_db, SessionLocal, ClienteCripto
from app.api import clientes, interacciones, oportunidades, tareas, lotes, deportes
from app.services.exchange_sync import ExchangeConnector
from app.services.analytics import AnalyticsService
from app.services.binance_events import BinanceEventService
from app.services.notification_service import NotificationService
from app.services.crm_service import CRMService
from app.services.p2p_service import P2PService

app = FastAPI(
    title="Crypto CRM",
    description="Tratando criptomonedas como clientes - Sistema de gestion de portafolio",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(clientes.router)
app.include_router(interacciones.router)
app.include_router(oportunidades.router)
app.include_router(tareas.router)
app.include_router(lotes.router)
app.include_router(deportes.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== TAREAS PROGRAMADAS (APScheduler) ==========
def actualizar_precios_automatico():
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
        print(f"[SCHEDULER] Precios actualizados automáticamente: {actualizados} de {len(clientes)} clientes.")
    except Exception as e:
        print(f"[SCHEDULER] Error actualizando precios: {e}")
    finally:
        db.close()

def generar_notificaciones_automaticas():
    db = SessionLocal()
    try:
        service = NotificationService(db)
        results = service.generate_all_alerts()
        print(f"[SCHEDULER] Notificaciones generadas: {results}")
    except Exception as e:
        print(f"[SCHEDULER] Error generando notificaciones: {e}")
    finally:
        db.close()

def actualizar_precios_p2p():
    try:
        for asset in ["USDT", "BTC"]:
            for fiat in ["ARS", "MXN"]:
                datos = P2PService.get_best_prices(asset, fiat)
                print(f"[P2P] {asset}/{fiat}: spread {datos['spread_pct']}%")
    except Exception as e:
        print(f"[P2P] Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=actualizar_precios_automatico,
    trigger=IntervalTrigger(hours=1),
    id='actualizar_precios_hora',
    replace_existing=True
)
scheduler.add_job(
    func=generar_notificaciones_automaticas,
    trigger=IntervalTrigger(minutes=5),
    id='notificaciones_auto',
    replace_existing=True
)
scheduler.add_job(
    func=actualizar_precios_p2p,
    trigger=IntervalTrigger(minutes=5),
    id='actualizar_p2p',
    replace_existing=True
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ========== ENDPOINTS ==========
@app.get("/")
def root():
    return {
        "message": "Crypto CRM API",
        "docs": "/docs",
        "endpoints": {
            "clientes": "/clientes",
            "interacciones": "/interacciones",
            "oportunidades": "/oportunidades",
            "tareas": "/tareas",
            "lotes": "/lotes/cliente/{symbol}",
            "precios": "/precios/{symbol}",
            "ticker": "/ticker/{symbol}",
            "daily-pnl": "/analytics/daily-pnl",
            "performance-by-category": "/analytics/performance-by-category",
            "realized-pnl-summary": "/analytics/realized-pnl-summary",
            "binance-events": "/binance-events",
            "notifications": "/notifications",
            "notifications/read": "/notifications/read (POST)",
            "p2p": "/p2p/best-prices",
            "deportes": "/deportes",
            "deportes/retiros": "/deportes/retiros",
            "export-db": "/export-db (GET)"
        }
    }

@app.get("/precios/{symbol}")
def obtener_precio_real(symbol: str, vs: str = "USDT"):
    connector = ExchangeConnector()
    precio = connector.obtener_precio(symbol.upper(), vs)
    return {"symbol": symbol.upper(), "price": precio, "vs_currency": vs}

@app.get("/ticker/{symbol}")
def obtener_ticker_real(symbol: str, vs: str = "USDT"):
    connector = ExchangeConnector()
    ticker = connector.obtener_ticker(symbol.upper(), vs)
    return ticker

@app.get("/velas/{symbol}")
def obtener_velas(symbol: str, timeframe: str = "1h", limit: int = 100, vs: str = "USDT"):
    connector = ExchangeConnector()
    velas = connector.obtener_velas(symbol.upper(), timeframe, limit, vs)
    return {"symbol": symbol.upper(), "timeframe": timeframe, "data": velas}

@app.get("/dashboard/resumen")
def resumen_dashboard(db: Session = Depends(get_db)):
    from app.services.crm_service import CRMService
    crm = CRMService(db)
    analytics = AnalyticsService(db)
    return {
        "resumen": crm.resumen_portafolio(),
        "top_performers": [
            {"symbol": c.symbol, "roi": float(c.roi_porcentaje)}
            for c in crm.top_performers(5)
        ],
        "alertas": analytics.alertas_inteligentes(),
        "distribucion": analytics.distribucion_portafolio()[:5]
    }

@app.get("/analytics/daily-pnl")
def get_daily_pnl(days: int = 7, db: Session = Depends(get_db)):
    analytics = AnalyticsService(db)
    return analytics.daily_pnl(days)

@app.get("/analytics/performance-by-category")
def get_performance_by_category(db: Session = Depends(get_db)):
    analytics = AnalyticsService(db)
    return analytics.rendimiento_por_categoria()

@app.get("/analytics/realized-pnl-summary")
def get_realized_pnl_summary(db: Session = Depends(get_db)):
    analytics = AnalyticsService(db)
    return analytics.ganancias_perdidas_realizadas()

@app.get("/p2p/best-prices")
def get_p2p_best_prices(asset: str = "USDT", fiat: str = "ARS"):
    return P2PService.get_best_prices(asset, fiat)

@app.get("/binance-events")
def get_binance_events(limit: int = 20, db: Session = Depends(get_db)):
    service = BinanceEventService(db)
    events = service.get_active_events(limit)
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "event_type": e.event_type,
            "url": e.url,
            "event_date": e.event_date.isoformat() if e.event_date else None,
            "detected_at": e.detected_at.isoformat()
        }
        for e in events
    ]

@app.post("/binance-events/update")
def update_binance_events(db: Session = Depends(get_db)):
    service = BinanceEventService(db)
    saved = service.update_events()
    if saved == 0:
        return {"message": "No se encontraron nuevos eventos."}
    return {"message": f"Actualización completada. {saved} nuevos eventos guardados."}

# ========== NOTIFICACIONES ==========
@app.get("/notifications")
def get_notifications(limit: int = 20, unread_only: bool = False, db: Session = Depends(get_db)):
    service = NotificationService(db)
    if unread_only:
        notifs = service.get_unread_notifications(limit)
    else:
        notifs = service.get_recent_notifications(limit)
    return [
        {
            "id": n.id,
            "message": n.message,
            "type": n.type,
            "related_id": n.related_id,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        }
        for n in notifs
    ]

@app.post("/notifications/read/{notif_id}")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    service = NotificationService(db)
    if service.mark_as_read(notif_id):
        return {"message": "Notificación marcada como leída"}
    else:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

@app.post("/notifications/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    service = NotificationService(db)
    service.mark_all_as_read()
    return {"message": "Todas las notificaciones marcadas como leídas"}

@app.post("/notifications/generate")
def trigger_notifications(db: Session = Depends(get_db)):
    service = NotificationService(db)
    results = service.generate_all_alerts()
    return results

# ========== EXPORTAR BASE DE DATOS ==========
@app.get("/export-db")
def export_db():
    db_path = "crypto_crm.db"
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    temp_path = "crypto_crm_temp.db"
    try:
        shutil.copy2(db_path, temp_path)
        return FileResponse(
            temp_path,
            media_type="application/x-sqlite3",
            filename="crypto_crm_backup.db"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
