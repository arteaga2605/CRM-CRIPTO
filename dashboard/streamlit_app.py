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
# PAGINA: CLIENTES (sin cambios relevantes)
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
# PAGINA: OPORTUNIDADES (MEJORADA)
# ═══════════════════════════════════════
elif page == "🎯 Oportunidades":
    st.title("🎯 Pipeline de Oportunidades")
    
    # Obtener lista de clientes para validar
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
        
        # Opción para cerrar oportunidad
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
# PAGINA: TAREAS (MEJORADA)
# ═══════════════════════════════════════
elif page == "✅ Tareas":
    st.title("✅ Tareas y Alertas")
    
    # Obtener lista de clientes para validar
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
                    # Mostrar cliente y fecha
                    cliente_id = t.get('cliente_id')
                    if cliente_id:
                        # Podríamos obtener el símbolo, pero es más simple mostrar el ID
                        st.caption(f"Cliente ID: {cliente_id} | Límite: {t.get('fecha_limite', '')}")
                    else:
                        st.caption(f"Límite: {t.get('fecha_limite', '')}")
                    # Indicar si está vencida
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
    
    # Opcional: mostrar tareas completadas recientemente
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