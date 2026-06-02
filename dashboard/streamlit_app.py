"""
Dashboard visual del CRM Crypto usando Streamlit.
Ejecuta: streamlit run dashboard/streamlit_app.py
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import time
from scipy.stats import pearsonr
import numpy as np

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Crypto CRM Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════
# ESTILOS PERSONALIZADOS PARA EL SIDEBAR
# ═══════════════════════════════════════
st.markdown("""
<style>
    /* Fondo del sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1e2a3a 0%, #0f1724 100%);
        border-right: 1px solid #2d3e50;
    }
    /* Título principal */
    [data-testid="stSidebar"] .css-1d391kg {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        border-bottom: 2px solid #ffd700;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Subtítulo */
    [data-testid="stSidebar"] .css-1wivap2 {
        color: #b0c4de;
        font-size: 0.9rem;
        text-align: center;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
    }
    /* Opciones del radio */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 8px 12px;
        margin: 4px 0;
        transition: all 0.2s ease;
        color: #e0e0e0;
        font-weight: 500;
        font-size: 1rem;
    }
    /* Hover sobre opciones */
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255,215,0,0.2);
        color: #ffd700;
        transform: translateX(5px);
    }
    /* Opción seleccionada */
    [data-testid="stSidebar"] div[role="radiogroup"] label[data-testid="stMarkdownContainer"]:has(input:checked) {
        background-color: #ffd700;
        color: #0f1724;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(255,215,0,0.3);
    }
    /* Radio circle oculto (personalizamos con background) */
    [data-testid="stSidebar"] div[role="radiogroup"] input {
        accent-color: #ffd700;
    }
    /* Checkbox de actualización automática */
    [data-testid="stSidebar"] .stCheckbox {
        background: #2d3e50;
        padding: 6px 12px;
        border-radius: 20px;
        margin: 10px 0;
        color: white;
    }
    /* Selectbox dentro del sidebar */
    [data-testid="stSidebar"] .stSelectbox {
        background: #2d3e50;
        border-radius: 8px;
    }
    /* Info box */
    [data-testid="stSidebar"] .stAlert {
        background: #2d3e50;
        border-left: 4px solid #ffd700;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
st.sidebar.title("🪙 Crypto CRM")
st.sidebar.markdown("*Tratando criptomonedas como clientes*")

# Control de actualización automática
st.sidebar.subheader("⚡ Actualización automática")
auto_refresh = st.sidebar.checkbox("🔄 Activar actualización automática", value=False)
if auto_refresh:
    interval = st.sidebar.selectbox("⏱️ Intervalo (segundos)", [5, 10, 30, 60], index=1)
    st_autorefresh(interval=interval * 1000, key="auto_refresh")
else:
    st.sidebar.info("Desactivado. Usa los botones 'Actualizar' en cada sección.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navegación")

page = st.sidebar.radio("Navegación", [
    "🏠 Dashboard",
    "👥 Clientes",
    "💱 Interacciones",
    "🎯 Oportunidades",
    "✅ Tareas",
    "📦 Lotes FIFO",
    "📈 Analytics",
    "📡 Mercado en Vivo",
    "🔥 Tendencias de Mercado",
    "📢 Eventos Binance",
    "📈 Análisis y Trading",
    "⚙️ Configuracion"
], label_visibility="hidden")

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
# FUNCIONES PARA ANÁLISIS TÉCNICO (mejoradas)
# ═══════════════════════════════════════
def obtener_velas_binance(symbol, interval="1h", limit=168):
    """
    Obtiene velas OHLCV desde Binance directamente.
    Por defecto: 168 velas = 7 días a 1 hora.
    """
    try:
        # Aseguramos el símbolo con USDT
        pair = f"{symbol.upper()}USDT"
        # Mapeo de intervalos soportados por Binance
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
        }
        binance_interval = interval_map.get(interval, "1h")
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={binance_interval}&limit={limit}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            ohlcv = []
            for candle in data:
                ohlcv.append({
                    "timestamp": candle[0],
                    "datetime": datetime.fromtimestamp(candle[0]/1000).isoformat(),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5])
                })
            return ohlcv
        else:
            st.error(f"Error {r.status_code} de Binance: {r.text[:100]}")
            return None
    except Exception as e:
        st.error(f"Error al conectar con Binance: {e}")
        return None

