Vamos a actualizar la documentación del proyecto y el archivo `codigo_completo_crypto_crm.txt` para reflejar todas las funcionalidades implementadas hasta ahora: **sistema FIFO con lotes de compra**, **eliminación de interacciones**, **cálculo de PnL no realizado basado en lotes**, **precios reales desde Binance**, **dashboard editable**, etc.

A continuación, te entrego el contenido completo y actualizado de ambos archivos.

---

## 1. `README.md` (documentación actualizada)

```markdown
# 🪙 Crypto CRM - Tratando Criptomonedas como Clientes

**Versión 2.0** - Con sistema FIFO, lotes de compra, precios en tiempo real y dashboard interactivo.

Un sistema completo de gestión de portafolio de criptomonedas construido con la mentalidad de CRM (Customer Relationship Management). Cada moneda es un "cliente" al que le das seguimiento, atención y estrategia.  
Ahora con **cálculo de ganancias/pérdidas por lotes (FIFO)** y **sincronización de precios reales desde Binance**.

## 🎯 Filosofía

> "No operas criptomonedas, gestionas relaciones con activos digitales"

- **Cliente** = Criptomoneda (BTC, ETH, PEPE)
- **Interacción** = Transacción (compra, venta, staking)
- **Lote de compra** = cada compra se guarda individualmente (con su cantidad, precio + comisión, fecha)
- **Oportunidad** = Trade setup con entrada, objetivo y stop
- **Tarea** = Alerta o recordatorio de seguimiento

## 🏗️ Arquitectura

```
crypto_crm/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # SQLAlchemy ORM (incluye LoteCompra)
│   ├── schemas.py           # Pydantic validation
│   ├── services/
│   │   ├── crm_service.py   # Lógica de negocio (FIFO, recalculo)
│   │   ├── exchange_sync.py # CCXT connector (precios públicos)
│   │   └── analytics.py     # Métricas y alertas
│   ├── api/
│   │   ├── clientes.py      # CRUD criptomonedas
│   │   ├── interacciones.py # Transacciones (con eliminación)
│   │   ├── oportunidades.py # Pipeline trades
│   │   ├── tareas.py        # Alertas
│   │   └── lotes.py         # Consulta de lotes FIFO
│   └── tasks.py             # Celery background jobs
├── dashboard/
│   └── streamlit_app.py     # Interfaz visual (editable, con precios reales)
├── config.py
└── requirements.txt
```

## 🚀 Instalación Rápida

```bash
# 1. Clonar y entrar
cd crypto_crm

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos (se crea automáticamente)
# Se crea crypto_crm.db

# 5. Iniciar API
uvicorn app.main:app --reload --port 8000

# 6. En otra terminal, iniciar dashboard
streamlit run dashboard/streamlit_app.py

# 7. Opcional: workers Celery (para alertas periódicas)
celery -A app.tasks worker --beat --loglevel=info
```

## 📡 API Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/clientes/` | GET | Listar todas las criptomonedas |
| `/clientes/` | POST | Registrar nueva moneda |
| `/clientes/{symbol}` | PUT | Actualizar campos (cantidad, estado, etc.) |
| `/clientes/{symbol}/actualizar-precio` | POST | Actualizar precio de mercado (automático desde Binance) |
| `/interacciones/` | POST | Registrar compra/venta/staking (FIFO automático) |
| `/interacciones/{id}` | DELETE | Eliminar interacción y reconstruir el cliente |
| `/interacciones/cliente/{symbol}` | GET | Historial de transacciones |
| `/lotes/cliente/{symbol}` | GET | Ver lotes de compra de un cliente |
| `/lotes/all` | GET | Todos los lotes activos (para dashboard) |
| `/oportunidades/` | GET/POST | Pipeline de trades |
| `/tareas/` | GET/POST | Tareas y alertas |
| `/precios/{symbol}` | GET | Precio actual desde Binance (público) |
| `/ticker/{symbol}` | GET | Información completa del ticker |
| `/velas/{symbol}` | GET | Velas OHLCV históricas |
| `/dashboard/resumen` | GET | Resumen para el dashboard |

## 💡 Ejemplo de Uso (FIFO)

```python
from app.models import init_db, SessionLocal
from app.services.crm_service import CRMService

init_db()
db = SessionLocal()
crm = CRMService(db)

# 1. Registrar cliente
crm.registrar_cliente("BTC", "Bitcoin", "layer1")

# 2. Comprar 0.1 BTC a 60000 USD (fee 10 USD)
crm.registrar_compra("BTC", 0.1, 60000, fee=10)

# 3. Comprar 0.2 BTC a 55000 USD (fee 20 USD)
crm.registrar_compra("BTC", 0.2, 55000, fee=20)

# 4. Vender 0.15 BTC a 65000 USD (fee 15 USD)
venta = crm.registrar_venta_fifo("BTC", 0.15, 65000, fee=15)
print(f"PnL total de la venta: ${venta['pnl_total']}")
for detalle in venta['detalle_lotes']:
    print(f"Lote {detalle['lote_id']}: {detalle['cantidad']} BTC, PnL: ${detalle['pnl_lote']}")

# 5. Ver lotes restantes
lotes = crm.obtener_lotes_cliente("BTC")
for l in lotes:
    print(f"Quedan {l.cantidad_restante} BTC a precio {l.precio_unitario}")
```

## 🔔 Alertas Inteligentes (Celery)

Se generan automáticamente tareas basadas en:
- Pérdida > 20% → sugerir stop loss
- Ganancia > 50% → sugerir take profit parcial
- Concentración > 30% → sugerir rebalancear
- Sin movimiento en 30 días → revisar estrategia

## 📊 Dashboard

El dashboard de Streamlit incluye:

- **KPIs** del portafolio en tiempo real
- **Tabla de clientes editable** (cantidad, costo, estado, etc.)
- **Cálculo automático de PnL no realizado** usando FIFO (coincide con Binance)
- **Visualización de lotes de compra** por cliente
- **Botones para actualizar precios desde Binance** (individual o masivo)
- **Eliminación de interacciones** (con reconstrucción automática del estado)
- **Gráficos de distribución y top performers**
- **Alertas inteligentes visuales**
- **Sección "Mercado en Vivo"** con precios, ticker y velas históricas

## 🔗 Conexión con Binance (API Pública)

Sin necesidad de API key, se pueden obtener:
- Precio actual de cualquier par `symbol/USDT`
- Ticker (cambio 24h, volumen, máximos/mínimos)
- Velas históricas (OHLCV) para gráficos

## 🛡️ Seguridad

- Las API keys **nunca se almacenan** en la DB (solo se usan en tiempo real si se proporcionan)
- SQLite local por defecto (fácil de migrar a PostgreSQL)
- Sin conexión a internet requerida para operación básica

## 📝 Roadmap (próximas mejoras)

- [x] FIFO con lotes de compra
- [x] Eliminación de interacciones
- [x] Precios en tiempo real desde Binance
- [x] Dashboard editable
- [ ] WebSockets para precios en tiempo real (streaming)
- [ ] Notificaciones Telegram/Email
- [ ] Backtesting de oportunidades
- [ ] Machine Learning para sentiment scoring

## 📄 Licencia

MIT - Usalo, modificalo, hazlo tuyo.

---

**Construido con ❤️ para traders que piensan como gestores de relaciones.**
```

---

## 2. `codigo_completo_crypto_crm.txt` (archivo consolidado)

Este archivo contiene todo el código fuente del proyecto, actualizado con las últimas funcionalidades. Se incluyen los siguientes archivos (en orden):

- `.gitignore`
- `README.md` (el nuevo contenido)
- `config.py`
- `requirements.txt`
- `app/__init__.py`
- `app/main.py`
- `app/models.py`
- `app/schemas.py`
- `app/tasks.py`
- `app/services/__init__.py`
- `app/services/crm_service.py`
- `app/services/analytics.py`
- `app/services/exchange_sync.py`
- `app/api/__init__.py`
- `app/api/clientes.py`
- `app/api/interacciones.py`
- `app/api/oportunidades.py`
- `app/api/tareas.py`
- `app/api/lotes.py`
- `dashboard/streamlit_app.py`

No omito ni una línea. **El contenido es extenso**, por lo que te lo proporciono a continuación, listo para copiar y pegar en un solo archivo de texto.

```text
================================================================================
  ARCHIVO: .gitignore
================================================================================

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Database
crypto_crm.db
*.db
*.sqlite

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db


================================================================================
  FIN DE ARCHIVO: .gitignore
================================================================================


================================================================================
  ARCHIVO: README.md
================================================================================

# 🪙 Crypto CRM - Tratando Criptomonedas como Clientes

**Versión 2.0** - Con sistema FIFO, lotes de compra, precios en tiempo real y dashboard interactivo.

Un sistema completo de gestión de portafolio de criptomonedas construido con la mentalidad de CRM (Customer Relationship Management). Cada moneda es un "cliente" al que le das seguimiento, atención y estrategia.  
Ahora con **cálculo de ganancias/pérdidas por lotes (FIFO)** y **sincronización de precios reales desde Binance**.

## 🎯 Filosofía

> "No operas criptomonedas, gestionas relaciones con activos digitales"

- **Cliente** = Criptomoneda (BTC, ETH, PEPE)
- **Interacción** = Transacción (compra, venta, staking)
- **Lote de compra** = cada compra se guarda individualmente (con su cantidad, precio + comisión, fecha)
- **Oportunidad** = Trade setup con entrada, objetivo y stop
- **Tarea** = Alerta o recordatorio de seguimiento

## 🏗️ Arquitectura

```
crypto_crm/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # SQLAlchemy ORM (incluye LoteCompra)
│   ├── schemas.py           # Pydantic validation
│   ├── services/
│   │   ├── crm_service.py   # Lógica de negocio (FIFO, recalculo)
│   │   ├── exchange_sync.py # CCXT connector (precios públicos)
│   │   └── analytics.py     # Métricas y alertas
│   ├── api/
│   │   ├── clientes.py      # CRUD criptomonedas
│   │   ├── interacciones.py # Transacciones (con eliminación)
│   │   ├── oportunidades.py # Pipeline trades
│   │   ├── tareas.py        # Alertas
│   │   └── lotes.py         # Consulta de lotes FIFO
│   └── tasks.py             # Celery background jobs
├── dashboard/
│   └── streamlit_app.py     # Interfaz visual (editable, con precios reales)
├── config.py
└── requirements.txt
```

