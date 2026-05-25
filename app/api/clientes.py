from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import SessionLocal, init_db
from app.schemas import ClienteCriptoCreate, ClienteCriptoUpdate, ClienteCriptoResponse
from app.services.crm_service import CRMService

router = APIRouter(prefix="/clientes", tags=["Clientes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ClienteCriptoResponse)
def crear_cliente(cliente: ClienteCriptoCreate, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.registrar_cliente(
            symbol=cliente.symbol,
            nombre=cliente.nombre,
            categoria=cliente.categoria,
            tags=cliente.tags,
            notas_personal=cliente.notas_personal
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ClienteCriptoResponse])
def listar_clientes(
    estado: Optional[str] = None,
    categoria: Optional[str] = None,
    min_roi: Optional[float] = None,
    db: Session = Depends(get_db)
):
    crm = CRMService(db)
    return crm.listar_clientes(estado=estado, categoria=categoria, min_roi=min_roi)

@router.get("/{symbol}", response_model=ClienteCriptoResponse)
def obtener_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    cliente = crm.obtener_cliente(symbol)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{symbol}", response_model=ClienteCriptoResponse)
def actualizar_cliente(symbol: str, update: ClienteCriptoUpdate, db: Session = Depends(get_db)):
    crm = CRMService(db)
    cliente = crm.obtener_cliente(symbol)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in update.dict(exclude_unset=True).items():
        setattr(cliente, field, value)

    db.commit()
    db.refresh(cliente)
    return cliente

@router.delete("/{symbol}")
def eliminar_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    cliente = crm.obtener_cliente(symbol)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cliente)
    db.commit()
    return {"message": f"Cliente {symbol} eliminado"}

@router.post("/{symbol}/actualizar-precio")
def actualizar_precio(symbol: str, precio: float, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.actualizar_precio_mercado(symbol, precio)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