def encontrar_soportes_resistencias(velas, num_niveles=3):
    """Encuentra soportes (mínimos locales) y resistencias (máximos locales)."""
    highs = [v["high"] for v in velas]
    lows = [v["low"] for v in velas]
    window = 5
    soportes = []
    resistencias = []
    for i in range(window, len(lows) - window):
        # Mínimo local (soporte)
        if all(lows[i] <= lows[i - j] for j in range(1, window+1)) and all(lows[i] <= lows[i + j] for j in range(1, window+1)):
            soportes.append(lows[i])
        # Máximo local (resistencia)
        if all(highs[i] >= highs[i - j] for j in range(1, window+1)) and all(highs[i] >= highs[i + j] for j in range(1, window+1)):
            resistencias.append(highs[i])
    soportes = sorted(list(set(soportes)), reverse=False)
    resistencias = sorted(list(set(resistencias)), reverse=True)
    precio_actual = velas[-1]["close"]
    # Soportes cercanos por debajo
    soportes_cercanos = [s for s in soportes if s < precio_actual][-num_niveles:]
    if len(soportes_cercanos) < num_niveles:
        soportes_cercanos = soportes[-num_niveles:] if soportes else []
    # Resistencias cercanas por encima
    resistencias_cercanas = [r for r in resistencias if r > precio_actual][:num_niveles]
    if len(resistencias_cercanas) < num_niveles:
        resistencias_cercanas = resistencias[:num_niveles] if resistencias else []
    return soportes_cercanos[:num_niveles], resistencias_cercanas[:num_niveles]

# Categorías actualizadas (Binance)
CATEGORIAS = [
    "BNB Chain", "Solana", "RWA", "MEME", "Pagos", "IA",
    "Capa 1/Capa 2", "Fase semilla", "Launchpool", "New", "Megadrop",
    "Juegos", "DeFi", "En observación", "Fan Token", "Infraestructura",
    "Almacenamiento", "NFT", "Launchpad", "Yzi", "desconocida"
]