## 🚀 Instalación Rápida

```bash
# 1. Clonar y entrar
cd crypto_crm

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos (se crea automáticamente)
# Se crea crypto_crm.db

# 5. Iniciar API
uvicorn app.main:app --reload --port 8000

# 6. En otra terminal, iniciar dashboard
streamlit run dashboard/streamlit_app.py

# 7. Opcional: workers Celery (para alertas periódicas)
celery -A app.tasks worker --beat --loglevel=info
```

## 📡 API Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/clientes/` | GET | Listar todas las criptomonedas |
| `/clientes/` | POST | Registrar nueva moneda |
| `/clientes/{symbol}` | PUT | Actualizar campos (cantidad, estado, etc.) |
| `/clientes/{symbol}/actualizar-precio` | POST | Actualizar precio de mercado (automático desde Binance) |
| `/interacciones/` | POST | Registrar compra/venta/staking (FIFO automático) |
| `/interacciones/{id}` | DELETE | Eliminar interacción y reconstruir el cliente |
| `/interacciones/cliente/{symbol}` | GET | Historial de transacciones |
| `/lotes/cliente/{symbol}` | GET | Ver lotes de compra de un cliente |
| `/lotes/all` | GET | Todos los lotes activos (para dashboard) |
| `/oportunidades/` | GET/POST | Pipeline de trades |
| `/tareas/` | GET/POST | Tareas y alertas |
| `/precios/{symbol}` | GET | Precio actual desde Binance (público) |
| `/ticker/{symbol}` | GET | Información completa del ticker |
| `/velas/{symbol}` | GET | Velas OHLCV históricas |
| `/dashboard/resumen` | GET | Resumen para el dashboard |

## 💡 Ejemplo de Uso (FIFO)

```python
from app.models import init_db, SessionLocal
from app.services.crm_service import CRMService

init_db()
db = SessionLocal()
crm = CRMService(db)

# 1. Registrar cliente
crm.registrar_cliente("BTC", "Bitcoin", "layer1")

# 2. Comprar 0.1 BTC a 60000 USD (fee 10 USD)
crm.registrar_compra("BTC", 0.1, 60000, fee=10)

# 3. Comprar 0.2 BTC a 55000 USD (fee 20 USD)
crm.registrar_compra("BTC", 0.2, 55000, fee=20)

# 4. Vender 0.15 BTC a 65000 USD (fee 15 USD)
venta = crm.registrar_venta_fifo("BTC", 0.15, 65000, fee=15)
print(f"PnL total de la venta: ${venta['pnl_total']}")
for detalle in venta['detalle_lotes']:
    print(f"Lote {detalle['lote_id']}: {detalle['cantidad']} BTC, PnL: ${detalle['pnl_lote']}")

# 5. Ver lotes restantes
lotes = crm.obtener_lotes_cliente("BTC")
for l in lotes:
    print(f"Quedan {l.cantidad_restante} BTC a precio {l.precio_unitario}")
```

## 🔔 Alertas Inteligentes (Celery)

Se generan automáticamente tareas basadas en:
- Pérdida > 20% → sugerir stop loss
- Ganancia > 50% → sugerir take profit parcial
- Concentración > 30% → sugerir rebalancear
- Sin movimiento en 30 días → revisar estrategia

## 📊 Dashboard

El dashboard de Streamlit incluye:

- **KPIs** del portafolio en tiempo real
- **Tabla de clientes editable** (cantidad, costo, estado, etc.)
- **Cálculo automático de PnL no realizado** usando FIFO (coincide con Binance)
- **Visualización de lotes de compra** por cliente
- **Botones para actualizar precios desde Binance** (individual o masivo)
- **Eliminación de interacciones** (con reconstrucción automática del estado)
- **Gráficos de distribución y top performers**
- **Alertas inteligentes visuales**
- **Sección "Mercado en Vivo"** con precios, ticker y velas históricas

## 🔗 Conexión con Binance (API Pública)

Sin necesidad de API key, se pueden obtener:
- Precio actual de cualquier par `symbol/USDT`
- Ticker (cambio 24h, volumen, máximos/mínimos)
- Velas históricas (OHLCV) para gráficos

## 🛡️ Seguridad

- Las API keys **nunca se almacenan** en la DB (solo se usan en tiempo real si se proporcionan)
- SQLite local por defecto (fácil de migrar a PostgreSQL)
- Sin conexión a internet requerida para operación básica

## 📝 Roadmap (próximas mejoras)

- [x] FIFO con lotes de compra
- [x] Eliminación de interacciones
- [x] Precios en tiempo real desde Binance
- [x] Dashboard editable
- [ ] WebSockets para precios en tiempo real (streaming)
- [ ] Notificaciones Telegram/Email
- [ ] Backtesting de oportunidades
- [ ] Machine Learning para sentiment scoring

## 📄 Licencia

MIT - Usalo, modificalo, hazlo tuyo.

---

**Construido con ❤️ para traders que piensan como gestores de relaciones.**


================================================================================
  FIN DE ARCHIVO: README.md
================================================================================


================================================================================
  ARCHIVO: config.py
================================================================================

"""
Configuracion del CRM Crypto.
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./crypto_crm.db"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Exchange (opcional - para sincronizacion)
    EXCHANGE_ID: str = "binance"
    EXCHANGE_API_KEY: Optional[str] = None
    EXCHANGE_API_SECRET: Optional[str] = None

    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Alertas
    ALERTA_PERDIDA_PORCENTAJE: float = 20.0
    ALERTA_GANANCIA_PORCENTAJE: float = 50.0
    ALERTA_CONCENTRACION_MAX: float = 30.0
    DIAS_CLIENTE_DORMIDO: int = 30

    class Config:
        env_file = ".env"

settings = Settings()


================================================================================
  FIN DE ARCHIVO: config.py
================================================================================


================================================================================
  ARCHIVO: requirements.txt
================================================================================

# Framework
fastapi==0.111.0
uvicorn[standard]==0.30.0

# Database
sqlalchemy==2.0.30
alembic==1.13.1

# Validation
pydantic==2.7.0
pydantic-settings==2.2.1

# Dashboard
streamlit==1.35.0
plotly==5.22.0
pandas==2.2.2

# Exchange API
ccxt==4.3.0

# Background Tasks
celery==5.4.0
redis==5.0.0

# Notifications (opcional)
python-telegram-bot==21.0

# Testing
pytest==8.2.0
httpx==0.27.0


================================================================================
  FIN DE ARCHIVO: requirements.txt
================================================================================


================================================================================
  ARCHIVO: app/__init__.py
================================================================================

# Crypto CRM - Tratando criptomonedas como clientes
__version__ = "2.0.0"


================================================================================
  FIN DE ARCHIVO: app/__init__.py
================================================================================


================================================================================
  ARCHIVO: app/main.py
================================================================================

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models import init_db, SessionLocal
from app.api import clientes, interacciones, oportunidades, tareas, lotes
from app.services.exchange_sync import ExchangeConnector

app = FastAPI(
    title="Crypto CRM",
    description="Tratando criptomonedas como clientes - Sistema de gestion de portafolio",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(clientes.router)
app.include_router(interacciones.router)
app.include_router(oportunidades.router)
app.include_router(tareas.router)
app.include_router(lotes.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "message": "Crypto CRM API",
        "docs": "/docs",
        "endpoints": {
            "clientes": "/clientes",
            "interacciones": "/interacciones",
            "oportunidades": "/oportunidades",
            "tareas": "/tareas",
            "lotes": "/lotes/cliente/{symbol}",
            "precios": "/precios/{symbol}",
            "ticker": "/ticker/{symbol}"
        }
    }

@app.get("/precios/{symbol}")
def obtener_precio_real(symbol: str, vs: str = "USDT"):
    connector = ExchangeConnector()
    precio = connector.obtener_precio(symbol.upper(), vs)
    return {"symbol": symbol.upper(), "price": precio, "vs_currency": vs}

@app.get("/ticker/{symbol}")
def obtener_ticker_real(symbol: str, vs: str = "USDT"):
    connector = ExchangeConnector()
    ticker = connector.obtener_ticker(symbol.upper(), vs)
    return ticker

@app.get("/velas/{symbol}")
def obtener_velas(symbol: str, timeframe: str = "1h", limit: int = 100, vs: str = "USDT"):
    connector = ExchangeConnector()
    velas = connector.obtener_velas(symbol.upper(), timeframe, limit, vs)
    return {"symbol": symbol.upper(), "timeframe": timeframe, "data": velas}

@app.get("/dashboard/resumen")
def resumen_dashboard(db: Session = Depends(get_db)):
    from app.services.crm_service import CRMService
    from app.services.analytics import AnalyticsService

    crm = CRMService(db)
    analytics = AnalyticsService(db)

    return {
        "resumen": crm.resumen_portafolio(),
        "top_performers": [
            {"symbol": c.symbol, "roi": float(c.roi_porcentaje)}
            for c in crm.top_performers(5)
        ],
        "alertas": analytics.alertas_inteligentes(),
        "distribucion": analytics.distribucion_portafolio()[:5]
    }


================================================================================
  FIN DE ARCHIVO: app/main.py
================================================================================


================================================================================
  ARCHIVO: app/models.py
================================================================================

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
    inversion_total = Column(Numeric(20, 2), default=0)
    valor_mercado = Column(Numeric(20, 2), default=0)
    pnl_total = Column(Numeric(20, 2), default=0)
    roi_porcentaje = Column(Numeric(10, 2), default=0)

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

    monto_usd = Column(Numeric(20, 2), default=0)
    precio_unitario = Column(Numeric(20, 8), nullable=False)
    cantidad = Column(Numeric(20, 8), nullable=False)
    fee = Column(Numeric(20, 4), default=0)
    exchange = Column(String(50), default="binance")

    timestamp = Column(DateTime, default=datetime.utcnow)
    notas = Column(Text, default="")

    pnl_realizado = Column(Numeric(20, 2), default=0)

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
    riesgo_beneficio = Column(Numeric(5, 2))
    monto_planificado = Column(Numeric(20, 2), default=0)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_ejecucion = Column(DateTime)
    confianza = Column(Integer, default=3)
    notas_analisis = Column(Text, default="")
    resultado_pnl = Column(Numeric(20, 2))

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

# ─── CONFIGURACION DB ───
DATABASE_URL = "sqlite:///./crypto_crm.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)


================================================================================
  FIN DE ARCHIVO: app/models.py
================================================================================


================================================================================
  ARCHIVO: app/schemas.py
================================================================================

from pydantic import BaseModel, Field, validator
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


================================================================================
  FIN DE ARCHIVO: app/schemas.py
================================================================================


================================================================================
  ARCHIVO: app/tasks.py
================================================================================

"""
Tareas en background con Celery.
Ejecuta: celery -A app.tasks worker --beat --loglevel=info
"""
from celery import Celery
from sqlalchemy.orm import sessionmaker
from app.models import engine, ClienteCripto, EstadoCliente, Tarea
from app.services.crm_service import CRMService
from app.services.analytics import AnalyticsService
from app.services.exchange_sync import ExchangeConnector
from datetime import datetime, timedelta

app = Celery('crypto_crm', broker='redis://localhost:6379/0')

SessionLocal = sessionmaker(bind=engine)

@app.task
def verificar_alertas_programadas():
    """Revisa cada hora si algun cliente necesita atencion"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        analytics = AnalyticsService(db)

        alertas = analytics.alertas_inteligentes()

        for alerta in alertas:
            if alerta["nivel"] in ["CRITICO", "ADVERTENCIA"]:
                existente = db.query(Tarea).filter(
                    Tarea.cliente.has(symbol=alerta["symbol"]),
                    Tarea.tipo_tarea == alerta["accion_sugerida"],
                    Tarea.completada == False
                ).first()

                if not existente:
                    crm.crear_tarea(
                        symbol=alerta["symbol"],
                        tipo=alerta["accion_sugerida"],
                        descripcion=alerta["mensaje"],
                        dias=0 if alerta["nivel"] == "CRITICO" else 1,
                        prioridad=1 if alerta["nivel"] == "CRITICO" else 2
                    )

        return f"Alertas verificadas: {len(alertas)} generadas"
    finally:
        db.close()

