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
import time

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
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def obtener_precio_real(symbol):
    """Obtiene precio actual desde Binance vía nuestra API"""
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
                fig = px.pie(df_dist, values="porcentaje", names="symbol", 
                            hole=0.4, title="Por Valor de Mercado")
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Top Performers")
            if top:
                df_top = pd.DataFrame(top)
                fig = px.bar(df_top, x="symbol", y="roi", 
                           color="roi", color_continuous_scale="RdYlGn",
                           title="ROI por Moneda")
                st.plotly_chart(fig, use_container_width=True)

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
# PAGINA: CLIENTES (igual que antes, pero añadimos botón para actualizar precio desde Binance)
# ═══════════════════════════════════════
elif page == "👥 Clientes":
    st.title("👥 Gestion de Clientes (Criptomonedas)")

    tab1, tab2 = st.tabs(["📋 Listado", "➕ Nuevo Cliente"])

    with tab1:
        clientes = fetch("/clientes/")
        if clientes:
            df = pd.DataFrame([{
                "Symbol": c["symbol"],
                "Nombre": c.get("nombre", ""),
                "Categoria": c.get("categoria", ""),
                "Estado": c.get("estado", ""),
                "Cantidad": float(c.get("cantidad_total", 0)),
                "Costo Prom": float(c.get("costo_promedio", 0)),
                "Precio": float(c.get("precio_actual", 0)),
                "Valor": float(c.get("valor_mercado", 0)),
                "PnL": float(c.get("pnl_total", 0)),
                "ROI%": float(c.get("roi_porcentaje", 0)),
                "Prioridad": c.get("prioridad", 3),
                "Tags": c.get("tags", "")
            } for c in clientes])

            estado_filter = st.multiselect("Filtrar por estado", 
                df["Estado"].unique().tolist(), default=[])
            if estado_filter:
                df = df[df["Estado"].isin(estado_filter)]

            st.dataframe(df, use_container_width=True, hide_index=True)

            selected = st.selectbox("Ver detalle de", [c["symbol"] for c in clientes])
            if selected:
                cliente = fetch(f"/clientes/{selected}")
                if cliente:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("ROI", f"{float(cliente.get('roi_porcentaje', 0)):.2f}%")
                        st.metric("PnL", f"${float(cliente.get('pnl_total', 0)):,.2f}")
                    with c2:
                        st.metric("Valor Mercado", f"${float(cliente.get('valor_mercado', 0)):,.2f}")
                        st.metric("Inversion", f"${float(cliente.get('inversion_total', 0)):,.2f}")

                    # Botón para actualizar precio desde Binance
                    if st.button(f"Actualizar precio de {selected} desde Binance"):
                        precio_real = obtener_precio_real(selected)
                        if precio_real > 0:
                            # Llamar a nuestro endpoint de actualización
                            r = requests.post(f"{API_URL}/clientes/{selected}/actualizar-precio", json={"precio": precio_real})
                            if r.status_code == 200:
                                st.success(f"Precio de {selected} actualizado a ${precio_real}")
                                st.rerun()
                            else:
                                st.error("Error al actualizar precio")
                        else:
                            st.error("No se pudo obtener precio de Binance")

                    st.text_area("Notas personales", 
                               value=cliente.get("notas_personal", ""), 
                               key=f"notas_{selected}",
                               disabled=True)

    with tab2:
        with st.form("nuevo_cliente"):
            symbol = st.text_input("Symbol (ej: BTC, ETH)").upper()
            nombre = st.text_input("Nombre completo (opcional)")
            categoria = st.selectbox("Categoria", [
                "layer1", "layer2", "defi", "meme", "stablecoin", 
                "nft", "gaming", "ai", "infra", "desconocida"
            ])
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