# ═══════════════════════════════════════
# PAGINA: DASHBOARD
# ═══════════════════════════════════════
if page == "🏠 Dashboard":
    st.title("📊 Dashboard Principal")
    
    if st.button("🔄 Actualizar precios ahora (Binance)"):
        with st.spinner("Actualizando precios de todos los clientes..."):
            clientes = fetch("/clientes/")
            if clientes:
                for c in clientes:
                    precio_real = obtener_precio_real(c["symbol"])
                    if precio_real > 0:
                        post(f"/clientes/{c['symbol']}/actualizar-precio", {"precio": precio_real})
                st.success("Precios actualizados")
                st.rerun()
    
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
        
        st.subheader("📈 Evolución de PnL Realizado (Últimos 7 días)")
        daily_pnl_data = fetch("/analytics/daily-pnl?days=7")
        if daily_pnl_data:
            df_pnl = pd.DataFrame(daily_pnl_data)
            if not df_pnl.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_pnl["date"],
                    y=df_pnl["pnl"],
                    marker_color=['green' if val >= 0 else 'red' for val in df_pnl["pnl"]],
                    text=df_pnl["pnl"].apply(lambda x: f"${x:.2f}"),
                    textposition='auto'
                ))
                fig.update_layout(title="PnL Realizado por Día", xaxis_title="Fecha", yaxis_title="PnL (USD)", height=400)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No hay datos de PnL para los últimos 7 días.")
        else:
            st.info("No se pudieron cargar los datos de PnL diario.")

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

    if st.button("🔄 Actualizar todos los precios desde Binance"):
        with st.spinner("Actualizando precios..."):
            clientes_actualizar = fetch("/clientes/")
            if clientes_actualizar:
                for c in clientes_actualizar:
                    precio_real = obtener_precio_real(c["symbol"])
                    if precio_real > 0:
                        post(f"/clientes/{c['symbol']}/actualizar-precio", {"precio": precio_real})
                st.success("Precios actualizados")
                st.rerun()

    clientes = fetch("/clientes/")
    if not clientes:
        st.warning("No hay clientes registrados. Crea uno nuevo en la pestaña '➕ Nuevo Cliente'")
        clientes = []

    if clientes:
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
            "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
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
            categoria = st.selectbox("Categoria", CATEGORIAS)
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
# PAGINA: OPORTUNIDADES
# ═══════════════════════════════════════
elif page == "🎯 Oportunidades":
    st.title("🎯 Pipeline de Oportunidades")
    
    clientes_lista = fetch("/clientes/")
    simbolos_clientes = [c["symbol"] for c in clientes_lista] if clientes_lista else []
    
    with st.expander("➕ Nueva Oportunidad", expanded=True):
        with st.form("nueva_oportunidad"):
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Symbol del cliente").upper()
                tipo = st.selectbox("Tipo de oportunidad", [
                    "swing_trade", "scalp", "dca", "staking", "breakout", "reversal"
                ])
                entrada = st.number_input("Precio entrada (USD)", min_value=0.0, step=0.01)
                objetivo = st.number_input("Precio objetivo (USD)", min_value=0.0, step=0.01)
            with col2:
                stop = st.number_input("Stop loss (USD)", min_value=0.0, step=0.01)
                monto = st.number_input("Monto planificado (USD)", min_value=0.0, step=10.0)
                confianza = st.slider("Confianza (1-5)", 1, 5, 3)
                notas = st.text_area("Analisis y notas")
            submitted = st.form_submit_button("Crear Oportunidad")
            if submitted:
                if not symbol:
                    st.error("Debes ingresar un símbolo de cliente")
                elif symbol not in simbolos_clientes:
                    st.error(f"El cliente '{symbol}' no existe. Regístralo primero en la sección Clientes.")
                elif entrada <= 0 or objetivo <= 0 or stop <= 0:
                    st.error("Los precios de entrada, objetivo y stop deben ser mayores que cero.")
                else:
                    with st.spinner("Creando oportunidad..."):
                        result = post("/oportunidades/", {
                            "cliente_symbol": symbol,
                            "tipo": tipo,
                            "precio_entrada": entrada,
                            "precio_objetivo": objetivo,
                            "precio_stop_loss": stop,
                            "monto_planificado": monto,
                            "confianza": confianza,
                            "notas_analisis": notas
                        })
                        if result:
                            st.success("Oportunidad creada exitosamente!")
                            st.rerun()
                        else:
                            st.error("No se pudo crear la oportunidad. Revisa que los datos sean correctos.")
    
    st.subheader("📋 Oportunidades Abiertas")
    if st.button("Refrescar lista"):
        st.rerun()
    
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
            "Fecha Creación": o.get("fecha_creacion", "")[:16] if o.get("fecha_creacion") else "",
            "Notas": o.get("notas_analisis", "")[:50]
        } for o in oportunidades])
        st.dataframe(df_opp, width='stretch')
        
        st.subheader("Cerrar Oportunidad")
        col_opp, col_estado, col_pnl, col_btn = st.columns([2,2,2,1])
        with col_opp:
            opp_id = st.selectbox("Seleccionar oportunidad", [o["id"] for o in oportunidades])
        with col_estado:
            nuevo_estado = st.selectbox("Nuevo estado", ["ejecutada", "cancelada"])
        with col_pnl:
            pnl_realizado = st.number_input("PnL realizado (USD)", value=0.0, step=0.01)
        with col_btn:
            if st.button("Cerrar"):
                resp = requests.post(f"{API_URL}/oportunidades/{opp_id}/cerrar", params={"estado": nuevo_estado, "pnl": pnl_realizado})
                if resp.status_code == 200:
                    st.success("Oportunidad cerrada")
                    st.rerun()
                else:
                    st.error(f"Error al cerrar: {resp.text}")
    else:
        st.info("No hay oportunidades abiertas. Crea una nueva usando el formulario de arriba.")