@app.task
def sincronizar_precios():
    """
    Actualiza precios de mercado para todos los clientes con cantidad > 0
    usando la API pública de Binance.
    """
    db = SessionLocal()
    try:
        crm = CRMService(db)
        connector = ExchangeConnector()
        clientes = db.query(ClienteCripto).filter(ClienteCripto.cantidad_total > 0).all()

        actualizados = 0
        for cliente in clientes:
            precio = connector.obtener_precio(cliente.symbol)
            if precio > 0:
                crm.actualizar_precio_mercado(cliente.symbol, precio)
                actualizados += 1
            else:
                print(f"No se pudo obtener precio para {cliente.symbol}")

        return f"Precios actualizados para {actualizados} de {len(clientes)} clientes"
    finally:
        db.close()

@app.task
def reporte_diario():
    """Genera reporte diario del portafolio"""
    db = SessionLocal()
    try:
        crm = CRMService(db)
        resumen = crm.resumen_portafolio()

        reporte = f"""
📊 REPORTE DIARIO CRM CRYPTO
━━━━━━━━━━━━━━━━━━━━━━
Clientes activos: {resumen['clientes_activos']}
VIP: {resumen['clientes_vip']} | Peligro: {resumen['clientes_peligro']}
PnL Total: ${resumen['pnl_total']}
ROI: {resumen['roi_porcentaje']}%
Tareas pendientes: {resumen['tareas_pendientes']}
Oportunidades abiertas: {resumen['oportunidades_abiertas']}
━━━━━━━━━━━━━━━━━━━━━━
        """
        return reporte
    finally:
        db.close()


================================================================================
  FIN DE ARCHIVO: app/tasks.py
================================================================================


================================================================================
  ARCHIVO: app/services/__init__.py
================================================================================

# Services module


================================================================================
  FIN DE ARCHIVO: app/services/__init__.py
================================================================================


================================================================================
  ARCHIVO: app/services/crm_service.py
================================================================================

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    ClienteCripto, Interaccion, Oportunidad, Tarea, LoteCompra,
    EstadoCliente, TipoInteraccion
)

