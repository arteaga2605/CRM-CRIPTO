from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models import init_db, SessionLocal
from app.api import clientes, interacciones, oportunidades, tareas
from app.services.exchange_sync import ExchangeConnector

app = FastAPI(
    title="Crypto CRM",
    description="Tratando criptomonedas como clientes - Sistema de gestion de portafolio",
    version="1.0.0"
)

# CORS para dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar DB
init_db()

# Routers
app.include_router(clientes.router)
app.include_router(interacciones.router)
app.include_router(oportunidades.router)
app.include_router(tareas.router)

# Dependencia para obtener DB
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
            "precios": "/precios/{symbol}",
            "ticker": "/ticker/{symbol}"
        }
    }

@app.get("/precios/{symbol}")
def obtener_precio_real(symbol: str, vs: str = "USDT"):
    """
    Obtiene el precio actual de una criptomoneda desde Binance (API pública).
    """
    connector = ExchangeConnector()
    precio = connector.obtener_precio(symbol.upper(), vs)
    return {"symbol": symbol.upper(), "price": precio, "vs_currency": vs}

@app.get("/ticker/{symbol}")
def obtener_ticker_real(symbol: str, vs: str = "USDT"):
    """
    Obtiene información completa del ticker (precio, cambio 24h, volumen, etc.)
    """
    connector = ExchangeConnector()
    ticker = connector.obtener_ticker(symbol.upper(), vs)
    return ticker

@app.get("/velas/{symbol}")
def obtener_velas(symbol: str, timeframe: str = "1h", limit: int = 100, vs: str = "USDT"):
    """
    Obtiene velas OHLCV históricas.
    """
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