# ═══════════════════════════════════════
# PAGINA: TAREAS
# ═══════════════════════════════════════
elif page == "✅ Tareas":
    st.title("✅ Tareas y Alertas")
    
    clientes_lista = fetch("/clientes/")
    simbolos_clientes = [c["symbol"] for c in clientes_lista] if clientes_lista else []
    
    with st.expander("➕ Nueva Tarea", expanded=True):
        with st.form("nueva_tarea"):
            symbol = st.text_input("Symbol del cliente").upper()
            tipo = st.selectbox("Tipo de tarea", [
                "revisar_stop", "take_profit", "dca", "actualizar_precio",
                "revision_estrategia", "rebalancear", "alerta_precio"
            ])
            descripcion = st.text_area("Descripcion")
            dias = st.number_input("Días para completar", min_value=0, max_value=30, value=1)
            prioridad = st.slider("Prioridad (1=alta, 5=baja)", 1, 5, 2)
            submitted = st.form_submit_button("Crear Tarea")
            if submitted:
                if not symbol:
                    st.error("Debes ingresar un símbolo de cliente")
                elif symbol not in simbolos_clientes:
                    st.error(f"El cliente '{symbol}' no existe. Regístralo primero en la sección Clientes.")
                elif not descripcion:
                    st.error("La descripción es obligatoria")
                else:
                    with st.spinner("Creando tarea..."):
                        result = post("/tareas/", {
                            "cliente_symbol": symbol,
                            "tipo_tarea": tipo,
                            "descripcion": descripcion,
                            "prioridad": prioridad
                        })
                        if result:
                            st.success("Tarea creada exitosamente!")
                            st.rerun()
                        else:
                            st.error("No se pudo crear la tarea. Revisa los datos.")
    
    st.subheader("📋 Tareas Pendientes")
    if st.button("Refrescar lista"):
        st.rerun()
    
    tareas_pendientes = fetch("/tareas/pendientes")
    if tareas_pendientes:
        for t in tareas_pendientes:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{t.get('tipo_tarea', '')}** - {t.get('descripcion', '')}")
                    cliente_id = t.get('cliente_id')
                    if cliente_id:
                        st.caption(f"Cliente ID: {cliente_id} | Límite: {t.get('fecha_limite', '')}")
                    else:
                        st.caption(f"Límite: {t.get('fecha_limite', '')}")
                    if t.get('fecha_limite'):
                        fecha_limite = datetime.fromisoformat(t['fecha_limite'].replace('Z', '+00:00'))
                        if fecha_limite < datetime.now():
                            st.markdown("⚠️ **VENCIDA**")
                with col2:
                    prioridad = t.get('prioridad', 2)
                    color = "🟢" if prioridad <= 2 else "🟡" if prioridad <= 4 else "🔴"
                    st.write(f"{color} Prioridad {prioridad}")
                with col3:
                    if st.button("✅ Completar", key=f"comp_{t['id']}"):
                        requests.post(f"{API_URL}/tareas/{t['id']}/completar")
                        st.success("Tarea completada")
                        st.rerun()
                st.divider()
    else:
        st.success("No hay tareas pendientes. ¡Todo al día! 🎉")
    
    with st.expander("Ver tareas completadas (últimas 10)"):
        st.info("Funcionalidad en desarrollo: próximamente podrás ver el historial de tareas completadas.")

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
# PAGINA: ANALYTICS
# ═══════════════════════════════════════
elif page == "📈 Analytics":
    st.title("📈 Analytics y Reportes")
    
    st.subheader("🔥 Heatmap: Rendimiento por Categoría (ROI %)")
    perf_data = fetch("/analytics/performance-by-category")
    if perf_data:
        df_perf = pd.DataFrame(perf_data)
        if not df_perf.empty:
            df_perf = df_perf.sort_values("roi_promedio", ascending=False)
            fig = px.imshow(
                df_perf[["roi_promedio"]].values.T,
                x=df_perf["categoria"],
                y=["ROI Promedio %"],
                color_continuous_scale="RdYlGn",
                text_auto=True,
                aspect="auto",
                title="ROI Promedio por Categoría"
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=300, width=800)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No hay datos de categorías aún. Registra clientes con categorías.")
    else:
        st.info("No se pudieron cargar los datos de rendimiento por categoría.")
    
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
    
    st.subheader("Evolución de PnL Realizado (Últimos 7 días)")
    daily_pnl_data = fetch("/analytics/daily-pnl?days=7")
    if daily_pnl_data:
        df_pnl = pd.DataFrame(daily_pnl_data)
        if not df_pnl.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_pnl["date"],
                y=df_pnl["pnl"],
                marker_color=['green' if val >= 0 else 'red' for val in df_pnl["pnl"]],
                text=df_pnl["pnl"].apply(lambda x: f"${x:.2f}"),
                textposition='auto'
            ))
            fig.update_layout(title="PnL Realizado por Día", xaxis_title="Fecha", yaxis_title="PnL (USD)")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No hay datos de PnL para los últimos 7 días.")
    else:
        st.info("No se pudieron cargar los datos de PnL diario.")

