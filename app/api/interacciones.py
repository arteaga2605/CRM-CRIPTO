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

def serializar_interaccion(interaccion):
    """Convierte un objeto Interaccion a dict serializable"""
    return {
        "id": interaccion.id,
        "cliente_id": interaccion.cliente_id,
        "tipo": interaccion.tipo.value if interaccion.tipo else None,
        "cantidad": float(interaccion.cantidad),
        "precio_unitario": float(interaccion.precio_unitario),
        "monto_usd": float(interaccion.monto_usd),
        "fee": float(interaccion.fee),
        "exchange": interaccion.exchange,
        "notas": interaccion.notas,
        "timestamp": interaccion.timestamp.isoformat(),
        "pnl_realizado": float(interaccion.pnl_realizado)
    }

def serializar_lote(lote):
    """Convierte un objeto LoteCompra a dict serializable"""
    return {
        "id": lote.id,
        "cliente_id": lote.cliente_id,
        "cantidad": float(lote.cantidad),
        "cantidad_restante": float(lote.cantidad_restante),
        "precio_unitario": float(lote.precio_unitario),
        "fecha_compra": lote.fecha_compra.isoformat(),
        "exchange": lote.exchange,
        "notas": lote.notas
    }

@router.post("/", response_model=dict)
def crear_interaccion(interaccion: InteraccionCreate, db: Session = Depends(get_db)):
    """
    Registra una compra o venta usando sistema FIFO para ventas.
    Para otros tipos (staking, airdrop) se usa el método general.
    """
    crm = CRMService(db)
    try:
        if interaccion.tipo == "compra":
            resultado = crm.registrar_compra(
                symbol=interaccion.cliente_symbol,
                cantidad=float(interaccion.cantidad),
                precio=float(interaccion.precio_unitario),
                fee=float(interaccion.fee),
                exchange=interaccion.exchange,
                notas=interaccion.notas
            )
            return {
                "tipo": "compra",
                "lote": serializar_lote(resultado["lote"]),
                "interaccion": serializar_interaccion(resultado["interaccion"])
            }
        elif interaccion.tipo == "venta":
            resultado = crm.registrar_venta_fifo(
                symbol=interaccion.cliente_symbol,
                cantidad_vender=float(interaccion.cantidad),
                precio_venta=float(interaccion.precio_unitario),
                fee=float(interaccion.fee),
                exchange=interaccion.exchange,
                notas=interaccion.notas
            )
            return {
                "tipo": "venta",
                "interaccion": serializar_interaccion(resultado["interaccion"]),
                "pnl_total": resultado["pnl_total"],
                "detalle_lotes": resultado["detalle_lotes"]
            }
        else:
            resultado = crm.registrar_interaccion_general(
                symbol=interaccion.cliente_symbol,
                tipo=interaccion.tipo,
                cantidad=float(interaccion.cantidad),
                precio=float(interaccion.precio_unitario),
                fee=float(interaccion.fee),
                exchange=interaccion.exchange,
                notas=interaccion.notas
            )
            return {
                "tipo": interaccion.tipo,
                "interaccion": serializar_interaccion(resultado["interaccion"])
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cliente/{symbol}", response_model=List[InteraccionResponse])
def historial_cliente(symbol: str, db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.historial_interacciones(symbol)

@router.delete("/{interaccion_id}")
def eliminar_interaccion(interaccion_id: int, db: Session = Depends(get_db)):
    """
    Elimina una interacción y reconstruye el estado del cliente desde cero.
    """
    crm = CRMService(db)
    try:
        resultado = crm.eliminar_interaccion(interaccion_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))