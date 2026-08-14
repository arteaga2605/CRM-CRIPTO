import sys
import os
from datetime import datetime, timedelta

# Incluir la carpeta raíz del proyecto en el path de búsqueda
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from sqlalchemy.orm import Session
from app.models import SessionLocal, InversionDeportiva, EstadoInversionDeportiva
from app.services.deportes_service import DeportesService

# Define aquí el capital base que tienes en tu cuenta deportiva
CAPITAL_BASE_INICIAL = 1000.00 

API_URL = "http://localhost:8000"

def mostrar_pagina_deportes():
    st.title("⚽ Inversiones y Apuestas Deportivas")
    st.markdown("Gestión de capital (*Bankroll*) independiente del portafolio cripto.")

    db = SessionLocal()
    try:
        srv = DeportesService(db)
        stats = srv.obtener_resumen_y_estadisticas(capital_base=CAPITAL_BASE_INICIAL)

        capital_actual = stats['capital_actual']
        total_retiros = stats['total_retiros']
        total_inyecciones = stats['total_inyecciones']
        pnl_neto = stats['pnl_neto']

        # ─── METRICAS PRINCIPALES ───
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Capital Actual", f"Bs {capital_actual:,.2f}", delta=f"{stats['pnl_neto']:,.2f} PnL Neto")
        col2.metric("Tasa Aciertos (Win Rate)", f"{stats['win_rate']}%")
        col3.metric("Capital en Juego", f"Bs {stats['capital_en_juego']:,.2f}")
        col4.metric("Equipo Más Rentable", str(stats['equipo_mas_rentable']), delta=f"Bs {stats['max_ganancia_equipo']:,.2f}")
        col5.metric("Total Apuestas", f"{stats['total_inversiones']} ({stats['ganadas']}G / {stats['perdidas']}P)")

        # ─── DESGLOSE TRANSPARENTE DEL CAPITAL ───
        with st.expander("🔍 Ver desglose del cálculo de Capital", expanded=False):
            st.markdown("""
            <div style="background-color: #1e2a3a; padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
            <table style="width:100%; color: #e0e0e0; font-size: 14px;">
                <tr><td style="padding: 6px 0;">💵 Capital Base Inicial</td><td style="text-align:right; font-weight:600;">Bs {:,.2f}</td></tr>
                <tr><td style="padding: 6px 0; color: #00e676;">⬆️ Total Inyecciones de Capital</td><td style="text-align:right; font-weight:600; color: #00e676;">+Bs {:,.2f}</td></tr>
                <tr><td style="padding: 6px 0;">📈 PnL Neto Acumulado (Ganadas - Perdidas)</td><td style="text-align:right; font-weight:600; color: {};">Bs {:,.2f}</td></tr>
                <tr><td style="padding: 6px 0; border-top: 1px solid rgba(255,255,255,0.1);">💰 Subtotal (Base + Inyecciones + PnL)</td><td style="text-align:right; font-weight:600; border-top: 1px solid rgba(255,255,255,0.1);">Bs {:,.2f}</td></tr>
                <tr><td style="padding: 6px 0; color: #ff6b6b;">⬇️ Total Retiros Registrados</td><td style="text-align:right; font-weight:600; color: #ff6b6b;">-Bs {:,.2f}</td></tr>
                <tr><td style="padding: 10px 0; border-top: 2px solid #ffd700; font-size: 16px; font-weight:700; color: #ffd700;">🏦 CAPITAL ACTUAL REAL</td><td style="text-align:right; font-weight:700; color: #ffd700; border-top: 2px solid #ffd700; font-size: 16px;">Bs {:,.2f}</td></tr>
            </table>
            </div>
            """.format(
                CAPITAL_BASE_INICIAL,
                total_inyecciones,
                "#00e676" if pnl_neto >= 0 else "#ff6b6b", pnl_neto,
                CAPITAL_BASE_INICIAL + total_inyecciones + pnl_neto,
                total_retiros,
                capital_actual
            ), unsafe_allow_html=True)

            if total_inyecciones > 0:
                st.success(f"💡 Has inyectado Bs {total_inyecciones:,.2f} de capital adicional. Tu inversión total de bolsillo es: Bs {CAPITAL_BASE_INICIAL + total_inyecciones:,.2f}")
            if total_retiros > 0:
                st.info(f"ℹ️ Has retirado Bs {total_retiros:,.2f} en total.")

            # Comparativa: ¿Estoy en ganancia o pérdida respecto a lo invertido?
            dinero_de_bolsillo = CAPITAL_BASE_INICIAL + total_inyecciones
            ganancia_vs_bolsillo = capital_actual - dinero_de_bolsillo
            if dinero_de_bolsillo > 0:
                if ganancia_vs_bolsillo >= 0:
                    st.success(f"🎯 **Estás en GANANCIA** respecto a tu dinero de bolsillo: +Bs {ganancia_vs_bolsillo:,.2f} ({(ganancia_vs_bolsillo/dinero_de_bolsillo)*100:.1f}%)")
                else:
                    st.error(f"🎯 **Estás en PÉRDIDA** respecto a tu dinero de bolsillo: Bs {ganancia_vs_bolsillo:,.2f} ({(ganancia_vs_bolsillo/dinero_de_bolsillo)*100:.1f}%)")

        st.divider()

        # ─── SECCION: INYECCIONES Y RETIROS (DOS COLUMNAS) ───
        st.subheader("💰 Movimientos de Capital (Inyecciones / Retiros)")

        col_i1, col_r2 = st.columns(2)

        # ─── INYECCIONES ───
        with col_i1:
            with st.expander("⬆️ Inyectar Capital Nuevo", expanded=False):
                st.info(f"Capital actual: **Bs {capital_actual:,.2f}**")
                with st.form("form_inyeccion"):
                    monto_inyeccion = st.number_input(
                        "Monto a inyectar (Bs)", 
                        min_value=0.01, 
                        value=100.0,
                        step=10.0,
                        format="%.2f"
                    )
                    notas_inyeccion = st.text_input("Notas / Origen del capital", value="Recarga de bankroll")

                    submitted_inyeccion = st.form_submit_button("💵 Inyectar Capital", type="primary", use_container_width=True)

                    if submitted_inyeccion:
                        if monto_inyeccion <= 0:
                            st.error("El monto debe ser mayor a cero.")
                        else:
                            try:
                                r = requests.post(
                                    f"{API_URL}/deportes/inyecciones",
                                    json={"monto": monto_inyeccion, "notas": notas_inyeccion},
                                    timeout=10
                                )
                                if r.status_code == 200:
                                    data = r.json()
                                    st.success(f"✅ Inyección de Bs {data['monto']:,.2f} registrada!")
                                    st.info(f"Capital actualizado: Bs {data['capital_actual']:,.2f}")
                                    st.rerun()
                                elif r.status_code == 400:
                                    st.error(f"Error: {r.json().get('detail', 'Solicitud inválida')}")
                                else:
                                    st.error(f"Error del servidor: {r.status_code}")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")

            with st.expander("📜 Historial de Inyecciones", expanded=False):
                try:
                    r = requests.get(f"{API_URL}/deportes/inyecciones?limit=20", timeout=10)
                    if r.status_code == 200:
                        inyecciones = r.json()
                        if inyecciones:
                            df_iny = pd.DataFrame([{
                                "Fecha": datetime.fromisoformat(ic["fecha_inyeccion"]).strftime("%Y-%m-%d %H:%M"),
                                "Monto": float(ic["monto"]),
                                "Notas": ic.get("notas", "")
                            } for ic in inyecciones])

                            st.dataframe(df_iny, use_container_width=True, hide_index=True)

                            fig_iny = px.bar(
                                df_iny.iloc[::-1],
                                x="Fecha",
                                y="Monto",
                                text="Monto",
                                title="Historial de Inyecciones de Capital",
                                color="Monto",
                                color_continuous_scale="Greens"
                            )
                            fig_iny.update_traces(texttemplate='Bs %{text:,.2f}', textposition='outside')
                            st.plotly_chart(fig_iny, use_container_width=True)
                        else:
                            st.info("No hay inyecciones registradas todavía.")
                    else:
                        st.warning("No se pudo cargar el historial de inyecciones.")
                except Exception as e:
                    st.error(f"Error cargando inyecciones: {e}")

        # ─── RETIROS ───
        with col_r2:
            with st.expander("⬇️ Retirar Capital / Ganancias", expanded=False):
                st.info(f"Capital disponible para retirar: **Bs {capital_actual:,.2f}**")
                with st.form("form_retiro"):
                    monto_retiro = st.number_input(
                        "Monto a retirar (Bs)", 
                        min_value=0.01, 
                        max_value=float(capital_actual) if capital_actual > 0 else 0.01,
                        value=min(100.0, float(capital_actual)) if capital_actual > 0 else 0.01,
                        step=10.0,
                        format="%.2f"
                    )
                    notas_retiro = st.text_input("Motivo / Notas del retiro", value="Retiro de ganancias")

                    submitted_retiro = st.form_submit_button("💸 Retirar Capital", type="primary", use_container_width=True)

                    if submitted_retiro:
                        if monto_retiro <= 0:
                            st.error("El monto debe ser mayor a cero.")
                        elif monto_retiro > capital_actual:
                            st.error(f"Fondos insuficientes. Capital disponible: Bs {capital_actual:,.2f}")
                        else:
                            try:
                                r = requests.post(
                                    f"{API_URL}/deportes/retiros",
                                    json={"monto": monto_retiro, "notas": notas_retiro},
                                    timeout=10
                                )
                                if r.status_code == 200:
                                    data = r.json()
                                    st.success(f"✅ Retiro de Bs {data['monto']:,.2f} registrado exitosamente!")
                                    st.info(f"Capital restante: Bs {data['capital_restante']:,.2f}")
                                    st.rerun()
                                elif r.status_code == 400:
                                    st.error(f"Error: {r.json().get('detail', 'Solicitud inválida')}")
                                else:
                                    st.error(f"Error del servidor: {r.status_code}")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")

            with st.expander("📜 Historial de Retiros", expanded=False):
                try:
                    r = requests.get(f"{API_URL}/deportes/retiros?limit=20", timeout=10)
                    if r.status_code == 200:
                        retiros = r.json()
                        if retiros:
                            df_retiros = pd.DataFrame([{
                                "Fecha": datetime.fromisoformat(rt["fecha_retiro"]).strftime("%Y-%m-%d %H:%M"),
                                "Monto": float(rt["monto"]),
                                "Notas": rt.get("notas", "")
                            } for rt in retiros])

                            st.dataframe(df_retiros, use_container_width=True, hide_index=True)

                            fig_ret = px.bar(
                                df_retiros.iloc[::-1],
                                x="Fecha",
                                y="Monto",
                                text="Monto",
                                title="Historial de Retiros",
                                color="Monto",
                                color_continuous_scale="Reds"
                            )
                            fig_ret.update_traces(texttemplate='Bs %{text:,.2f}', textposition='outside')
                            st.plotly_chart(fig_ret, use_container_width=True)
                        else:
                            st.info("No hay retiros registrados todavía.")
                    else:
                        st.warning("No se pudo cargar el historial de retiros.")
                except Exception as e:
                    st.error(f"Error cargando retiros: {e}")

        st.divider()

        # ─── REPORTE POR FECHAS ───
        st.subheader("📅 Generar Reporte de Resultados")
        with st.expander("Generar Reporte (Semanal, Mensual o Personalizado)", expanded=False):
            col_d1, col_d2, col_d3 = st.columns([2, 2, 1])
            with col_d1:
                fecha_inicio_input = st.date_input("Fecha Inicio", value=datetime.today().date() - timedelta(days=7))
            with col_d2:
                fecha_fin_input = st.date_input("Fecha Fin", value=datetime.today().date())
            with col_d3:
                st.write("")
                st.write("")
                generar_reporte = st.button("📊 Generar Reporte", use_container_width=True)

            if generar_reporte:
                if fecha_inicio_input > fecha_fin_input:
                    st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
                else:
                    dt_inicio = datetime.combine(fecha_inicio_input, datetime.min.time())
                    dt_fin = datetime.combine(fecha_fin_input, datetime.max.time())

                    reporte = srv.obtener_reporte_por_fechas(dt_inicio, dt_fin)

                    st.markdown("### 📋 Resultados del Reporte")
                    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                    r_col1.metric("Total Inversiones", reporte["total_inversiones"])
                    r_col2.metric("✅ Ganadas", reporte["ganadas"])
                    r_col3.metric("❌ Perdidas", reporte["perdidas"])

                    pnl_valor = reporte['pnl_total']
                    r_col4.metric("💰 PnL Total", f"Bs {pnl_valor:,.2f}", 
                                  delta=f"Bs {pnl_valor:,.2f}" if pnl_valor >= 0 else f"-Bs {abs(pnl_valor):,.2f}",
                                  delta_color="normal" if pnl_valor >= 0 else "inverse")

        # ─── FORMULARIO DE REGISTRO ───
        with st.expander("➕ Registrar Nueva Inversión Deportiva", expanded=False):
            with st.form("form_deportes"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    deporte = st.selectbox("Deporte", ["BEISBOL", "FUTBOL", "BALONCESTO", "TENIS", "OTRO"])
                    tipo_merc = st.selectbox("Tipo de Mercado", ["EQUIPO", "RESULTADO", "ESTADISTICA"])
                with c2:
                    if tipo_merc == "EQUIPO":
                        objetivo = st.text_input("Nombre del Equipo (Mayúsculas automáticamente)").upper()
                    elif tipo_merc == "RESULTADO":
                        objetivo = st.text_input("Resultado (Ej: 2-1, 105, Empate)")
                    else:
                        objetivo = st.text_input("Estadística (Ej: OVER 8.5 STRIKEOUTS, +2.5 GOLES)").upper()
                with c3:
                    capital = st.number_input("Capital Invertido (Bs)", min_value=1.0, value=20.0, step=5.0)
                    ganancia_pot = st.number_input("Ganancia Total a Cobrar (Bs)", min_value=0.0, value=38.0, step=5.0, help="El total que paga el ticket (Inversión + Ganancia)")
                    perdida_pot = st.number_input("Pérdida Potencial (Bs)", min_value=0.0, value=20.0, step=5.0)

                notas = st.text_input("Notas o Análisis del partido")

                if st.form_submit_button("Registrar Inversión"):
                    if not objetivo:
                        st.error("Por favor ingresa un equipo o resultado.")
                    else:
                        srv.crear_inversion(deporte, tipo_merc, objetivo, capital, ganancia_pot, perdida_pot, notas)
                        st.success(f"Inversión registrada para: {objetivo}")
                        st.rerun()

        # ─── GRÁFICOS ANALÍTICOS ───
        ultimas_10 = stats.get("ultimas_10_inversiones", [])
        if ultimas_10:
            df_ultimas = pd.DataFrame(ultimas_10)
            df_ultimas["etiqueta"] = df_ultimas["id"].astype(str) + " - " + df_ultimas["objetivo"]

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.subheader("🏆 PnL de las Últimas 10 Inversiones")
                fig_pnl = px.bar(
                    df_ultimas,
                    x="etiqueta", y="pnl",
                    color="pnl", color_continuous_scale="RdYlGn",
                    text="pnl", title="Ganancia/Pérdida Cronológica (Bs)"
                )
                fig_pnl.update_traces(texttemplate='Bs %{text:.2f}', textposition='outside')
                st.plotly_chart(fig_pnl, use_container_width=True)

            with g_col2:
                st.subheader("📊 Deporte en las Últimas 10")
                fig_pie = px.pie(
                    df_ultimas, 
                    names="deporte", 
                    title="Distribución de Deporte (Recientes)",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay estadísticas históricas cerradas aún para generar gráficos.")

        # ─── NUEVO: GRÁFICO DE LÍNEA PnL DIARIO (ÚLTIMOS 7 DÍAS) ───
        st.divider()
        st.subheader("📈 PnL Diario (Últimos 7 días)")
        try:
            r = requests.get(f"{API_URL}/deportes/pnl-diario?dias=7", timeout=10)
            if r.status_code == 200:
                pnl_data = r.json()
                if pnl_data:
                    df_pnl_dia = pd.DataFrame(pnl_data)
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(
                        x=df_pnl_dia["fecha"],
                        y=df_pnl_dia["pnl"],
                        mode='lines+markers+text',
                        name='PnL',
                        line=dict(color='#00e676', width=3),
                        marker=dict(size=8, color=['#00e676' if v >= 0 else '#ff6b6b' for v in df_pnl_dia["pnl"]]),
                        text=df_pnl_dia["pnl"].apply(lambda x: f"Bs {x:.2f}"),
                        textposition="top center"
                    ))
                    fig_line.update_layout(
                        title="Evolución diaria de Ganancias / Pérdidas",
                        xaxis_title="Fecha",
                        yaxis_title="PnL (Bs)",
                        height=400,
                        template="plotly_dark",
                        showlegend=False
                    )
                    fig_line.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("No hay datos de PnL diario todavía.")
            else:
                st.warning("No se pudo cargar el PnL diario.")
        except Exception as e:
            st.error(f"Error cargando PnL diario: {e}")

        # ─── TABLA DE LIQUIDACIÓN DE APUESTAS ABIERTAS ───
        st.subheader("⏳ Inversiones Abiertas (Pendientes por Resultado)")
        abiertas_db = db.query(InversionDeportiva).filter_by(estado=EstadoInversionDeportiva.ABIERTA).all()
        if abiertas_db:
            for inv in abiertas_db:
                with st.container():
                    r1, r2, r3, r4 = st.columns([2, 1, 2, 2])
                    with r1:
                        st.markdown(f"**{inv.deporte}** | `{inv.tipo_mercado.value}`")
                        st.markdown(f"### {inv.objetivo}")
                    with r2:
                        st.metric("Capital", f"Bs {inv.capital_invertido}")
                    with r3:
                        st.write(f"🟢 **A ganar:** +Bs {inv.ganancia_potencial}")
                        st.write(f"🔴 **A perder:** -Bs {inv.perdida_potencial}")
                    with r4:
                        st.write("Liq. Resultado:")
                        b_col1, b_col2, b_col3 = st.columns(3)
                        if b_col1.button("✅ Ganó", key=f"g_{inv.id}"):
                            srv.liquidar_inversion(inv.id, "GANADA")
                            st.rerun()
                        if b_col2.button("❌ Perdió", key=f"p_{inv.id}"):
                            srv.liquidar_inversion(inv.id, "PERDIDA")
                            st.rerun()
                        if b_col3.button("⚪ Nulo", key=f"n_{inv.id}"):
                            srv.liquidar_inversion(inv.id, "NULA")
                            st.rerun()
                st.divider()
        else:
            st.write("No tienes inversiones deportivas abiertas en este momento.")

    finally:
        db.close()