# ═══════════════════════════════════════
# PAGINA: MERCADO EN VIVO
# ═══════════════════════════════════════
elif page == "📡 Mercado en Vivo":
    st.title("📡 Datos Reales de Binance")
    st.markdown("Tendencias y sentimiento del mercado en tiempo real")
    
    simbolos = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "PEPE"]
    symbol = st.selectbox("Selecciona una criptomoneda", simbolos, index=0)
    
    ticker = obtener_ticker_real(symbol)
    if ticker:
        cambio_pct = ticker.get("percentage", 0.0)
        precio_actual = ticker.get("last", 0)
        
        if cambio_pct > 0.5:
            arrow = "🔼"
            tendencia = "Alcista fuerte"
        elif cambio_pct > 0:
            arrow = "↗️"
            tendencia = "Ligeramente alcista"
        elif cambio_pct < -0.5:
            arrow = "🔽"
            tendencia = "Bajista fuerte"
        elif cambio_pct < 0:
            arrow = "↘️"
            tendencia = "Ligeramente bajista"
        else:
            arrow = "⏸️"
            tendencia = "Neutral"
        
        if cambio_pct > 3:
            sentimiento = "🟢 Muy alcista / Euforia"
        elif cambio_pct > 1:
            sentimiento = "🟢 Alcista / Confianza"
        elif cambio_pct > 0.2:
            sentimiento = "🟢 Ligeramente alcista"
        elif cambio_pct > -0.2:
            sentimiento = "⚪ Neutral / Lateral"
        elif cambio_pct > -1:
            sentimiento = "🔴 Ligeramente bajista"
        elif cambio_pct > -3:
            sentimiento = "🔴 Bajista / Preocupación"
        else:
            sentimiento = "🔴 Muy bajista / Pánico"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"{symbol}/USDT", f"${precio_actual:,.4f}", delta=f"{cambio_pct:.2f}%")
        with col2:
            st.markdown(f"### Tendencia: {arrow} {tendencia}")
        with col3:
            st.markdown(f"### Sentimiento: {sentimiento}")
        
        st.divider()
        
        st.subheader("Detalles del Ticker")
        detalle_col1, detalle_col2 = st.columns(2)
        with detalle_col1:
            st.metric("Máximo 24h", f"${ticker.get('high', 0):,.4f}")
            st.metric("Mínimo 24h", f"${ticker.get('low', 0):,.4f}")
            st.metric("Volumen (24h)", f"{ticker.get('volume', 0):,.2f}")
        with detalle_col2:
            st.metric("Ask", f"${ticker.get('ask', 0):,.4f}")
            st.metric("Bid", f"${ticker.get('bid', 0):,.4f}")
            st.metric("Última actualización", ticker.get('timestamp', '')[:19])
        
        st.subheader("Gráfico de Velas (OHLCV)")
        timeframe = st.selectbox("Timeframe", ["1m","5m","15m","30m","1h","4h","1d"], index=4)
        limit = st.slider("Cantidad de velas", 30, 200, 100)
        velas = obtener_velas(symbol, timeframe, limit)
        if velas:
            df_velas = pd.DataFrame(velas)
            df_velas['timestamp'] = pd.to_datetime(df_velas['timestamp'], unit='ms')
            fig = go.Figure(data=[go.Candlestick(
                x=df_velas['timestamp'],
                open=df_velas['open'],
                high=df_velas['high'],
                low=df_velas['low'],
                close=df_velas['close']
            )])
            fig.update_layout(title=f"{symbol}/USDT - Velas {timeframe}", xaxis_title="Fecha", yaxis_title="Precio USD")
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("No se pudieron obtener velas para este símbolo.")
    else:
        st.error("No se pudo obtener información del ticker. Intenta con otro símbolo.")