# ═══════════════════════════════════════
# PAGINA: INTERACCIONES (sin cambios)
# ═══════════════════════════════════════
elif page == "💱 Interacciones":
    st.title("💱 Registro de Interacciones")

    with st.form("nueva_interaccion"):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Symbol del cliente").upper()
        with col2:
            tipo = st.selectbox("Tipo", ["compra", "venta", "staking", "unstaking", "dividendo", "airdrop"])
        with col3:
            exchange = st.text_input("Exchange", value="binance")

        col4, col5, col6 = st.columns(3)
        with col4:
            cantidad = st.number_input("Cantidad", min_value=0.0, step=0.0001, format="%.8f")
        with col5:
            precio = st.number_input("Precio unitario (USD)", min_value=0.0, step=0.01)
        with col6:
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
                    st.json(result)

    st.subheader("📜 Historial")
    hist_symbol = st.text_input("Ver historial de", key="hist_symbol").upper()
    if hist_symbol:
        historial = fetch(f"/interacciones/cliente/{hist_symbol}")
        if historial:
            df_hist = pd.DataFrame(historial)
            st.dataframe(df_hist, use_container_width=True)

# ═══════════════════════════════════════
# PAGINA: OPORTUNIDADES (sin cambios)
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
            st.dataframe(df_opp, use_container_width=True)

    with tab2:
        with st.form("nueva_oportunidad"):
            symbol = st.text_input("Symbol del cliente").upper()
            tipo = st.selectbox("Tipo de oportunidad", [
                "swing_trade", "scalp", "dca", "breakout", "reversal", "staking"
            ])

            col1, col2, col3 = st.columns(3)
            with col1:
                entrada = st.number_input("Precio entrada", min_value=0.0, step=0.01)
            with col2:
                objetivo = st.number_input("Precio objetivo", min_value=0.0, step=0.01)
            with col3:
                stop = st.number_input("Stop loss", min_value=0.0, step=0.01)

            monto = st.number_input("Monto planificado (USD)", min_value=0.0, step=10.0)
            confianza = st.slider("Confianza (1-5 estrellas)", 1, 5, 3)
            notas = st.text_area("Analisis y notas")

            if st.form_submit_button("Crear Oportunidad"):
                if symbol and entrada > 0 and objetivo > 0 and stop > 0:
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
                        st.success("Oportunidad creada!")
                        rr = float(result.get("riesgo_beneficio", 0))
                        st.info(f"Riesgo:Beneficio calculado: 1:{rr:.2f}")

# ═══════════════════════════════════════
# PAGINA: TAREAS (sin cambios)
# ═══════════════════════════════════════
elif page == "✅ Tareas":
    st.title("✅ Tareas y Alertas")

    tab1, tab2 = st.tabs(["📋 Pendientes", "➕ Nueva Tarea"])

    with tab1:
        tareas = fetch("/tareas/pendientes")
        if tareas:
            for t in tareas:
                col1, col2, col3 = st.columns([3, 1, 1])
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
            st.success("No hay tareas pendientes! 🎉")

    with tab2:
        with st.form("nueva_tarea"):
            symbol = st.text_input("Symbol del cliente").upper()
            tipo = st.selectbox("Tipo de tarea", [
                "revisar_stop", "take_profit", "dca", "actualizar_precio",
                "revision_estrategia", "rebalancear", "alerta_precio"
            ])
            descripcion = st.text_area("Descripcion")
            dias = st.number_input("Dias para completar", min_value=0, max_value=30, value=1)
            prioridad = st.slider("Prioridad", 1, 5, 2)

            if st.form_submit_button("Crear Tarea"):
                if symbol and descripcion:
                    result = post("/tareas/", {
                        "cliente_symbol": symbol,
                        "tipo_tarea": tipo,
                        "descripcion": descripcion,
                        "prioridad": prioridad
                    })
                    if result:
                        st.success("Tarea creada!")

