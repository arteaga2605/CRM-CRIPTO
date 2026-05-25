from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.models import init_db
from app.api import clientes, interacciones, oportunidades, tareas

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

@app.get("/")
def root():
    return {
        "message": "Crypto CRM API",
        "docs": "/docs",
        "endpoints": {
            "clientes": "/clientes",
            "interacciones": "/interacciones",
            "oportunidades": "/oportunidades",
            "tareas": "/tareas"
        }
    }

@app.get("/dashboard/resumen")
def resumen_dashboard(db=Depends(clientes.get_db)):
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