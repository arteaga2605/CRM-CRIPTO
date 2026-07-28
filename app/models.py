from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Boolean, ForeignKey, Text, Enum, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

# ─── ENUMS ───
class EstadoCliente(enum.Enum):
    PROSPECTO = "prospecto"
    ACTIVO_COMPRA = "activo_compra"
    ACTIVO_PELIGRO = "activo_peligro"
    DORMANTE = "dormante"
    CHURN = "churn"
    VIP = "vip"

class TipoInteraccion(enum.Enum):
    COMPRA = "compra"
    VENTA = "venta"
    STAKING = "staking"
    UNSTAKING = "unstaking"
    TRANSFERENCIA = "transferencia"
    DIVIDENDO = "dividendo"
    AIRDROP = "airdrop"

class TipoOportunidad(enum.Enum):
    SWING = "swing_trade"
    SCALP = "scalp"
    DCA = "dca"
    STAKING_OPP = "staking"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"

# ─── CLIENTE CRIPTO ───
class ClienteCripto(Base):
    __tablename__ = "clientes_cripto"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100))
    categoria = Column(String(50), default="desconocida")

    exchange_principal = Column(String(50), default="binance")
    precio_actual = Column(Numeric(20, 8), default=0)
    cantidad_total = Column(Numeric(20, 8), default=0)
    costo_promedio = Column(Numeric(20, 8), default=0)
    inversion_total = Column(Numeric(20, 8), default=0)
    valor_mercado = Column(Numeric(20, 8), default=0)
    pnl_total = Column(Numeric(20, 8), default=0)
    roi_porcentaje = Column(Numeric(20, 4), default=0)

    estado = Column(Enum(EstadoCliente), default=EstadoCliente.PROSPECTO)
    sentiment_score = Column(Numeric(3, 2), default=0)
    prioridad = Column(Integer, default=3)

    tags = Column(String(255), default="")
    notas_personal = Column(Text, default="")
    fecha_ultimo_contacto = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    interacciones = relationship("Interaccion", back_populates="cliente", cascade="all, delete-orphan")
    oportunidades = relationship("Oportunidad", back_populates="cliente", cascade="all, delete-orphan")
    tareas = relationship("Tarea", back_populates="cliente", cascade="all, delete-orphan")
    lotes = relationship("LoteCompra", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClienteCripto({self.symbol}: {self.estado.value}, ROI={self.roi_porcentaje}%)>"

# ─── INTERACCION ───
class Interaccion(Base):
    __tablename__ = "interacciones"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes_cripto.id"), nullable=False)
    tipo = Column(Enum(TipoInteraccion), nullable=False)

    monto_usd = Column(Numeric(20, 8), default=0)
    precio_unitario = Column(Numeric(20, 8), nullable=False)
    cantidad = Column(Numeric(20, 8), nullable=False)
    fee = Column(Numeric(20, 8), default=0)
    exchange = Column(String(50), default="binance")

    timestamp = Column(DateTime, default=datetime.utcnow)
    notas = Column(Text, default="")

    pnl_realizado = Column(Numeric(20, 8), default=0)

    cliente = relationship("ClienteCripto", back_populates="interacciones")

    def __repr__(self):
        return f"<Interaccion({self.tipo.value} {self.cantidad} {self.cliente.symbol})>"

# ─── LOTE DE COMPRA (FIFO) ───
class LoteCompra(Base):
    __tablename__ = "lotes_compra"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes_cripto.id"), nullable=False)
    cantidad = Column(Numeric(20, 8), nullable=False)
    cantidad_restante = Column(Numeric(20, 8), nullable=False)
    precio_unitario = Column(Numeric(20, 8), nullable=False)
    fecha_compra = Column(DateTime, default=datetime.utcnow)
    exchange = Column(String(50), default="binance")
    notas = Column(Text, default="")

    cliente = relationship("ClienteCripto", back_populates="lotes")

    def __repr__(self):
        return f"<LoteCompra({self.cliente.symbol} {self.cantidad}@{self.precio_unitario} restante={self.cantidad_restante})>"

# ─── OPORTUNIDAD ───
class Oportunidad(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes_cripto.id"), nullable=False)

    tipo = Column(Enum(TipoOportunidad), default=TipoOportunidad.SWING)
    estado = Column(String(20), default="abierta")

    precio_entrada = Column(Numeric(20, 8))
    precio_objetivo = Column(Numeric(20, 8))
    precio_stop_loss = Column(Numeric(20, 8))
    riesgo_beneficio = Column(Numeric(20, 4))
    monto_planificado = Column(Numeric(20, 8), default=0)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_ejecucion = Column(DateTime)
    confianza = Column(Integer, default=3)
    notas_analisis = Column(Text, default="")
    resultado_pnl = Column(Numeric(20, 8))

    cliente = relationship("ClienteCripto", back_populates="oportunidades")

    def __repr__(self):
        return f"<Oportunidad({self.cliente.symbol} {self.tipo.value} R:R={self.riesgo_beneficio})>"

# ─── TAREA ───
class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes_cripto.id"), nullable=False)

    tipo_tarea = Column(String(50))
    descripcion = Column(Text)
    fecha_limite = Column(DateTime)
    completada = Column(Boolean, default=False)
    fecha_completada = Column(DateTime)
    prioridad = Column(Integer, default=2)

    cliente = relationship("ClienteCripto", back_populates="tareas")

    def __repr__(self):
        return f"<Tarea({self.cliente.symbol}: {self.tipo_tarea})>"

# ─── EVENTOS DE BINANCE ───
class BinanceEvent(Base):
    __tablename__ = "binance_events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False)
    url = Column(String(500), nullable=True)
    event_date = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<BinanceEvent({self.event_type}: {self.title})>"

# ─── NOTIFICACIONES ───
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    message = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)
    related_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification({self.type}: {self.message[:50]})>"

# ─── INVERSIONES DEPORTIVAS (MÓDULO AISLADO) ───
class TipoMercadoDeportivo(enum.Enum):
    EQUIPO = "EQUIPO"
    RESULTADO = "RESULTADO"
    ESTADISTICA = "ESTADISTICA"

class EstadoInversionDeportiva(enum.Enum):
    ABIERTA = "ABIERTA"
    GANADA = "GANADA"
    PERDIDA = "PERDIDA"
    NULA = "NULA"

class InversionDeportiva(Base):
    __tablename__ = "inversiones_deportivas"

    id = Column(Integer, primary_key=True)
    deporte = Column(String(50), default="BEISBOL")
    tipo_mercado = Column(Enum(TipoMercadoDeportivo), nullable=False)
    objetivo = Column(String(100), nullable=False)

    capital_invertido = Column(Numeric(20, 2), nullable=False)
    ganancia_potencial = Column(Numeric(20, 2), nullable=False)
    perdida_potencial = Column(Numeric(20, 2), nullable=False)

    estado = Column(Enum(EstadoInversionDeportiva), default=EstadoInversionDeportiva.ABIERTA)
    pnl_realizado = Column(Numeric(20, 2), default=0.00)

    cuota_odds = Column(Numeric(10, 2), nullable=True)
    notas = Column(Text, default="")

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<InversionDeportiva({self.deporte} - {self.objetivo}: {self.estado.value})>"

# ─── RETIROS DEPORTIVOS ───
class RetiroDeportivo(Base):
    __tablename__ = "retiros_deportivos"

    id = Column(Integer, primary_key=True)
    monto = Column(Numeric(20, 2), nullable=False)
    fecha_retiro = Column(DateTime, default=datetime.utcnow)
    notas = Column(Text, default="")

    def __repr__(self):
        return f"<RetiroDeportivo(${self.monto} el {self.fecha_retiro})>"

# ─── INYECCIONES DE CAPITAL DEPORTIVAS (NUEVO) ───
class InyeccionCapitalDeportivo(Base):
    __tablename__ = "inyecciones_capital_deportivo"

    id = Column(Integer, primary_key=True)
    monto = Column(Numeric(20, 2), nullable=False)
    fecha_inyeccion = Column(DateTime, default=datetime.utcnow)
    notas = Column(Text, default="")

    def __repr__(self):
        return f"<InyeccionCapitalDeportivo(${self.monto} el {self.fecha_inyeccion})>"

# ─── CONFIGURACION DB ───
DATABASE_URL = "sqlite:///./crypto_crm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