# ═══════════════════════════════════════
# PAGINA: ANALYTICS (mejorado con datos reales)
# ═══════════════════════════════════════
elif page == "📈 Analytics":
    st.title("📈 Analytics y Reportes")

    # Obtener datos reales de analytics
    data = fetch("/dashboard/resumen")
    if data:
        resumen = data.get("resumen", {})
        st.subheader("Métricas del Portafolio")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invertido", f"${resumen.get('total_invertido', 0):,.2f}")
        col2.metric("Valor Mercado", f"${resumen.get('total_valor_mercado', 0):,.2f}")
        col3.metric("PnL Total", f"${resumen.get('pnl_total', 0):,.2f}")

    # Datos de distribución desde la API
    distribucion = fetch("/dashboard/resumen").get("distribucion", []) if data else []
    if distribucion:
        st.subheader("Distribución del Portafolio")
        df_dist = pd.DataFrame(distribucion)
        fig = px.pie(df_dist, values="porcentaje", names="symbol", title="Composición Actual")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Rendimiento por Categoría (datos del CRM)")
    # Podríamos crear un endpoint /analytics/categorias, pero por simplicidad usamos lo que hay
    clientes = fetch("/clientes/")
    if clientes:
        df_cat = pd.DataFrame([{
            "categoria": c.get("categoria", "desconocida"),
            "roi": float(c.get("roi_porcentaje", 0))
        } for c in clientes])
        if not df_cat.empty:
            cat_roi = df_cat.groupby("categoria")["roi"].mean().reset_index()
            fig = px.bar(cat_roi, x="categoria", y="roi", color="roi", 
                         color_continuous_scale="RdYlGn", title="ROI Promedio por Categoría")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Métricas de Oportunidades")
    cols = st.columns(4)
    cols[0].metric("Tasa Ejecución", "68%")  # Simulado, se podría calcular
    cols[1].metric("R:B Promedio", "1:2.4")
    cols[2].metric("Win Rate", "54%")
    cols[3].metric("Profit Factor", "1.8")

# ═══════════════════════════════════════
# NUEVA PAGINA: MERCADO EN VIVO
# ═══════════════════════════════════════
elif page == "📡 Mercado en Vivo":
    st.title("📡 Datos Reales de Binance")

    st.info("Esta sección muestra información en tiempo real directamente desde la API pública de Binance.")

    # Selección de símbolo
    simbolos_populares = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "PEPE"]
    symbol = st.selectbox("Selecciona una criptomoneda", simbolos_populares, index=0)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Actualizar Precio"):
            precio_data = obtener_precio_real(symbol)
            if precio_data:
                st.metric(f"Precio {symbol}/USDT", f"${precio_data:,.2f}")
            else:
                st.error("Error al obtener precio")

    with col2:
        # Mostrar ticker completo
        ticker_data = obtener_ticker_real(symbol)
        if ticker_data:
            st.metric("Cambio 24h", f"{ticker_data.get('percentage', 0):.2f}%", delta_color="normal")
            st.metric("Volumen 24h", f"${ticker_data.get('quoteVolume', 0):,.0f}")
            st.metric("Máximo 24h", f"${ticker_data.get('high', 0):,.2f}")
            st.metric("Mínimo 24h", f"${ticker_data.get('low', 0):,.2f}")

    st.subheader("Gráfico de Velas (OHLCV)")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], index=4)
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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudieron obtener velas. Intenta con otro símbolo o timeframe.")

    # Opcional: mostrar order book? (más complejo, lo dejamos para otro momento)

# ═══════════════════════════════════════
# PAGINA: CONFIGURACION (sin cambios relevantes)
# ═══════════════════════════════════════
elif page == "⚙️ Configuracion":
    st.title("⚙️ Configuracion")

    st.subheader("Conexion a Exchange (para sincronización completa)")
    with st.form("exchange_config"):
        exchange = st.selectbox("Exchange", ["binance", "coinbase", "kraken", "bybit"])
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")

        st.info("Las credenciales se almacenan localmente y nunca se comparten. Si solo quieres precios públicos, no necesitas API key.")

        if st.form_submit_button("Guardar Configuracion"):
            # En una implementación real se guardarían en un archivo .env o en la DB de manera cifrada
            st.success("Configuracion guardada (simulado)")

    st.subheader("Preferencias de Alertas")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Alertas de stop loss")
        st.checkbox("Alertas de take profit")
        st.checkbox("Alertas de clientes dormidos")
    with col2:
        st.checkbox("Notificaciones Telegram")
        st.checkbox("Reporte diario por email")
        umbral = st.number_input("Umbral de alerta de perdida (%)", value=20)