# ═══════════════════════════════════════
# PAGINA: TENDENCIAS DE MERCADO (CoinGecko)
# ═══════════════════════════════════════
elif page == "🔥 Tendencias de Mercado":
    st.title("🔥 Tendencias de Mercado (CoinGecko)")
    st.markdown("Criptomonedas más buscadas y con mayor tendencia actualmente.")
    
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Cargando datos de tendencias, Binance y correlaciones..."):
        binance_symbols = obtener_simbolos_binance()
        tendencias = obtener_tendencias_coingecko()
        
        if tendencias:
            df_list = []
            progress_bar = st.progress(0)
            for i, token in enumerate(tendencias):
                token_id = token["id"]
                symbol = token["symbol"]
                name = token["name"]
                score = token["score"]
                market_rank = token["market_cap_rank"]
                thumb = token["thumb"]
                
                in_binance = f"{symbol}USDT" in binance_symbols
                price_data = obtener_precio_actual_coingecko(token_id)
                change_24h = price_data["change_24h"]
                
                if change_24h > 1:
                    trend_icon = "🟢"
                    trend_text = "Alcista fuerte"
                elif change_24h > 0:
                    trend_icon = "🟢"
                    trend_text = "Alcista"
                elif change_24h > -1:
                    trend_icon = "🔴"
                    trend_text = "Bajista"
                else:
                    trend_icon = "🔴"
                    trend_text = "Bajista fuerte"
                
                correlation = None
                if symbol != "BTC" and token_id:
                    token_prices = obtener_historicos_coingecko(token_id, days=7)
                    btc_prices = obtener_historicos_coingecko("bitcoin", days=7)
                    if token_prices and btc_prices:
                        min_len = min(len(token_prices), len(btc_prices))
                        if min_len >= 3:
                            corr = calcular_correlacion_con_btc(token_prices[:min_len], btc_prices[:min_len])
                            if corr is not None:
                                if corr > 0.5:
                                    correlation = f"🟢 Positiva ({corr:.2f})"
                                elif corr < -0.5:
                                    correlation = f"🔴 Negativa ({corr:.2f})"
                                else:
                                    correlation = f"⚪ Neutra ({corr:.2f})"
                            else:
                                correlation = "⚪ No disponible"
                        else:
                            correlation = "⚪ Datos insuficientes"
                    else:
                        correlation = "⚪ Sin datos"
                elif symbol == "BTC":
                    correlation = "⚪ Referencia"
                
                df_list.append({
                    "Token": symbol,
                    "Nombre": name,
                    "Score": score,
                    "Market Cap Rank": market_rank,
                    "En Binance": "✅" if in_binance else "❌",
                    "Cambio 24h (%)": round(change_24h, 2),
                    "Tendencia": f"{trend_icon} {trend_text}",
                    "Correlación BTC": correlation,
                    "Logo": thumb,
                    "ID": token_id
                })
                progress_bar.progress((i + 1) / len(tendencias))
            
            df_trend = pd.DataFrame(df_list)
            if not df_trend.empty:
                display_cols = ["Token", "Nombre", "Score", "Market Cap Rank", "En Binance", "Cambio 24h (%)", "Tendencia", "Correlación BTC"]
                st.dataframe(df_trend[display_cols], width='stretch')
                
                fig = px.bar(df_trend, x="Token", y="Score", color="Score",
                             color_continuous_scale="Blues", title="Score de Tendencia")
                st.plotly_chart(fig, width='stretch')
                
                fig2 = go.Figure()
                colors = ['green' if x > 0 else 'red' for x in df_trend["Cambio 24h (%)"]]
                fig2.add_trace(go.Bar(
                    x=df_trend["Token"],
                    y=df_trend["Cambio 24h (%)"],
                    marker_color=colors,
                    text=df_trend["Cambio 24h (%)"].apply(lambda x: f"{x:.2f}%"),
                    textposition='auto'
                ))
                fig2.update_layout(title="Variación 24h por Token", xaxis_title="Token", yaxis_title="Cambio (%)")
                st.plotly_chart(fig2, width='stretch')
                
                st.subheader("🖼️ Logos de tokens en tendencia")
                cols = st.columns(5)
                for i, row in df_trend.head(10).iterrows():
                    with cols[i % 5]:
                        if row["Logo"]:
                            st.image(row["Logo"], caption=row["Token"], width=60)
                
                binance_count = df_trend[df_trend["En Binance"] == "✅"].shape[0]
                st.info(f"De los {len(df_trend)} tokens en tendencia, **{binance_count}** cotizan actualmente en Binance (par USDT).")
            else:
                st.info("No se encontraron datos de tendencias.")
        else:
            st.error("No se pudieron obtener datos de tendencias. Intenta más tarde.")

