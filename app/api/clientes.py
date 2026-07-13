from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel

from app.models import SessionLocal, EstadoCliente
from app.schemas import ClienteCriptoCreate, ClienteCriptoUpdate, ClienteCriptoResponse
from app.services.crm_service import CRMService
from app.services.exchange_sync import ExchangeConnector

router = APIRouter(prefix="/clientes", tags=["Clientes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ESQUEMA NUEVO PARA CORRECCION MANUAL
class CorreccionInversion(BaseModel):
    nueva_inversion: float

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
    update_data = update.dict(exclude_unset=True)
    if 'estado' in update_data:
        estado_str = update_data['estado'].upper()
        try:
            update_data['estado'] = EstadoCliente[estado_str]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {estado_str}. Opciones: {[e.name for e in EstadoCliente]}")
    for field, value in update_data.items():
        setattr(cliente, field, value)
    
    cantidad = cliente.cantidad_total if cliente.cantidad_total else Decimal("0")
    precio_actual = cliente.precio_actual if cliente.precio_actual else Decimal("0")
    costo_promedio = cliente.costo_promedio if cliente.costo_promedio else Decimal("0")
    
    if cantidad > 0:
        cliente.valor_mercado = cantidad * precio_actual
        inversion = cantidad * costo_promedio
        cliente.inversion_total = inversion
        cliente.pnl_total = cliente.valor_mercado - inversion
        if inversion > 0:
            cliente.roi_porcentaje = (cliente.pnl_total / inversion) * Decimal("100")
        else:
            cliente.roi_porcentaje = Decimal("0")
    else:
        cliente.valor_mercado = Decimal("0")
        cliente.inversion_total = Decimal("0")
        cliente.pnl_total = Decimal("0")
        cliente.roi_porcentaje = Decimal("0")
        
    db.commit()
    db.refresh(cliente)
    crm.actualizar_estado_cliente(symbol)
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
def actualizar_precio(symbol: str, precio: float = None, db: Session = Depends(get_db)):
    crm = CRMService(db)
    cliente = crm.obtener_cliente(symbol)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if precio is None:
        connector = ExchangeConnector()
        precio = connector.obtener_precio(symbol)
        if precio == 0:
            raise HTTPException(status_code=400, detail=f"No se pudo obtener precio de {symbol} desde Binance")
    cliente_actualizado = crm.actualizar_precio_mercado(symbol, precio)
    return cliente_actualizado

# ENDPOINT NUEVO PARA CORRECCION MANUAL DE CAPITAL
@router.post("/{symbol}/corregir-inversion")
def corregir_inversion(symbol: str, data: CorreccionInversion, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        cliente_actualizado = crm.corregir_inversion_total(symbol, data.nueva_inversion)
        return cliente_actualizado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))