class CRMService:
    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════
    # GESTION DE CLIENTES (CRIPTO)
    # ═══════════════════════════════════════

    def registrar_cliente(self, symbol: str, nombre: str = None, 
                          categoria: str = "desconocida", **kwargs) -> ClienteCripto:
        symbol = symbol.upper()
        existente = self.db.query(ClienteCripto).filter_by(symbol=symbol).first()
        if existente:
            raise ValueError(f"El cliente {symbol} ya existe en el CRM")

        cliente = ClienteCripto(
            symbol=symbol,
            nombre=nombre or symbol,
            categoria=categoria,
            **kwargs
        )
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def obtener_cliente(self, symbol: str) -> Optional[ClienteCripto]:
        return self.db.query(ClienteCripto).filter_by(symbol=symbol.upper()).first()

    def listar_clientes(self, estado: str = None, categoria: str = None,
                        min_roi: float = None, tags: str = None) -> List[ClienteCripto]:
        query = self.db.query(ClienteCripto)
        if estado:
            query = query.filter(ClienteCripto.estado == estado)
        if categoria:
            query = query.filter(ClienteCripto.categoria == categoria)
        if min_roi is not None:
            query = query.filter(ClienteCripto.roi_porcentaje >= min_roi)
        if tags:
            query = query.filter(ClienteCripto.tags.contains(tags))
        return query.order_by(ClienteCripto.prioridad).all()

    def actualizar_estado_cliente(self, symbol: str) -> Optional[ClienteCripto]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return None

        roi = float(cliente.roi_porcentaje) if cliente.roi_porcentaje else 0
        cantidad = float(cliente.cantidad_total) if cliente.cantidad_total else 0

        if cantidad == 0:
            nuevo_estado = EstadoCliente.PROSPECTO
        elif roi > 50:
            nuevo_estado = EstadoCliente.VIP
        elif roi < -20:
            nuevo_estado = EstadoCliente.ACTIVO_PELIGRO
        elif roi == 0 and cantidad > 0:
            nuevo_estado = EstadoCliente.DORMANTE
        elif roi > 0:
            nuevo_estado = EstadoCliente.ACTIVO_COMPRA
        else:
            nuevo_estado = EstadoCliente.ACTIVO_PELIGRO

        cliente.estado = nuevo_estado
        self.db.commit()
        return cliente

    def actualizar_precio_mercado(self, symbol: str, precio: float) -> ClienteCripto:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")

        cliente.precio_actual = Decimal(str(precio))
        cantidad = float(cliente.cantidad_total)

        if cantidad > 0:
            cliente.valor_mercado = Decimal(str(precio * cantidad))
            costo_total = float(cliente.cantidad_total) * float(cliente.costo_promedio)
            if costo_total > 0:
                cliente.pnl_total = cliente.valor_mercado - Decimal(str(costo_total))
                cliente.roi_porcentaje = (cliente.pnl_total / Decimal(str(costo_total))) * 100

        self.db.commit()
        self.actualizar_estado_cliente(symbol)
        return cliente

    # ═══════════════════════════════════════
    # INTERACCIONES CON FIFO Y COMISIONES
    # ═══════════════════════════════════════

    def registrar_compra(self, symbol: str, cantidad: float, precio: float,
                         fee: float = 0.0, exchange: str = "binance", notas: str = "") -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Criptomoneda {symbol} no registrada")

        costo_total = cantidad * precio + fee
        precio_con_fee = costo_total / cantidad

        lote = LoteCompra(
            cliente_id=cliente.id,
            cantidad=Decimal(str(cantidad)),
            cantidad_restante=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio_con_fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(lote)

        monto = cantidad * precio
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.COMPRA,
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio)),
            monto_usd=Decimal(str(monto)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)

        total_previo = float(cliente.cantidad_total) * float(cliente.costo_promedio)
        total_nuevo = costo_total
        nueva_cantidad = float(cliente.cantidad_total) + cantidad
        if nueva_cantidad > 0:
            cliente.costo_promedio = Decimal(str((total_previo + total_nuevo) / nueva_cantidad))
        cliente.cantidad_total = Decimal(str(nueva_cantidad))
        cliente.inversion_total += Decimal(str(costo_total))

        self.db.commit()
        self.db.refresh(lote)
        self.actualizar_estado_cliente(symbol)

        return {"lote": lote, "interaccion": interaccion}

    def registrar_venta_fifo(self, symbol: str, cantidad_vender: float, precio_venta: float,
                             fee: float = 0.0, exchange: str = "binance", notas: str = "") -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        cantidad_vender = Decimal(str(cantidad_vender))
        if cantidad_vender > cliente.cantidad_total:
            raise ValueError(f"No hay suficiente cantidad para vender. Disponible: {cliente.cantidad_total}")

        lotes = self.db.query(LoteCompra).filter(
            LoteCompra.cliente_id == cliente.id,
            LoteCompra.cantidad_restante > 0
        ).order_by(LoteCompra.fecha_compra.asc()).all()

        if not lotes:
            raise ValueError("No hay lotes de compra para este cliente")

        cantidad_a_vender = cantidad_vender
        pnl_total = Decimal("0")
        detalles_consumo = []

        for lote in lotes:
            if cantidad_a_vender <= 0:
                break
            disponible = lote.cantidad_restante
            a_consumir = min(disponible, cantidad_a_vender)

            precio_compra_con_fee = lote.precio_unitario
            precio_venta_dec = Decimal(str(precio_venta))
            pnl_lote = (precio_venta_dec - precio_compra_con_fee) * a_consumir
            pnl_total += pnl_lote

            lote.cantidad_restante -= a_consumir
            cantidad_a_vender -= a_consumir

            detalles_consumo.append({
                "lote_id": lote.id,
                "cantidad": float(a_consumir),
                "precio_compra": float(precio_compra_con_fee),
                "pnl_lote": float(pnl_lote)
            })

        pnl_total -= Decimal(str(fee))
        cantidad_vendida = cantidad_vender - cantidad_a_vender
        monto = float(cantidad_vendida) * precio_venta

        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion.VENTA,
            cantidad=cantidad_vendida,
            precio_unitario=Decimal(str(precio_venta)),
            monto_usd=Decimal(str(monto)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas,
            pnl_realizado=pnl_total
        )
        self.db.add(interaccion)

        nueva_cantidad = cliente.cantidad_total - cantidad_vendida
        cliente.cantidad_total = nueva_cantidad
        cliente.pnl_total += pnl_total

        if nueva_cantidad > 0:
            lotes_restantes = self.db.query(LoteCompra).filter(
                LoteCompra.cliente_id == cliente.id,
                LoteCompra.cantidad_restante > 0
            ).all()
            inversion_restante = sum(float(l.cantidad_restante) * float(l.precio_unitario) for l in lotes_restantes)
            cliente.costo_promedio = Decimal(str(inversion_restante / float(nueva_cantidad))) if nueva_cantidad > 0 else Decimal("0")
        else:
            cliente.costo_promedio = Decimal("0")

        self.db.commit()
        self.actualizar_estado_cliente(symbol)

        return {
            "interaccion": interaccion,
            "pnl_total": float(pnl_total),
            "detalle_lotes": detalles_consumo
        }

    def registrar_interaccion_general(self, symbol: str, tipo: str, cantidad: float, precio: float,
                                      fee: float = 0.0, exchange: str = "binance", notas: str = ""):
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")
        interaccion = Interaccion(
            cliente_id=cliente.id,
            tipo=TipoInteraccion(tipo),
            cantidad=Decimal(str(cantidad)),
            precio_unitario=Decimal(str(precio)),
            monto_usd=Decimal(str(cantidad * precio)),
            fee=Decimal(str(fee)),
            exchange=exchange,
            notas=notas
        )
        self.db.add(interaccion)
        if tipo in ["staking", "airdrop", "dividendo"]:
            cliente.cantidad_total += Decimal(str(cantidad))
        self.db.commit()
        return {"interaccion": interaccion}

    def registrar_interaccion(self, symbol: str, tipo: str, cantidad: float, precio: float,
                              fee: float = 0.0, exchange: str = "binance", notas: str = ""):
        return self.registrar_interaccion_general(symbol, tipo, cantidad, precio, fee, exchange, notas)

    def eliminar_interaccion(self, interaccion_id: int) -> Dict[str, Any]:
        interaccion = self.db.query(Interaccion).filter_by(id=interaccion_id).first()
        if not interaccion:
            raise ValueError("Interacción no encontrada")

        cliente = interaccion.cliente
        symbol = cliente.symbol
        tipo_eliminado = interaccion.tipo.value
        cantidad_eliminada = float(interaccion.cantidad)

        self.db.delete(interaccion)
        self.db.commit()

        self.recalcular_cliente_desde_cero(symbol)

        return {
            "mensaje": f"Interacción {interaccion_id} de tipo {tipo_eliminado} eliminada",
            "cliente": symbol,
            "cantidad_afectada": cantidad_eliminada
        }

    def recalcular_cliente_desde_cero(self, symbol: str):
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no encontrado")

        self.db.query(LoteCompra).filter(LoteCompra.cliente_id == cliente.id).delete()
        self.db.commit()

        cliente.cantidad_total = Decimal("0")
        cliente.costo_promedio = Decimal("0")
        cliente.inversion_total = Decimal("0")
        cliente.pnl_total = Decimal("0")
        cliente.valor_mercado = Decimal("0")
        cliente.roi_porcentaje = Decimal("0")
        self.db.commit()

        interacciones = self.db.query(Interaccion).filter(
            Interaccion.cliente_id == cliente.id
        ).order_by(Interaccion.timestamp.asc()).all()

        for inter in interacciones:
            tipo = inter.tipo.value
            cantidad = float(inter.cantidad)
            precio = float(inter.precio_unitario)
            fee = float(inter.fee)

            if tipo == "compra":
                costo_total = cantidad * precio + fee
                precio_con_fee = costo_total / cantidad

                lote = LoteCompra(
                    cliente_id=cliente.id,
                    cantidad=Decimal(str(cantidad)),
                    cantidad_restante=Decimal(str(cantidad)),
                    precio_unitario=Decimal(str(precio_con_fee)),
                    exchange=inter.exchange,
                    notas=inter.notas
                )
                self.db.add(lote)

                total_previo = float(cliente.cantidad_total) * float(cliente.costo_promedio)
                nueva_cantidad = float(cliente.cantidad_total) + cantidad
                if nueva_cantidad > 0:
                    cliente.costo_promedio = Decimal(str((total_previo + costo_total) / nueva_cantidad))
                cliente.cantidad_total = Decimal(str(nueva_cantidad))
                cliente.inversion_total += Decimal(str(costo_total))

            elif tipo == "venta":
                cantidad_vender = Decimal(str(cantidad))
                lotes = self.db.query(LoteCompra).filter(
                    LoteCompra.cliente_id == cliente.id,
                    LoteCompra.cantidad_restante > 0
                ).order_by(LoteCompra.fecha_compra.asc()).all()

                cantidad_a_vender = cantidad_vender
                pnl_total = Decimal("0")

                for lote in lotes:
                    if cantidad_a_vender <= 0:
                        break
                    disponible = lote.cantidad_restante
                    a_consumir = min(disponible, cantidad_a_vender)

                    pnl_lote = (Decimal(str(precio)) - lote.precio_unitario) * a_consumir
                    pnl_total += pnl_lote

                    lote.cantidad_restante -= a_consumir
                    cantidad_a_vender -= a_consumir

                pnl_total -= Decimal(str(fee))
                cantidad_vendida = cantidad_vender - cantidad_a_vender

                nueva_cantidad = float(cliente.cantidad_total) - float(cantidad_vendida)
                cliente.cantidad_total = Decimal(str(nueva_cantidad))
                cliente.pnl_total += pnl_total

                if nueva_cantidad > 0:
                    lotes_restantes = self.db.query(LoteCompra).filter(
                        LoteCompra.cliente_id == cliente.id,
                        LoteCompra.cantidad_restante > 0
                    ).all()
                    inversion_restante = sum(float(l.cantidad_restante) * float(l.precio_unitario) for l in lotes_restantes)
                    cliente.costo_promedio = Decimal(str(inversion_restante / nueva_cantidad))
                else:
                    cliente.costo_promedio = Decimal("0")

                inter.pnl_realizado = pnl_total

            else:
                if tipo in ["staking", "airdrop", "dividendo"]:
                    cliente.cantidad_total += Decimal(str(cantidad))

        if float(cliente.cantidad_total) > 0:
            precio_actual = float(cliente.precio_actual) if cliente.precio_actual else 0
            cliente.valor_mercado = Decimal(str(precio_actual * float(cliente.cantidad_total)))
            inversion_total = float(cliente.inversion_total)
            if inversion_total > 0:
                cliente.pnl_total = cliente.valor_mercado - Decimal(str(inversion_total))
                cliente.roi_porcentaje = (cliente.pnl_total / Decimal(str(inversion_total))) * 100

        self.db.commit()
        self.actualizar_estado_cliente(symbol)

    def historial_interacciones(self, symbol: str) -> List[Interaccion]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(Interaccion).filter_by(cliente_id=cliente.id)\
                   .order_by(Interaccion.timestamp.desc()).all()

    def obtener_lotes_cliente(self, symbol: str) -> List[LoteCompra]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return []
        return self.db.query(LoteCompra).filter_by(cliente_id=cliente.id)\
                   .order_by(LoteCompra.fecha_compra.asc()).all()

    def obtener_todos_lotes_con_clientes(self) -> Dict[str, List[LoteCompra]]:
        lotes = self.db.query(LoteCompra).join(ClienteCripto).filter(LoteCompra.cantidad_restante > 0).all()
        resultado = {}
        for lote in lotes:
            symbol = lote.cliente.symbol
            if symbol not in resultado:
                resultado[symbol] = []
            resultado[symbol].append(lote)
        return resultado

    def calcular_pnl_fifo_para_cliente(self, symbol: str, precio_actual: float) -> Dict[str, Any]:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            return {"error": "Cliente no encontrado"}
        lotes = self.db.query(LoteCompra).filter(
            LoteCompra.cliente_id == cliente.id,
            LoteCompra.cantidad_restante > 0
        ).order_by(LoteCompra.fecha_compra.asc()).all()
        
        cantidad_total = 0.0
        costo_total = 0.0
        for lote in lotes:
            cant = float(lote.cantidad_restante)
            cantidad_total += cant
            costo_total += cant * float(lote.precio_unitario)
        
        valor_actual = cantidad_total * precio_actual
        pnl = valor_actual - costo_total
        return {
            "pnl_total": pnl,
            "costo_total": costo_total,
            "valor_actual": valor_actual,
            "cantidad_total": cantidad_total
        }

    # ═══════════════════════════════════════
    # OPORTUNIDADES
    # ═══════════════════════════════════════
    def crear_oportunidad(self, symbol: str, tipo: str,
                          entrada: float, objetivo: float, stop: float,
                          monto_planificado: float = 0,
                          confianza: int = 3, notas: str = "") -> Oportunidad:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        riesgo = abs(entrada - stop)
        beneficio = abs(objetivo - entrada)
        rb = beneficio / riesgo if riesgo > 0 else 0

        opp = Oportunidad(
            cliente_id=cliente.id,
            tipo=tipo,
            precio_entrada=Decimal(str(entrada)),
            precio_objetivo=Decimal(str(objetivo)),
            precio_stop_loss=Decimal(str(stop)),
            riesgo_beneficio=Decimal(str(round(rb, 2))),
            monto_planificado=Decimal(str(monto_planificado)),
            confianza=confianza,
            notas_analisis=notas
        )
        self.db.add(opp)
        self.db.commit()
        self.db.refresh(opp)
        return opp

    def cerrar_oportunidad(self, opp_id: int, estado: str, pnl: float = None):
        opp = self.db.query(Oportunidad).filter_by(id=opp_id).first()
        if not opp:
            raise ValueError("Oportunidad no encontrada")
        opp.estado = estado
        opp.fecha_ejecucion = datetime.utcnow()
        if pnl is not None:
            opp.resultado_pnl = Decimal(str(pnl))
        self.db.commit()
        return opp

    def oportunidades_por_estado(self, estado: str = "abierta") -> List[Oportunidad]:
        return self.db.query(Oportunidad).filter_by(estado=estado)\
                   .order_by(Oportunidad.confianza.desc()).all()

    # ═══════════════════════════════════════
    # TAREAS
    # ═══════════════════════════════════════
    def crear_tarea(self, symbol: str, tipo: str, descripcion: str,
                    dias: int = 1, prioridad: int = 2) -> Tarea:
        cliente = self.obtener_cliente(symbol)
        if not cliente:
            raise ValueError(f"Cliente {symbol} no existe")

        tarea = Tarea(
            cliente_id=cliente.id,
            tipo_tarea=tipo,
            descripcion=descripcion,
            fecha_limite=datetime.utcnow() + timedelta(days=dias),
            prioridad=prioridad
        )
        self.db.add(tarea)
        self.db.commit()
        self.db.refresh(tarea)
        return tarea

    def completar_tarea(self, tarea_id: int) -> Tarea:
        tarea = self.db.query(Tarea).filter_by(id=tarea_id).first()
        if not tarea:
            raise ValueError("Tarea no encontrada")
        tarea.completada = True
        tarea.fecha_completada = datetime.utcnow()
        self.db.commit()
        return tarea

    def tareas_pendientes(self, urgentes: bool = False) -> List[Tarea]:
        query = self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= datetime.utcnow()
        )
        if urgentes:
            query = query.filter(Tarea.prioridad == 1)
        return query.order_by(Tarea.fecha_limite).all()

    def tareas_proximas(self, dias: int = 3) -> List[Tarea]:
        limite = datetime.utcnow() + timedelta(days=dias)
        return self.db.query(Tarea).filter(
            Tarea.completada == False,
            Tarea.fecha_limite <= limite
        ).order_by(Tarea.fecha_limite).all()

    # ═══════════════════════════════════════
    # ANALYTICS & REPORTES
    # ═══════════════════════════════════════
    def resumen_portafolio(self) -> dict:
        clientes = self.db.query(ClienteCripto).all()
        interacciones = self.db.query(Interaccion).count()
        oportunidades_abiertas = self.db.query(Oportunidad).filter_by(estado="abierta").count()
        tareas_pend = len(self.tareas_pendientes())

        total_invertido = sum(float(c.inversion_total) for c in clientes)
        total_valor = sum(float(c.valor_mercado) for c in clientes)
        pnl_total = total_valor - total_invertido
        roi = (pnl_total / total_invertido * 100) if total_invertido > 0 else 0

        return {
            "total_clientes": len(clientes),
            "clientes_activos": len([c for c in clientes if float(c.cantidad_total) > 0]),
            "clientes_vip": len([c for c in clientes if c.estado == EstadoCliente.VIP]),
            "clientes_peligro": len([c for c in clientes if c.estado == EstadoCliente.ACTIVO_PELIGRO]),
            "total_invertido": round(total_invertido, 2),
            "total_valor_mercado": round(total_valor, 2),
            "pnl_total": round(pnl_total, 2),
            "roi_porcentaje": round(roi, 2),
            "total_interacciones": interacciones,
            "oportunidades_abiertas": oportunidades_abiertas,
            "tareas_pendientes": tareas_pend
        }

    def top_performers(self, limit: int = 5) -> List[ClienteCripto]:
        return self.db.query(ClienteCripto)\
                   .filter(ClienteCripto.roi_porcentaje > 0)\
                   .order_by(ClienteCripto.roi_porcentaje.desc())\
                   .limit(limit).all()

    def peores_performers(self, limit: int = 5) -> List[ClienteCripto]:
        return self.db.query(ClienteCripto)\
                   .filter(ClienteCripto.roi_porcentaje < 0)\
                   .order_by(ClienteCripto.roi_porcentaje.asc())\
                   .limit(limit).all()

    def clientes_dormidos(self, dias: int = 30) -> List[ClienteCripto]:
        limite = datetime.utcnow() - timedelta(days=dias)
        return self.db.query(ClienteCripto).filter(
            ClienteCripto.fecha_ultimo_contacto < limite,
            ClienteCripto.cantidad_total > 0
        ).all()