# ═══════════════════════════════════════
# PAGINA: EVENTOS BINANCE
# ═══════════════════════════════════════
elif page == "📢 Eventos Binance":
    st.title("📢 Eventos Binance - Launchpool, Megadrop y Nuevos Listados")
    st.markdown("Eventos recientes extraídos de la página oficial de anuncios de Binance.")
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.info("🔍 Los eventos se obtienen mediante web scraping de la página de anuncios de Binance.")
    with col2:
        if st.button("🔄 Forzar actualización ahora", type="primary"):
            with st.spinner("Actualizando eventos desde Binance..."):
                try:
                    r = requests.post(f"{API_URL}/binance-events/update", timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        st.success(data.get("message", "Actualización completada."))
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text[:200]}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
    
    eventos = fetch("/binance-events?limit=30")
    if eventos is None:
        st.error("No se pudo conectar a la API. Asegúrate de que FastAPI esté corriendo en el puerto 8000.")
    elif isinstance(eventos, list):
        if len(eventos) > 0:
            df_events = pd.DataFrame(eventos)
            if "detected_at" in df_events.columns:
                df_events["detected_at"] = pd.to_datetime(df_events["detected_at"]).dt.strftime("%Y-%m-%d %H:%M")
            if "event_date" in df_events.columns:
                df_events["event_date"] = pd.to_datetime(df_events["event_date"]).dt.strftime("%Y-%m-%d") if df_events["event_date"].notna().any() else None
            
            st.subheader("📋 Últimos eventos detectados")
            display_cols = ["title", "event_type", "detected_at", "url"]
            st.dataframe(df_events[display_cols], width='stretch')
            
            st.subheader("🔍 Detalle de eventos")
            for idx, row in df_events.iterrows():
                with st.expander(f"📌 {row['title'][:100]}"):
                    st.markdown(f"**Tipo:** {row['event_type']}")
                    st.markdown(f"**Detectado:** {row['detected_at']}")
                    if row.get('event_date') and row['event_date'] != "None":
                        st.markdown(f"**Fecha del evento:** {row['event_date']}")
                    if row.get('url') and row['url'] != "None":
                        st.markdown(f"**Enlace:** [Ver anuncio]({row['url']})")
                    if row.get('description'):
                        st.markdown(f"**Descripción:** {row['description']}")
        else:
            st.warning("No se encontraron eventos reales en este momento. Es posible que Binance haya cambiado la estructura de su página o que no haya novedades recientes. Intenta más tarde.")
    else:
        st.error("La respuesta de la API no tiene el formato esperado.")
    
    with st.expander("ℹ️ ¿Cómo funciona?"):
        st.markdown("""
        - El sistema extrae anuncios de la página oficial de Binance.
        - Si no se detectan eventos reales (por cambios en la web o bloqueo), se mostrará un mensaje informativo.
        - Puedes forzar la actualización manual en cualquier momento.
        - **No se utilizan datos ficticios.** Solo eventos auténticos.
        """)

