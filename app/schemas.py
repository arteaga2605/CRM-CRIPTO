from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ─── CLIENTE SCHEMAS ───
class ClienteCriptoBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    nombre: Optional[str] = None
    categoria: Optional[str] = "desconocida"
    tags: Optional[str] = ""
    notas_personal: Optional[str] = ""

class ClienteCriptoCreate(ClienteCriptoBase):
    pass

class ClienteCriptoUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    tags: Optional[str] = None
    notas_personal: Optional[str] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)
    estado: Optional[str] = None

class ClienteCriptoResponse(ClienteCriptoBase):
    id: int
    exchange_principal: str
    precio_actual: Decimal
    cantidad_total: Decimal
    costo_promedio: Decimal
    inversion_total: Decimal
    valor_mercado: Decimal
    pnl_total: Decimal
    roi_porcentaje: Decimal
    estado: str
    sentiment_score: Decimal
    prioridad: int
    fecha_ultimo_contacto: datetime
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# ─── INTERACCION SCHEMAS ───
class InteraccionBase(BaseModel):
    tipo: str
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0)
    fee: Optional[Decimal] = Decimal("0")
    exchange: Optional[str] = "binance"
    notas: Optional[str] = ""

class InteraccionCreate(InteraccionBase):
    cliente_symbol: str

class InteraccionResponse(InteraccionBase):
    id: int
    cliente_id: int
    monto_usd: Decimal
    pnl_realizado: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True

# ─── OPORTUNIDAD SCHEMAS ───
class OportunidadBase(BaseModel):
    tipo: Optional[str] = "swing_trade"
    precio_entrada: Decimal = Field(..., gt=0)
    precio_objetivo: Decimal = Field(..., gt=0)
    precio_stop_loss: Decimal = Field(..., gt=0)
    monto_planificado: Optional[Decimal] = Decimal("0")
    confianza: Optional[int] = Field(3, ge=1, le=5)
    notas_analisis: Optional[str] = ""

class OportunidadCreate(OportunidadBase):
    cliente_symbol: str

class OportunidadResponse(OportunidadBase):
    id: int
    cliente_id: int
    estado: str
    riesgo_beneficio: Decimal
    fecha_creacion: datetime
    resultado_pnl: Optional[Decimal]

    class Config:
        from_attributes = True

# ─── TAREA SCHEMAS ───
class TareaBase(BaseModel):
    tipo_tarea: str
    descripcion: str
    fecha_limite: Optional[datetime] = None
    prioridad: Optional[int] = Field(2, ge=1, le=5)

class TareaCreate(TareaBase):
    cliente_symbol: str

class TareaResponse(TareaBase):
    id: int
    cliente_id: int
    completada: bool
    fecha_completada: Optional[datetime]

    class Config:
        from_attributes = True

# ─── DASHBOARD SCHEMAS ───
class DashboardResumen(BaseModel):
    total_clientes: int
    clientes_activos: int
    clientes_vip: int
    clientes_peligro: int
    pnl_total_portafolio: Decimal
    roi_promedio: Decimal
    tareas_pendientes: int
    oportunidades_abiertas: int

class ClienteConMetricas(BaseModel):
    cliente: ClienteCriptoResponse
    total_interacciones: int
    ultima_interaccion: Optional[datetime]
    oportunidades_count: int
    tareas_pendientes: int