================================================================================
  FIN DE ARCHIVO: app/services/crm_service.py
================================================================================


================================================================================
  ARCHIVO: app/services/analytics.py
================================================================================

"""
Modulo de analytics para el CRM Crypto.
Genera reportes, metricas y insights.
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models import ClienteCripto, Interaccion, Oportunidad, Tarea, TipoInteraccion

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def rendimiento_por_categoria(self) -> List[Dict]:
        result = self.db.query(
            ClienteCripto.categoria,
            func.count(ClienteCripto.id).label('count'),
            func.avg(ClienteCripto.roi_porcentaje).label('avg_roi'),
            func.sum(ClienteCripto.pnl_total).label('total_pnl')
        ).group_by(ClienteCripto.categoria).all()

        return [
            {
                "categoria": r.categoria,
                "monedas": r.count,
                "roi_promedio": round(float(r.avg_roi or 0), 2),
                "pnl_total": round(float(r.total_pnl or 0), 2)
            }
            for r in result
        ]

    def evolucion_pnl_mensual(self, meses: int = 6) -> List[Dict]:
        desde = datetime.utcnow() - timedelta(days=meses*30)
        result = self.db.query(
            func.strftime('%Y-%m', Interaccion.timestamp).label('mes'),
            func.sum(Interaccion.pnl_realizado).label('pnl')
        ).filter(
            Interaccion.timestamp >= desde,
            Interaccion.tipo == TipoInteraccion.VENTA
        ).group_by('mes').order_by('mes').all()

        return [
            {"mes": r.mes, "pnl_realizado": round(float(r.pnl or 0), 2)}
            for r in result
        ]

    def metricas_oportunidades(self) -> Dict:
        total = self.db.query(Oportunidad).count()
        abiertas = self.db.query(Oportunidad).filter_by(estado="abierta").count()
        ejecutadas = self.db.query(Oportunidad).filter_by(estado="ejecutada").count()
        canceladas = self.db.query(Oportunidad).filter_by(estado="cancelada").count()
        pnl_opps = self.db.query(func.sum(Oportunidad.resultado_pnl)).filter(
            Oportunidad.estado == "ejecutada"
        ).scalar()
        avg_rr = self.db.query(func.avg(Oportunidad.riesgo_beneficio)).filter(
            Oportunidad.estado == "ejecutada"
        ).scalar()

        return {
            "total_oportunidades": total,
            "abiertas": abiertas,
            "ejecutadas": ejecutadas,
            "canceladas": canceladas,
            "tasa_ejecucion": round(ejecutadas / total * 100, 1) if total > 0 else 0,
            "pnl_total_oportunidades": round(float(pnl_opps or 0), 2),
            "riesgo_beneficio_promedio": round(float(avg_rr or 0), 2)
        }

    def eficiencia_tareas(self, dias: int = 30) -> Dict:
        desde = datetime.utcnow() - timedelta(days=dias)
        total = self.db.query(Tarea).filter(Tarea.fecha_creacion >= desde).count()
        completadas = self.db.query(Tarea).filter(
            Tarea.completada == True,
            Tarea.fecha_creacion >= desde
        ).count()
        return {
            "tareas_creadas": total,
            "tareas_completadas": completadas,
            "tasa_completitud": round(completadas / total * 100, 1) if total > 0 else 0,
            "periodo_dias": dias
        }

    def distribucion_portafolio(self) -> List[Dict]:
        clientes = self.db.query(ClienteCripto).filter(
            ClienteCripto.cantidad_total > 0
        ).all()
        total_valor = sum(float(c.valor_mercado) for c in clientes)
        return [
            {
                "symbol": c.symbol,
                "valor": round(float(c.valor_mercado), 2),
                "porcentaje": round(float(c.valor_mercado) / total_valor * 100, 2) if total_valor > 0 else 0,
                "roi": round(float(c.roi_porcentaje), 2)
            }
            for c in sorted(clientes, key=lambda x: float(x.valor_mercado), reverse=True)
        ]

    def alertas_inteligentes(self) -> List[Dict]:
        alertas = []
        peligro = self.db.query(ClienteCripto).filter(
            ClienteCripto.roi_porcentaje < -20,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in peligro:
            alertas.append({
                "nivel": "CRITICO",
                "tipo": "perdida_excesiva",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} con perdida del {float(c.roi_porcentaje):.1f}%. Considerar stop o promediar.",
                "accion_sugerida": "revisar_stop_loss"
            })
        vip = self.db.query(ClienteCripto).filter(
            ClienteCripto.roi_porcentaje > 50,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in vip:
            alertas.append({
                "nivel": "INFO",
                "tipo": "take_profit_sugerido",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} ganando {float(c.roi_porcentaje):.1f}%. Considerar venta parcial.",
                "accion_sugerida": "vender_50_porciento"
            })
        dist = self.distribucion_portafolio()
        if dist:
            max_pos = dist[0]
            if max_pos["porcentaje"] > 30:
                alertas.append({
                    "nivel": "ADVERTENCIA",
                    "tipo": "concentracion_alta",
                    "symbol": max_pos["symbol"],
                    "mensaje": f"{max_pos['symbol']} representa {max_pos['porcentaje']}% del portafolio. Diversificar.",
                    "accion_sugerida": "rebalancear"
                })
        desde = datetime.utcnow() - timedelta(days=30)
        dormidos = self.db.query(ClienteCripto).filter(
            ClienteCripto.fecha_ultimo_contacto < desde,
            ClienteCripto.cantidad_total > 0
        ).all()
        for c in dormidos:
            alertas.append({
                "nivel": "BAJO",
                "tipo": "cliente_dormido",
                "symbol": c.symbol,
                "mensaje": f"{c.symbol} sin movimiento en 30+ dias. Revisar si mantener.",
                "accion_sugerida": "revision_estrategia"
            })
        return alertas


================================================================================
  FIN DE ARCHIVO: app/services/analytics.py
================================================================================


================================================================================
  ARCHIVO: app/services/exchange_sync.py
================================================================================

"""
Conector de exchanges usando CCXT.
Sincroniza portafolio real con el CRM.
Ahora con soporte para API pública de Binance (sin keys).
"""
from typing import Dict, List, Optional
import ccxt
from decimal import Decimal
from datetime import datetime
from app.models import ClienteCripto, TipoInteraccion
from app.services.crm_service import CRMService

class ExchangeConnector:
    def __init__(self, api_key: str = None, secret: str = None, exchange_id: str = "binance"):
        exchange_class = getattr(ccxt, exchange_id)
        config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        if api_key and secret:
            config['apiKey'] = api_key
            config['secret'] = secret
        self.exchange = exchange_class(config)
        self.is_authenticated = bool(api_key and secret)

    def obtener_precio(self, symbol: str, vs_currency: str = "USDT") -> float:
        try:
            ticker = self.exchange.fetch_ticker(f"{symbol}/{vs_currency}")
            return ticker['last'] or ticker['close'] or 0.0
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return 0.0

    def obtener_ticker(self, symbol: str, vs_currency: str = "USDT") -> Dict:
        try:
            ticker = self.exchange.fetch_ticker(f"{symbol}/{vs_currency}")
            return {
                "symbol": symbol,
                "last": ticker.get('last', 0),
                "bid": ticker.get('bid', 0),
                "ask": ticker.get('ask', 0),
                "change": ticker.get('change', 0),
                "percentage": ticker.get('percentage', 0),
                "volume": ticker.get('baseVolume', 0),
                "quoteVolume": ticker.get('quoteVolume', 0),
                "high": ticker.get('high', 0),
                "low": ticker.get('low', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error obteniendo ticker de {symbol}: {e}")
            return {}

    def obtener_velas(self, symbol: str, timeframe: str = "1h", limit: int = 100, vs_currency: str = "USDT") -> List[Dict]:
        try:
            ohlcv = self.exchange.fetch_ohlcv(f"{symbol}/{vs_currency}", timeframe=timeframe, limit=limit)
            velas = []
            for candle in ohlcv:
                velas.append({
                    "timestamp": candle[0],
                    "datetime": datetime.utcfromtimestamp(candle[0] / 1000).isoformat(),
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })
            return velas
        except Exception as e:
            print(f"Error obteniendo velas de {symbol}: {e}")
            return []

    def obtener_balance(self) -> Dict[str, float]:
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener balance.")
        balance = self.exchange.fetch_balance()
        return {
            k: float(v['total']) 
            for k, v in balance.items() 
            if isinstance(v, dict) and float(v.get('total', 0)) > 0
        }

    def obtener_historial_trades(self, symbol: str, limit: int = 100) -> List[dict]:
        if not self.is_authenticated:
            raise ValueError("Se requiere API key y secret para obtener historial de trades.")
        try:
            trades = self.exchange.fetch_my_trades(f"{symbol}/USDT", limit=limit)
            return trades
        except Exception as e:
            print(f"Error obteniendo trades de {symbol}: {e}")
            return []

    def sincronizar_portafolio(self, crm: CRMService):
        if not self.is_authenticated:
            print("No autenticado. No se puede sincronizar portafolio.")
            return False
        balance = self.obtener_balance()
        for symbol, cantidad in balance.items():
            if symbol in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                continue
            if cantidad <= 0:
                continue
            precio = self.obtener_precio(symbol)
            if precio == 0:
                continue
            cliente = crm.obtener_cliente(symbol)
            if not cliente:
                cliente = crm.registrar_cliente(
                    symbol=symbol,
                    nombre=symbol,
                    categoria="exchange_sync",
                    exchange_principal=self.exchange.id,
                    cantidad_total=Decimal(str(cantidad))
                )
                print(f"[SYNC] Nuevo cliente registrado: {symbol}")
            crm.actualizar_precio_mercado(symbol, precio)
            if not cliente.interacciones:
                crm.crear_tarea(
                    symbol=symbol,
                    tipo="revision_inicial",
                    descripcion=f"{symbol} sincronizado desde exchange. Revisar costo promedio manualmente.",
                    dias=1,
                    prioridad=3
                )
        return True

    def importar_historial(self, crm: CRMService, symbol: str):
        if not self.is_authenticated:
            raise ValueError("Se requiere autenticación para importar historial.")
        trades = self.obtener_historial_trades(symbol)
        for trade in trades:
            lado = trade.get('side', 'buy')
            tipo = TipoInteraccion.COMPRA if lado == 'buy' else TipoInteraccion.VENTA
            try:
                crm.registrar_interaccion(
                    symbol=symbol.replace('/USDT', ''),
                    tipo=tipo.value,
                    cantidad=trade['amount'],
                    precio=trade['price'],
                    fee=trade.get('fee', {}).get('cost', 0),
                    exchange=self.exchange.id,
                    notas=f"Importado desde exchange - Order: {trade.get('order', 'N/A')}"
                )
            except ValueError:
                pass
        return len(trades)


================================================================================
  FIN DE ARCHIVO: app/services/exchange_sync.py
================================================================================


================================================================================
  ARCHIVO: app/api/__init__.py
================================================================================

# API module


================================================================================
  FIN DE ARCHIVO: app/api/__init__.py
================================================================================


================================================================================
  ARCHIVO: app/api/clientes.py
================================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

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

    cantidad = float(cliente.cantidad_total) if cliente.cantidad_total else 0
    precio_actual = float(cliente.precio_actual) if cliente.precio_actual else 0
    costo_promedio = float(cliente.costo_promedio) if cliente.costo_promedio else 0
    
    if cantidad > 0:
        cliente.valor_mercado = Decimal(str(cantidad * precio_actual))
        inversion = cantidad * costo_promedio
        cliente.inversion_total = Decimal(str(inversion))
        cliente.pnl_total = cliente.valor_mercado - Decimal(str(inversion))
        if inversion > 0:
            cliente.roi_porcentaje = (cliente.pnl_total / Decimal(str(inversion))) * 100
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


================================================================================
  FIN DE ARCHIVO: app/api/clientes.py
================================================================================


================================================================================
  ARCHIVO: app/api/interacciones.py
================================================================================

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
    crm = CRMService(db)
    try:
        resultado = crm.eliminar_interaccion(interaccion_id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


================================================================================
  FIN DE ARCHIVO: app/api/interacciones.py
================================================================================


================================================================================
  ARCHIVO: app/api/oportunidades.py
================================================================================

from fastapi import APIRouter, Depends, HTTPException
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
def listar_oportunidades(estado: Optional[str] = "abierta", db: Session = Depends(get_db)):
    crm = CRMService(db)
    return crm.oportunidades_por_estado(estado)

@router.post("/{opp_id}/cerrar")
def cerrar_oportunidad(opp_id: int, estado: str, pnl: Optional[float] = None, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.cerrar_oportunidad(opp_id, estado, pnl)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


================================================================================
  FIN DE ARCHIVO: app/api/oportunidades.py
================================================================================


================================================================================
  ARCHIVO: app/api/tareas.py
================================================================================

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

@router.post("/{tarea_id}/completar")
def completar_tarea(tarea_id: int, db: Session = Depends(get_db)):
    crm = CRMService(db)
    try:
        return crm.completar_tarea(tarea_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


================================================================================
  FIN DE ARCHIVO: app/api/tareas.py
================================================================================


================================================================================
  ARCHIVO: app/api/lotes.py
================================================================================

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


================================================================================
  FIN DE ARCHIVO: app/api/lotes.py
================================================================================


================================================================================
  ARCHIVO: dashboard/streamlit_app.py
================================================================================

"""
Dashboard visual del CRM Crypto usando Streamlit.
Ejecuta: streamlit run dashboard/streamlit_app.py
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Crypto CRM Dashboard",
    page_icon="📊",
    layout="wide"
)

# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
st.sidebar.title("🪙 Crypto CRM")
st.sidebar.markdown("*Tratando criptomonedas como clientes*")

page = st.sidebar.radio("Navegacion", [
    "🏠 Dashboard",
    "👥 Clientes",
    "💱 Interacciones",
    "🎯 Oportunidades",
    "✅ Tareas",
    "📦 Lotes FIFO",
    "📈 Analytics",
    "📡 Mercado en Vivo",
    "⚙️ Configuracion"
])

# ═══════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════

def fetch(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}")
        return r.json()
    except:
        st.error("No se puede conectar a la API. Asegurate de que FastAPI este corriendo en puerto 8000")
        return None

def post(endpoint, data):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error {r.status_code} en POST: {r.text[:200]}")
            return None
    except Exception as e:
        st.error(f"Error en POST: {e}")
        return None

def put(endpoint, data):
    try:
        r = requests.put(f"{API_URL}{endpoint}", json=data)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error {r.status_code} en PUT: {r.text[:200]}")
            return None
    except Exception as e:
        st.error(f"Error en PUT: {e}")
        return None

def delete(endpoint):
    try:
        r = requests.delete(f"{API_URL}{endpoint}")
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error {r.status_code} en DELETE: {r.text[:200]}")
            return None
    except Exception as e:
        st.error(f"Error en DELETE: {e}")
        return None

def obtener_precio_real(symbol):
    try:
        r = requests.get(f"{API_URL}/precios/{symbol}")
        if r.status_code == 200:
            return r.json().get("price", 0)
    except:
        pass
    return 0

def obtener_ticker_real(symbol):
    try:
        r = requests.get(f"{API_URL}/ticker/{symbol}")
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def obtener_velas(symbol, timeframe="1h", limit=100):
    try:
        r = requests.get(f"{API_URL}/velas/{symbol}", params={"timeframe": timeframe, "limit": limit})
        if r.status_code == 200:
            return r.json().get("data", [])
    except:
        pass
    return []