# ═══════════════════════════════════════
# NUEVA PAGINA: ANÁLISIS Y TRADING (corregida)
# ═══════════════════════════════════════
elif page == "📈 Análisis y Trading":
    st.title("📈 Análisis Técnico e Historial de Trading")
    
    # Crear pestañas dentro de la página
    tab_analisis, tab_historial = st.tabs(["📊 Análisis Técnico", "📜 Historial de Transacciones"])
    
    # ========== PESTAÑA 1: ANÁLISIS TÉCNICO (fijo a 1 semana, sin selector de timeframe) ==========
    with tab_analisis:
        st.subheader("Análisis de Soportes y Resistencias (Última Semana)")
        symbol_analisis = st.text_input("Símbolo de la moneda (ej: BTC, ETH, XRP)", value="BTC", key="analisis_symbol").upper()
        
        if st.button("Generar Análisis", key="analisis_btn"):
            if not symbol_analisis:
                st.error("Ingresa un símbolo de moneda válido")
            else:
                with st.spinner(f"Obteniendo datos de {symbol_analisis} desde Binance (última semana)..."):
                    # Usamos intervalo fijo: 1 hora, 168 velas = 7 días
                    velas = obtener_velas_binance(symbol_analisis, interval="1h", limit=168)
                    if velas and len(velas) >= 10:
                        # Encontrar soportes y resistencias
                        soportes, resistencias = encontrar_soportes_resistencias(velas, num_niveles=3)
                        
                        # Crear gráfico de velas con líneas horizontales
                        df_velas = pd.DataFrame(velas)
                        df_velas['timestamp'] = pd.to_datetime(df_velas['timestamp'], unit='ms')
                        
                        fig = go.Figure()
                        # Candlestick
                        fig.add_trace(go.Candlestick(
                            x=df_velas['timestamp'],
                            open=df_velas['open'],
                            high=df_velas['high'],
                            low=df_velas['low'],
                            close=df_velas['close'],
                            name='Precio'
                        ))
                        # Líneas de soporte (verde)
                        for i, s in enumerate(soportes):
                            fig.add_hline(y=s, line_dash="dash", line_color="green", 
                                          annotation_text=f"Soporte {i+1} (${s:.2f})", 
                                          annotation_position="bottom right")
                        # Líneas de resistencia (rojo)
                        for i, r in enumerate(resistencias):
                            fig.add_hline(y=r, line_dash="dash", line_color="red", 
                                          annotation_text=f"Resistencia {i+1} (${r:.2f})", 
                                          annotation_position="top right")
                        
                        fig.update_layout(
                            title=f"{symbol_analisis}/USDT - Velas cada hora (Última semana)",
                            xaxis_title="Fecha",
                            yaxis_title="Precio (USD)",
                            height=600,
                            template="plotly_dark"
                        )
                        st.plotly_chart(fig, width='stretch')
                        
                        # Mostrar tabla de niveles
                        col_s, col_r = st.columns(2)
                        with col_s:
                            st.subheader("📉 Soportes detectados")
                            if soportes:
                                st.write(pd.DataFrame({"Soporte (USD)": [f"${s:.2f}" for s in soportes]}))
                            else:
                                st.info("No se detectaron soportes claros en el período.")
                        with col_r:
                            st.subheader("📈 Resistencias detectadas")
                            if resistencias:
                                st.write(pd.DataFrame({"Resistencia (USD)": [f"${r:.2f}" for r in resistencias]}))
                            else:
                                st.info("No se detectaron resistencias claras en el período.")
                    else:
                        st.error(f"No se pudieron obtener datos de {symbol_analisis}. Verifica el símbolo o inténtalo más tarde.")
    
    # ========== PESTAÑA 2: HISTORIAL DE TRANSACCIONES (sin cambios) ==========
    with tab_historial:
        st.subheader("Todas las compras y ventas registradas")
        
        with st.spinner("Cargando historial de transacciones..."):
            clientes_list = fetch("/clientes/")
            if clientes_list:
                all_transactions = []
                for cliente in clientes_list:
                    symbol = cliente["symbol"]
                    interacciones = fetch(f"/interacciones/cliente/{symbol}")
                    if interacciones:
                        for t in interacciones:
                            if t["tipo"] in ["compra", "venta"]:
                                all_transactions.append({
                                    "Moneda": symbol,
                                    "Tipo": t["tipo"].upper(),
                                    "Cantidad": float(t["cantidad"]),
                                    "Precio Unitario (USD)": float(t["precio_unitario"]),
                                    "Monto (USD)": float(t["monto_usd"]),
                                    "Fee (USD)": float(t["fee"]),
                                    "Fecha": t["timestamp"][:16] if t["timestamp"] else "",
                                    "PnL Realizado (USD)": float(t["pnl_realizado"]) if t["tipo"] == "venta" else 0
                                })
                if all_transactions:
                    df_hist = pd.DataFrame(all_transactions)
                    df_hist = df_hist.sort_values("Fecha", ascending=False)
                    st.dataframe(df_hist, width='stretch')
                    
                    # Resumen
                    total_comprado = df_hist[df_hist["Tipo"] == "COMPRA"]["Monto (USD)"].sum()
                    total_vendido = df_hist[df_hist["Tipo"] == "VENTA"]["Monto (USD)"].sum()
                    total_pnl = df_hist["PnL Realizado (USD)"].sum()
                    total_fees = df_hist["Fee (USD)"].sum()
                    
                    st.subheader("📊 Resumen")
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Total Comprado", f"${total_comprado:,.2f}")
                    col_b.metric("Total Vendido", f"${total_vendido:,.2f}")
                    col_c.metric("Total PnL Realizado", f"${total_pnl:,.2f}", delta_color="normal")
                    col_d.metric("Total Comisiones", f"${total_fees:,.2f}")
                else:
                    st.info("No hay transacciones de compra/venta registradas todavía.")
            else:
                st.info("No hay clientes registrados aún.")

# ═══════════════════════════════════════
# PAGINA: CONFIGURACION
# ═══════════════════════════════════════
elif page == "⚙️ Configuracion":
    st.title("⚙️ Configuracion")
    st.info("Configuración de Exchange y alertas (simulada).")
    with st.form("exchange_config"):
        exchange = st.selectbox("Exchange", ["binance", "coinbase", "kraken", "bybit"])
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        st.form_submit_button("Guardar")