from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import SessionLocal
from app.schemas import OportunidadCreate, OportunidadResponse
from app.services.crm_service import CRMService

router = APIRouter(prefix="/oportunidades", tags=["Oportunidades"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OportunidadResponse)
def crear_oportunidad(opp: OportunidadCreate, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.crear_oportunidad(
            symbol=opp.cliente_symbol,
            tipo=opp.tipo,
            entrada=float(opp.precio_entrada),
            objetivo=float(opp.precio_objetivo),
            stop=float(opp.precio_stop_loss),
            monto_planificado=float(opp.monto_planificado),
            confianza=opp.confianza,
            notas=opp.notas_analisis
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[OportunidadResponse])
def listar_oportunidades(estado: Optional[str] = "abierta", db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.oportunidades_por_estado(estado)

@router.post("/{opp_id}/cerrar")
def cerrar_oportunidad(opp_id: int, estado: str, pnl: Optional[float] = None, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.cerrar_oportunidad(opp_id, estado, pnl)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