# ═══════════════════════════════════════
# PAGINA: DASHBOARD
# ═══════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("📊 Dashboard Principal")
    data = fetch("/dashboard/resumen")
    if data:
        resumen = data.get("resumen", {})
        alertas = data.get("alertas", [])
        distribucion = data.get("distribucion", [])
        top = data.get("top_performers", [])

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Clientes Activos", resumen.get("clientes_activos", 0))
        col2.metric("VIP", resumen.get("clientes_vip", 0))
        col3.metric("En Peligro", resumen.get("clientes_peligro", 0))
        col4.metric("PnL Total", f"${resumen.get('pnl_total', 0):,.2f}")
        col5.metric("ROI", f"{resumen.get('roi_porcentaje', 0):.1f}%")

        st.divider()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Distribucion del Portafolio")
            if distribucion:
                df_dist = pd.DataFrame(distribucion)
                fig = px.pie(df_dist, values="porcentaje", names="symbol", hole=0.4, title="Por Valor de Mercado")
                st.plotly_chart(fig, width='stretch')
        with col_right:
            st.subheader("Top Performers")
            if top:
                df_top = pd.DataFrame(top)
                fig = px.bar(df_top, x="symbol", y="roi", color="roi", color_continuous_scale="RdYlGn", title="ROI por Moneda")
                st.plotly_chart(fig, width='stretch')

        st.subheader("🔔 Alertas Inteligentes")
        if alertas:
            for alerta in alertas:
                nivel = alerta["nivel"]
                color = {"CRITICO": "🔴", "ADVERTENCIA": "🟡", "INFO": "🟢", "BAJO": "🔵"}.get(nivel, "⚪")
                with st.expander(f"{color} [{nivel}] {alerta['symbol']} - {alerta['tipo']}"):
                    st.write(alerta["mensaje"])
                    st.caption(f"Accion sugerida: {alerta['accion_sugerida']}")
        else:
            st.success("No hay alertas activas. Todo en orden! 🎉")

# ═══════════════════════════════════════
# PAGINA: CLIENTES
# ═══════════════════════════════════════
elif page == "👥 Clientes":
    st.title("👥 Gestion de Clientes (Criptomonedas)")
    st.markdown("El PnL no realizado se calcula con **FIFO** (First In, First Out) e incluye comisiones.")

    clientes = fetch("/clientes/")
    if not clientes:
        st.warning("No hay clientes registrados. Crea uno nuevo en la pestaña '➕ Nuevo Cliente'")
        clientes = []

    if clientes:
        if st.button("Actualizar todos los precios desde Binance"):
            with st.spinner("Actualizando precios..."):
                for c in clientes:
                    precio_real = obtener_precio_real(c["symbol"])
                    if precio_real > 0:
                        post(f"/clientes/{c['symbol']}/actualizar-precio", {"precio": precio_real})
                st.success("Precios actualizados")
                st.rerun()

        lotes_data = fetch("/lotes/all")
        if not lotes_data:
            lotes_data = {}

        df_data = []
        for c in clientes:
            symbol = c["symbol"]
            cantidad_total = float(c.get("cantidad_total", 0))
            precio_actual = float(c.get("precio_actual", 0))
            
            lotes_cliente = lotes_data.get(symbol, [])
            cantidad_restante_fifo = 0.0
            costo_total_fifo = 0.0
            for lote in lotes_cliente:
                cant = lote["cantidad_restante"]
                cantidad_restante_fifo += cant
                costo_total_fifo += cant * lote["precio_unitario"]
            
            valor_actual_fifo = cantidad_restante_fifo * precio_actual
            pnl_no_realizado_fifo = valor_actual_fifo - costo_total_fifo
            
            costo_prom = float(c.get("costo_promedio", 0))

            df_data.append({
                "symbol": symbol,
                "nombre": c.get("nombre", ""),
                "categoria": c.get("categoria", ""),
                "estado": c.get("estado", ""),
                "cantidad_total": cantidad_total,
                "costo_promedio": costo_prom,
                "precio_actual": precio_actual,
                "valor_mercado": float(c.get("valor_mercado", 0)),
                "pnl_realizado": float(c.get("pnl_total", 0)),
                "roi_realizado_pct": float(c.get("roi_porcentaje", 0)),
                "pnl_fifo_no_realizado": pnl_no_realizado_fifo,
                "roi_fifo_pct": (pnl_no_realizado_fifo / costo_total_fifo * 100) if costo_total_fifo > 0 else 0,
                "prioridad": c.get("prioridad", 3),
                "tags": c.get("tags", ""),
                "notas": c.get("notas_personal", "")
            })

        df = pd.DataFrame(df_data)

        column_config = {
            "symbol": st.column_config.TextColumn("Symbol", disabled=True),
            "nombre": st.column_config.TextColumn("Nombre"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=["layer1","layer2","defi","meme","stablecoin","nft","gaming","ai","infra","desconocida"]),
            "estado": st.column_config.SelectboxColumn("Estado", options=["PROSPECTO","ACTIVO_COMPRA","ACTIVO_PELIGRO","DORMANTE","CHURN","VIP"]),
            "cantidad_total": st.column_config.NumberColumn("Cantidad Total", format="%.8f"),
            "costo_promedio": st.column_config.NumberColumn("Costo Promedio (USD)", format="$%.4f", disabled=True),
            "precio_actual": st.column_config.NumberColumn("Precio Actual (USD)", format="$%.4f", disabled=True),
            "valor_mercado": st.column_config.NumberColumn("Valor Mercado (USD)", format="$%.2f", disabled=True),
            "pnl_realizado": st.column_config.NumberColumn("PnL Realizado (USD)", format="$%.2f", disabled=True),
            "roi_realizado_pct": st.column_config.NumberColumn("ROI Realizado %", format="%.2f%%", disabled=True),
            "pnl_fifo_no_realizado": st.column_config.NumberColumn("PnL FIFO No Realizado (USD)", format="$%.2f"),
            "roi_fifo_pct": st.column_config.NumberColumn("ROI FIFO %", format="%.2f%%"),
            "prioridad": st.column_config.NumberColumn("Prioridad", min_value=1, max_value=5, step=1),
            "tags": st.column_config.TextColumn("Tags"),
            "notas": st.column_config.TextColumn("Notas")
        }

        edited_df = st.data_editor(
            df,
            column_config=column_config,
            width='stretch',
            hide_index=True,
            key="clientes_editor",
            disabled=["symbol", "costo_promedio", "precio_actual", "valor_mercado", "pnl_realizado", "roi_realizado_pct", "pnl_fifo_no_realizado", "roi_fifo_pct"]
        )

        if st.button("Guardar cambios realizados"):
            for idx, row in edited_df.iterrows():
                original = df.iloc[idx]
                if not row.equals(original):
                    symbol = row["symbol"]
                    update_data = {}
                    for col in ["nombre", "categoria", "estado", "cantidad_total", "costo_promedio", "prioridad", "tags", "notas"]:
                        if row[col] != original[col]:
                            value = row[col]
                            if col == "estado" and value:
                                value = value.upper()
                            update_data[col] = value
                    if update_data:
                        if "notas" in update_data:
                            update_data["notas_personal"] = update_data.pop("notas")
                        resp = put(f"/clientes/{symbol}", update_data)
                        if resp:
                            st.success(f"Cliente {symbol} actualizado")
                        else:
                            st.error(f"Error actualizando {symbol}")
            st.rerun()

        st.subheader("Actualizar Precio Individual y Ver Detalle FIFO")
        col_sel, col_btn = st.columns([3,1])
        with col_sel:
            selected_symbol = st.selectbox("Selecciona un cliente", [c["symbol"] for c in clientes] if clientes else [])
        with col_btn:
            if st.button("Actualizar precio desde Binance"):
                if selected_symbol:
                    precio_real = obtener_precio_real(selected_symbol)
                    if precio_real > 0:
                        resp = post(f"/clientes/{selected_symbol}/actualizar-precio", {"precio": precio_real})
                        if resp:
                            st.success(f"Precio de {selected_symbol} actualizado a ${precio_real}")
                            st.rerun()
                        else:
                            st.error("Error al actualizar")
                    else:
                        st.error("No se pudo obtener precio de Binance")

        if selected_symbol:
            st.subheader(f"📦 Lotes de {selected_symbol} (FIFO)")
            lotes_cliente = fetch(f"/lotes/cliente/{selected_symbol}")
            if lotes_cliente:
                df_lotes = pd.DataFrame([{
                    "Fecha": l["fecha_compra"],
                    "Cantidad Inicial": float(l["cantidad"]),
                    "Cantidad Restante": float(l["cantidad_restante"]),
                    "Precio Compra (incluye fee)": float(l["precio_unitario"]),
                    "Exchange": l.get("exchange", ""),
                    "Notas": l.get("notas", "")
                } for l in lotes_cliente])
                st.dataframe(df_lotes, width='stretch')
            else:
                st.info("No hay lotes activos para este cliente.")

    with st.expander("➕ Nuevo Cliente"):
        with st.form("nuevo_cliente"):
            symbol = st.text_input("Symbol (ej: BTC, ETH)").upper()
            nombre = st.text_input("Nombre completo (opcional)")
            categoria = st.selectbox("Categoria", ["layer1","layer2","defi","meme","stablecoin","nft","gaming","ai","infra","desconocida"])
            tags = st.text_input("Tags (separados por coma)")
            notas = st.text_area("Notas personales")
            if st.form_submit_button("Registrar Cliente"):
                if symbol:
                    result = post("/clientes/", {
                        "symbol": symbol,
                        "nombre": nombre or symbol,
                        "categoria": categoria,
                        "tags": tags,
                        "notas_personal": notas
                    })
                    if result:
                        st.success(f"Cliente {symbol} registrado exitosamente!")
                        st.balloons()
                        st.rerun()

