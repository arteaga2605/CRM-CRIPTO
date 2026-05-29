from fastapi import APIRouter, Depends, HTTPException, Query
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
def listar_oportunidades(
    estado: Optional[str] = Query(None, description="Filtrar por estado (abierta, ejecutada, cancelada)"),
    cliente_symbol: Optional[str] = Query(None, description="Filtrar por símbolo del cliente"),
    db: Session = Depends(get_db)
):
    crm = CRMService(db)
    if cliente_symbol:
        cliente = crm.obtener_cliente(cliente_symbol)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if estado:
            return crm.oportunidades_por_estado_cliente(cliente_symbol, estado)
        else:
            return crm.oportunidades_por_cliente(cliente_symbol)
    if estado:
        return crm.oportunidades_por_estado(estado)
    else:
        return crm.obtener_todas_oportunidades()

@router.get("/cliente/{symbol}", response_model=List[OportunidadResponse])
def oportunidades_por_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    cliente = crm.obtener_cliente(symbol)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return crm.oportunidades_por_cliente(symbol)

@router.post("/{opp_id}/cerrar")
def cerrar_oportunidad(opp_id: int, estado: str, pnl: Optional[float] = None, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.cerrar_oportunidad(opp_id, estado, pnl)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))