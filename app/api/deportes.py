from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.models import SessionLocal
from app.services.deportes_service import DeportesService

router = APIRouter(prefix="/deportes", tags=["Deportes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class InversionCreate(BaseModel):
    deporte: str
    tipo_mercado: str
    objetivo: str
    capital: float
    ganancia_potencial: float
    perdida_potencial: float
    cuota: Optional[float] = None
    notas: Optional[str] = ""

class RetiroCreate(BaseModel):
    monto: float
    notas: Optional[str] = ""

class InyeccionCreate(BaseModel):
    monto: float
    notas: Optional[str] = ""

@router.post("/", response_model=dict)
def crear(inv: InversionCreate, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    try:
        res = srv.crear_inversion(**inv.dict())
        return {"id": res.id, "objetivo": res.objetivo, "estado": res.estado.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/resumen")
def resumen(db: Session = Depends(get_db)):
    srv = DeportesService(db)
    return srv.obtener_resumen_y_estadisticas()

@router.post("/{inv_id}/liquidar")
def liquidar(inv_id: int, estado: str, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    try:
        res = srv.liquidar_inversion(inv_id, estado)
        return {"id": res.id, "nuevo_estado": res.estado.value, "pnl": float(res.pnl_realizado)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── ENDPOINTS DE RETIRO ───
@router.post("/retiros", response_model=dict)
def crear_retiro(data: RetiroCreate, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    try:
        res = srv.registrar_retiro(monto=data.monto, notas=data.notas or "")
        return {
            "id": res.id,
            "monto": float(res.monto),
            "fecha_retiro": res.fecha_retiro.isoformat(),
            "notas": res.notas,
            "capital_restante": srv._calcular_capital_actual()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retiros")
def listar_retiros(limit: int = 50, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    retiros = srv.obtener_historial_retiros(limit=limit)
    return [
        {
            "id": r.id,
            "monto": float(r.monto),
            "fecha_retiro": r.fecha_retiro.isoformat(),
            "notas": r.notas
        }
        for r in retiros
    ]

# ─── ENDPOINTS DE INYECCION DE CAPITAL (NUEVO) ───
@router.post("/inyecciones", response_model=dict)
def crear_inyeccion(data: InyeccionCreate, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    try:
        res = srv.registrar_inyeccion(monto=data.monto, notas=data.notas or "")
        return {
            "id": res.id,
            "monto": float(res.monto),
            "fecha_inyeccion": res.fecha_inyeccion.isoformat(),
            "notas": res.notas,
            "capital_actual": srv._calcular_capital_actual()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inyecciones")
def listar_inyecciones(limit: int = 50, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    inyecciones = srv.obtener_historial_inyecciones(limit=limit)
    return [
        {
            "id": ic.id,
            "monto": float(ic.monto),
            "fecha_inyeccion": ic.fecha_inyeccion.isoformat(),
            "notas": ic.notas
        }
        for ic in inyecciones
    ]

# ─── PnL DIARIO ───
@router.get("/pnl-diario")
def pnl_diario(dias: int = 7, db: Session = Depends(get_db)):
    srv = DeportesService(db)
    return srv.pnl_diario(dias=dias)
