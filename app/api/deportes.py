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