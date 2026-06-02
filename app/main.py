from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models import init_db, SessionLocal
from app.api import clientes, interacciones, oportunidades, tareas, lotes
from app.services.exchange_sync import ExchangeConnector
from app.services.analytics import AnalyticsService
from app.services.binance_events import BinanceEventService

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
            "binance-events": "/binance-events",
            "binance-events-update": "/binance-events/update (POST)",
            "historical-ohlcv": "/historical-ohlcv/{symbol}"
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
    from app.services.analytics import AnalyticsService

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

@app.get("/analytics/historial-transacciones")
def get_historial_transacciones(db: Session = Depends(get_db)):
    """Retorna todas las interacciones (compras/ventas) con detalles."""
    analytics = AnalyticsService(db)
    return analytics.historial_transacciones()

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
        return {"message": "No se encontraron nuevos eventos. Es posible que Binance haya cambiado su estructura o no haya novedades."}
    return {"message": f"Actualización completada. {saved} nuevos eventos guardados."}

@app.get("/historical-ohlcv/{symbol}")
def get_historical_ohlcv(symbol: str, days: int = 7, timeframe: str = "1h"):
    """Retorna velas históricas de Binance para análisis."""
    connector = ExchangeConnector()
    # Calcular límite de velas: 24 horas * días
    limit = 24 * days if timeframe == "1h" else 24 * days * 4  # si fuera 15m, etc. Por simplicidad, usamos 1h
    velas = connector.obtener_velas(symbol.upper(), timeframe, limit)
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "days": days,
        "data": velas
    }