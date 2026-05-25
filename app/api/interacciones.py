from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import SessionLocal
from app.schemas import InteraccionCreate, InteraccionResponse
from app.services.crm_service import CRMService

router = APIRouter(prefix="/interacciones", tags=["Interacciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=InteraccionResponse)
def crear_interaccion(interaccion: InteraccionCreate, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.registrar_interaccion(
            symbol=interaccion.cliente_symbol,
            tipo=interaccion.tipo,
            cantidad=float(interaccion.cantidad),
            precio=float(interaccion.precio_unitario),
            fee=float(interaccion.fee),
            exchange=interaccion.exchange,
            notas=interaccion.notas
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cliente/{symbol}", response_model=List[InteraccionResponse])
def historial_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.historial_interacciones(symbol)
