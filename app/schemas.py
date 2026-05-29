from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Lista de categorías actualizada (Binance)
CATEGORIAS_VALIDAS = [
    "BNB Chain", "Solana", "RWA", "MEME", "Pagos", "IA",
    "Capa 1/Capa 2", "Fase semilla", "Launchpool", "New", "Megadrop",
    "Juegos", "DeFi", "En observación", "Fan Token", "Infraestructura",
    "Almacenamiento", "NFT", "Launchpad", "Yzi", "desconocida"
]

# ─── CLIENTE SCHEMAS ───
class ClienteCriptoBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    nombre: Optional[str] = None
    categoria: Optional[str] = "desconocida"
    tags: Optional[str] = ""
    notas_personal: Optional[str] = ""

    @validator('categoria')
    def validate_categoria(cls, v):
        if v and v not in CATEGORIAS_VALIDAS:
            # Permitir cualquier valor, pero sugerir las válidas
            pass
        return v

class ClienteCriptoCreate(ClienteCriptoBase):
    pass

class ClienteCriptoUpdate(BaseModel):
    symbol: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    exchange_principal: Optional[str] = None
    cantidad_total: Optional[Decimal] = None
    costo_promedio: Optional[Decimal] = None
    inversion_total: Optional[Decimal] = None
    precio_actual: Optional[Decimal] = None
    valor_mercado: Optional[Decimal] = None
    pnl_total: Optional[Decimal] = None
    roi_porcentaje: Optional[Decimal] = None
    estado: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[str] = None
    notas_personal: Optional[str] = None
    fecha_ultimo_contacto: Optional[datetime] = None

    @validator('estado')
    def validate_estado(cls, v):
        if v is not None:
            allowed = ['PROSPECTO', 'ACTIVO_COMPRA', 'ACTIVO_PELIGRO', 'DORMANTE', 'CHURN', 'VIP']
            if v.upper() not in allowed:
                raise ValueError(f'Estado inválido. Debe ser uno de {allowed}')
            return v.upper()
        return v

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

# ─── LOTE COMPRA SCHEMAS ───
class LoteCompraBase(BaseModel):
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0)
    exchange: Optional[str] = "binance"
    notas: Optional[str] = ""

class LoteCompraCreate(LoteCompraBase):
    cliente_symbol: str

class LoteCompraResponse(LoteCompraBase):
    id: int
    cliente_id: int
    cantidad_restante: Decimal
    fecha_compra: datetime

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

    @validator('tipo')
    def validate_tipo(cls, v):
        if v is not None:
            # Mapear a los valores permitidos por el enum (en minúsculas)
            mapping = {
                "swing_trade": "swing_trade",
                "scalp": "scalp",
                "dca": "dca",
                "staking": "staking",
                "breakout": "breakout",
                "reversal": "reversal",
                # También aceptar mayúsculas si vienen del dashboard
                "SWING": "swing_trade",
                "SCALP": "scalp",
                "DCA": "dca",
                "STAKING": "staking",
                "BREAKOUT": "breakout",
                "REVERSAL": "reversal"
            }
            v_lower = v.lower()
            if v_lower in mapping:
                return mapping[v_lower]
            else:
                return v.lower()
        return v

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