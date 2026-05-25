# 🪙 Crypto CRM - Tratando Criptomonedas como Clientes

Un sistema completo de gestion de portafolio de criptomonedas construido con la mentalidad de CRM (Customer Relationship Management). Cada moneda es un "cliente" al que le das seguimiento, atencion y estrategia.

## 🎯 Filosofia

> "No operas criptomonedas, gestionas relaciones con activos digitales"

- **Cliente** = Criptomoneda (BTC, ETH, PEPE)
- **Interaccion** = Transaccion (compra, venta, staking)
- **Oportunidad** = Trade setup con entrada, objetivo y stop
- **Tarea** = Alerta o recordatorio de seguimiento

## 🏗️ Arquitectura

```
crypto_crm/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # SQLAlchemy ORM
│   ├── schemas.py           # Pydantic validation
│   ├── services/
│   │   ├── crm_service.py   # Logica de negocio
│   │   ├── exchange_sync.py # CCXT connector
│   │   └── analytics.py     # Metricas y reportes
│   ├── api/
│   │   ├── clientes.py      # CRUD criptomonedas
│   │   ├── interacciones.py # Transacciones
│   │   ├── oportunidades.py # Pipeline trades
│   │   └── tareas.py        # Alertas
│   └── tasks.py             # Celery background jobs
├── dashboard/
│   └── streamlit_app.py     # Interfaz visual
├── config.py
└── requirements.txt
```

## 🚀 Instalacion Rapida

```bash
# 1. Clonar y entrar
cd crypto_crm

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos (se crea automaticamente)
# La DB SQLite se crea en el primer run

# 5. Iniciar API
uvicorn app.main:app --reload --port 8000

# 6. En otra terminal, iniciar dashboard
streamlit run dashboard/streamlit_app.py
```

## 📡 API Endpoints

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/clientes/` | GET | Listar todas las criptomonedas |
| `/clientes/` | POST | Registrar nueva moneda |
| `/clientes/{symbol}` | GET | Detalle de una moneda |
| `/clientes/{symbol}/actualizar-precio` | POST | Actualizar precio de mercado |
| `/interacciones/` | POST | Registrar compra/venta/staking |
| `/interacciones/cliente/{symbol}` | GET | Historial de transacciones |
| `/oportunidades/` | GET/POST | Pipeline de trades |
| `/tareas/` | GET/POST | Tareas y alertas |
| `/dashboard/resumen` | GET | Resumen para el dashboard |

## 💡 Ejemplo de Uso

```python
from app.models import init_db, SessionLocal
from app.services.crm_service import CRMService

# Inicializar
init_db()
db = SessionLocal()
crm = CRMService(db)

# 1. Registrar un nuevo "cliente"
crm.registrar_cliente("BTC", "Bitcoin", "layer1", tags="favorito,hodl")

# 2. Registrar una compra (interaccion)
crm.registrar_interaccion("BTC", "compra", 0.01, 65000, fee=6.5,
                          notas="Compra en soporte semanal")

# 3. Crear oportunidad de venta
crm.crear_oportunidad("BTC", "swing_trade", 65000, 72000, 62000,
                      confianza=4, notas="Target: resistencia historica")

# 4. Crear alerta de seguimiento
crm.crear_tarea("BTC", "revisar_stop", "Revisar si BTC mantiene soporte",
                dias=3, prioridad=2)

# 5. Ver resumen
print(crm.resumen_portafolio())
```

## 🔔 Alertas Inteligentes (Celery)

```bash
# Iniciar worker y scheduler
celery -A app.tasks worker --beat --loglevel=info
```

Alertas automaticas:
- 🔴 **Critico**: Perdida > 20% → Sugiere stop o promediar
- 🟡 **Advertencia**: Concentracion > 30% → Sugiere rebalancear
- 🟢 **Info**: Ganancia > 50% → Sugiere take profit parcial
- 🔵 **Bajo**: Sin movimiento 30+ dias → Sugiere revision

## 📊 Dashboard

El dashboard de Streamlit incluye:
- **KPIs** del portafolio en tiempo real
- **Graficos** de distribucion y top performers
- **Alertas** inteligentes visuales
- **Pipeline** de oportunidades
- **Tareas** pendientes con acciones rapidas

## 🔗 Sincronizacion con Exchanges

```python
from app.services.exchange_sync import ExchangeConnector
from app.services.crm_service import CRMService

# Conectar a Binance
conn = ExchangeConnector("API_KEY", "API_SECRET", "binance")

# Sincronizar portafolio real con CRM
crm = CRMService(db)
conn.sincronizar_portafolio(crm)
```

## 🛡️ Seguridad

- Las API keys de exchange **nunca se almacenan en la DB**
- Usa variables de entorno (`.env`)
- SQLite local por defecto (puedes migrar a PostgreSQL)
- Sin conexion a internet requerida para operacion basica

## 📝 Roadmap

- [x] Modelo CRM completo (Clientes, Interacciones, Oportunidades, Tareas)
- [x] API REST con FastAPI
- [x] Dashboard visual con Streamlit
- [x] Alertas inteligentes
- [x] Conector CCXT para exchanges
- [ ] WebSockets para precios en tiempo real
- [ ] Notificaciones Telegram/Email
- [ ] Backtesting de oportunidades
- [ ] Machine Learning para sentiment scoring

## 📄 Licencia

MIT - Usalo, modificalo, hazlo tuyo.

---

**Construido con ❤️ para traders que piensan como gestores de relaciones.**
