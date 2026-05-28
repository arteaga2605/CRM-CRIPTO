from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models import SessionLocal
from app.schemas import LoteCompraResponse
from app.services.crm_service import CRMService

router = APIRouter(prefix="/lotes", tags=["Lotes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/cliente/{symbol}", response_model=List[LoteCompraResponse])
def obtener_lotes_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    lotes = crm.obtener_lotes_cliente(symbol)
    if lotes is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return lotes

@router.get("/all")
def obtener_todos_lotes(db: Session = Depends(get_db)):
    """
    Devuelve todos los lotes activos (cantidad_restante > 0) agrupados por símbolo.
    """
    crm = CRMService(db)
    lotes_por_cliente = crm.obtener_todos_lotes_con_clientes()
    resultado = {}
    for symbol, lotes in lotes_por_cliente.items():
        resultado[symbol] = [
            {
                "id": l.id,
                "cantidad": float(l.cantidad),
                "cantidad_restante": float(l.cantidad_restante),
                "precio_unitario": float(l.precio_unitario),
                "fecha_compra": l.fecha_compra.isoformat(),
                "exchange": l.exchange,
                "notas": l.notas
            }
            for l in lotes
        ]
    return resultado