# ═══════════════════════════════════════
# PAGINA: INTERACCIONES
# ═══════════════════════════════════════
elif page == "💱 Interacciones":
    st.title("💱 Registro de Interacciones (FIFO para ventas)")

    with st.form("nueva_interaccion"):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Symbol del cliente").upper()
        with col2:
            tipo = st.selectbox("Tipo", ["compra", "venta", "staking", "unstaking", "dividendo", "airdrop"])
        exchange = st.text_input("Exchange", value="binance")
        cantidad = st.number_input("Cantidad", min_value=0.0, step=0.0001, format="%.8f")
        precio = st.number_input("Precio unitario (USD)", min_value=0.0, step=0.01)
        fee = st.number_input("Fee", min_value=0.0, step=0.01)
        notas = st.text_area("Notas de la interaccion")
        if st.form_submit_button("Registrar Interaccion"):
            if symbol and cantidad > 0 and precio > 0:
                result = post("/interacciones/", {
                    "cliente_symbol": symbol,
                    "tipo": tipo,
                    "cantidad": cantidad,
                    "precio_unitario": precio,
                    "fee": fee,
                    "exchange": exchange,
                    "notas": notas
                })
                if result:
                    st.success("Interaccion registrada!")
                    if tipo == "venta" and "detalle_lotes" in result:
                        st.subheader("Detalle FIFO de la venta:")
                        for det in result["detalle_lotes"]:
                            st.write(f"Lote {det['lote_id']}: {det['cantidad']} unidades a precio compra ${det['precio_compra']:.2f} → PnL: ${det['pnl_lote']:.2f}")
                        st.metric("PnL total de la venta", f"${result['pnl_total']:.2f}")
                    st.rerun()

    st.subheader("📜 Historial (puedes eliminar interacciones)")
    hist_symbol = st.text_input("Ver historial de", key="hist_symbol").upper()
    if hist_symbol:
        historial = fetch(f"/interacciones/cliente/{hist_symbol}")
        if historial:
            for idx, row in enumerate(historial):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2,1,1,1,2,2,1])
                with col1:
                    st.write(row.get("tipo", ""))
                with col2:
                    st.write(f"{float(row.get('cantidad', 0)):.8f}")
                with col3:
                    st.write(f"${float(row.get('precio_unitario', 0)):.2f}")
                with col4:
                    st.write(f"${float(row.get('monto_usd', 0)):.2f}")
                with col5:
                    st.write(row.get("timestamp", "")[:16])
                with col6:
                    st.write(f"${float(row.get('pnl_realizado', 0)):.2f}")
                with col7:
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        if st.checkbox(f"Confirmar eliminación de {row['tipo']} {row['cantidad']} @ ${row['precio_unitario']}", key=f"confirm_{row['id']}"):
                            resp = delete(f"/interacciones/{row['id']}")
                            if resp:
                                st.success(f"Interacción {row['id']} eliminada")
                                st.rerun()
                st.divider()
        else:
            st.info("No hay interacciones para este cliente.")

# ═══════════════════════════════════════
# PAGINA: LOTES FIFO
# ═══════════════════════════════════════
elif page == "📦 Lotes FIFO":
    st.title("📦 Lotes de Compra (FIFO)")
    st.info("Cada compra genera un lote. Las ventas consumen lotes desde el más antiguo (FIFO).")

    symbol = st.selectbox("Selecciona un cliente", [c["symbol"] for c in fetch("/clientes/") or []])
    if symbol:
        lotes = fetch(f"/lotes/cliente/{symbol}")
        if lotes:
            df_lotes = pd.DataFrame([{
                "ID": l["id"],
                "Fecha": l["fecha_compra"],
                "Cantidad Inicial": float(l["cantidad"]),
                "Cantidad Restante": float(l["cantidad_restante"]),
                "Precio Compra (incluye fee)": float(l["precio_unitario"]),
                "Exchange": l.get("exchange", ""),
                "Notas": l.get("notas", "")
            } for l in lotes])
            st.dataframe(df_lotes, width='stretch')
            total_restante = df_lotes["Cantidad Restante"].sum()
            costo_total_restante = sum(df_lotes["Cantidad Restante"] * df_lotes["Precio Compra (incluye fee)"])
            st.metric("Cantidad total remanente", f"{total_restante:.8f}")
            st.metric("Costo promedio ponderado restante", f"${costo_total_restante/total_restante:.4f}" if total_restante>0 else "$0")
        else:
            st.write("No hay lotes para este cliente.")

# ═══════════════════════════════════════
# PAGINA: OPORTUNIDADES
# ═══════════════════════════════════════
elif page == "🎯 Oportunidades":
    st.title("🎯 Pipeline de Oportunidades")
    tab1, tab2 = st.tabs(["📋 Pipeline", "➕ Nueva Oportunidad"])
    with tab1:
        oportunidades = fetch("/oportunidades/?estado=abierta")
        if oportunidades:
            df_opp = pd.DataFrame([{
                "ID": o["id"],
                "Cliente": o.get("cliente_id", ""),
                "Tipo": o.get("tipo", ""),
                "Entrada": float(o.get("precio_entrada", 0)),
                "Objetivo": float(o.get("precio_objetivo", 0)),
                "Stop": float(o.get("precio_stop_loss", 0)),
                "R:R": float(o.get("riesgo_beneficio", 0)),
                "Confianza": o.get("confianza", 3),
                "Estado": o.get("estado", "")
            } for o in oportunidades])
            st.dataframe(df_opp, width='stretch')
    with tab2:
        with st.form("nueva_oportunidad"):
            symbol = st.text_input("Symbol del cliente").upper()
            tipo = st.selectbox("Tipo", ["swing_trade", "scalp", "dca", "breakout", "reversal", "staking"])
            col1, col2, col3 = st.columns(3)
            with col1:
                entrada = st.number_input("Precio entrada", min_value=0.0, step=0.01)
            with col2:
                objetivo = st.number_input("Precio objetivo", min_value=0.0, step=0.01)
            with col3:
                stop = st.number_input("Stop loss", min_value=0.0, step=0.01)
            monto = st.number_input("Monto planificado (USD)", min_value=0.0, step=10.0)
            confianza = st.slider("Confianza (1-5)", 1, 5, 3)
            notas = st.text_area("Analisis")
            if st.form_submit_button("Crear Oportunidad"):
                if symbol and entrada>0 and objetivo>0 and stop>0:
                    result = post("/oportunidades/", {"cliente_symbol": symbol, "tipo": tipo, "precio_entrada": entrada, "precio_objetivo": objetivo, "precio_stop_loss": stop, "monto_planificado": monto, "confianza": confianza, "notas_analisis": notas})
                    if result:
                        st.success("Oportunidad creada!")

# ═══════════════════════════════════════
# PAGINA: TAREAS
# ═══════════════════════════════════════
elif page == "✅ Tareas":
    st.title("✅ Tareas y Alertas")
    tab1, tab2 = st.tabs(["📋 Pendientes", "➕ Nueva Tarea"])
    with tab1:
        tareas = fetch("/tareas/pendientes")
        if tareas:
            for t in tareas:
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"**{t.get('tipo_tarea', '')}** - {t.get('descripcion', '')}")
                    st.caption(f"Limite: {t.get('fecha_limite', '')}")
                with col2:
                    st.badge(f"P{t.get('prioridad', 2)}")
                with col3:
                    if st.button("✅ Completar", key=f"comp_{t['id']}"):
                        requests.post(f"{API_URL}/tareas/{t['id']}/completar")
                        st.rerun()
                st.divider()
        else:
            st.success("No hay tareas pendientes!")
    with tab2:
        with st.form("nueva_tarea"):
            symbol = st.text_input("Symbol").upper()
            tipo = st.selectbox("Tipo", ["revisar_stop", "take_profit", "dca", "actualizar_precio", "revision_estrategia", "rebalancear", "alerta_precio"])
            descripcion = st.text_area("Descripcion")
            dias = st.number_input("Dias", 0,30,1)
            prioridad = st.slider("Prioridad",1,5,2)
            if st.form_submit_button("Crear Tarea"):
                if symbol and descripcion:
                    result = post("/tareas/", {"cliente_symbol": symbol, "tipo_tarea": tipo, "descripcion": descripcion, "prioridad": prioridad})
                    if result:
                        st.success("Tarea creada!")

# ═══════════════════════════════════════
# PAGINA: ANALYTICS
# ═══════════════════════════════════════
elif page == "📈 Analytics":
    st.title("📈 Analytics")
    data = fetch("/dashboard/resumen")
    if data:
        resumen = data.get("resumen", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invertido", f"${resumen.get('total_invertido',0):,.2f}")
        col2.metric("Valor Mercado", f"${resumen.get('total_valor_mercado',0):,.2f}")
        col3.metric("PnL Total", f"${resumen.get('pnl_total',0):,.2f}")
    st.subheader("Distribución del Portafolio")
    distribucion = fetch("/dashboard/resumen").get("distribucion",[]) if data else []
    if distribucion:
        df_dist = pd.DataFrame(distribucion)
        fig = px.pie(df_dist, values="porcentaje", names="symbol", title="Composición Actual")
        st.plotly_chart(fig, width='stretch')

# ═══════════════════════════════════════
# PAGINA: MERCADO EN VIVO
# ═══════════════════════════════════════
elif page == "📡 Mercado en Vivo":
    st.title("📡 Datos Reales de Binance")
    simbolos = ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","PEPE"]
    symbol = st.selectbox("Selecciona", simbolos)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Actualizar Precio"):
            precio = obtener_precio_real(symbol)
            if precio:
                st.metric(f"{symbol}/USDT", f"${precio:,.2f}")
    with col2:
        ticker = obtener_ticker_real(symbol)
        if ticker:
            st.metric("Cambio 24h", f"{ticker.get('percentage',0):.2f}%")
    st.subheader("Velas")
    timeframe = st.selectbox("Timeframe",["1m","5m","15m","30m","1h","4h","1d"], index=4)
    limit = st.slider("Velas",30,200,100)
    velas = obtener_velas(symbol, timeframe, limit)
    if velas:
        df_velas = pd.DataFrame(velas)
        df_velas['timestamp'] = pd.to_datetime(df_velas['timestamp'], unit='ms')
        fig = go.Figure(data=[go.Candlestick(x=df_velas['timestamp'], open=df_velas['open'], high=df_velas['high'], low=df_velas['low'], close=df_velas['close'])])
        st.plotly_chart(fig, width='stretch')
    else:
        st.warning("No se pudieron obtener velas.")

# ═══════════════════════════════════════
# PAGINA: CONFIGURACION
# ═══════════════════════════════════════
elif page == "⚙️ Configuracion":
    st.title("⚙️ Configuracion")
    st.info("Configuración de Exchange y alertas (simulada).")
    with st.form("exchange_config"):
        exchange = st.selectbox("Exchange",["binance","coinbase","kraken","bybit"])
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        st.form_submit_button("Guardar")


================================================================================
  FIN DE ARCHIVO: dashboard/streamlit_app.py
================================================================================
```

---

## ✅ Uso

1. Copia todo el contenido de `codigo_completo_crypto_crm.txt` en un archivo con esa extensión, o simplemente coloca los archivos individuales en su lugar correspondiente.
2. Sigue las instrucciones de instalación del `README.md`.
3. Disfruta de tu CRM Crypto con FIFO, precios reales y todas las funcionalidades.

Si necesitas que ajuste algo más, dímelo.