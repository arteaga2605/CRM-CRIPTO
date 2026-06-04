from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import SessionLocal
from app.schemas import TareaCreate, TareaResponse
from app.services.crm_service import CRMService

router = APIRouter(prefix="/tareas", tags=["Tareas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TareaResponse)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.crear_tarea(
            symbol=tarea.cliente_symbol,
            tipo=tarea.tipo_tarea,
            descripcion=tarea.descripcion,
            dias=3,
            prioridad=tarea.prioridad
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pendientes", response_model=List[TareaResponse])
def tareas_pendientes(db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.tareas_pendientes()

@router.get("/proximas", response_model=List[TareaResponse])
def tareas_proximas(db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.tareas_proximas(dias=3)

@router.get("/completadas", response_model=List[TareaResponse])
def tareas_completadas(limit: int = 10, db: Session = Depends(get_db)):
    """Devuelve las últimas tareas completadas (máximo `limit`)."""
    crm = CRMService(db)
    return crm.tareas_completadas(limit=limit)

@router.post("/{tarea_id}/completar")
def completar_tarea(tarea_id: int, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.completar_tarea(tarea_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))