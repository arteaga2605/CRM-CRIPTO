import sys
import os
from datetime import datetime, timedelta

# Incluir la carpeta raíz del proyecto en el path de búsqueda
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session
from app.models import SessionLocal, InversionDeportiva, EstadoInversionDeportiva
from app.services.deportes_service import DeportesService

# MODIFICACIÓN 3: Define aquí el capital base que tienes en tu cuenta deportiva
CAPITAL_BASE_INICIAL = 4236.00 

def mostrar_pagina_deportes():
    st.title("⚽ Inversiones y Apuestas Deportivas")
    st.markdown("Gestión de capital (*Bankroll*) independiente del portafolio cripto.")

    db = SessionLocal()
    try:
        srv = DeportesService(db)
        stats = srv.obtener_resumen_y_estadisticas()

        capital_actual = CAPITAL_BASE_INICIAL + stats['pnl_neto']

        # ─── METRICAS PRINCIPALES ───
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Capital Actual", f"${capital_actual:,.2f}", delta=f"{stats['pnl_neto']:,.2f} PnL Neto")
        col2.metric("Tasa Aciertos (Win Rate)", f"{stats['win_rate']}%")
        col3.metric("Capital en Juego", f"${stats['capital_en_juego']:,.2f}")
        col4.metric("Equipo Más Rentable", str(stats['equipo_mas_rentable']), delta=f"${stats['max_ganancia_equipo']:,.2f}")
        col5.metric("Total Apuestas", f"{stats['total_inversiones']} ({stats['ganadas']}G / {stats['perdidas']}P)")

        st.divider()

        # ─── REPORTE POR FECHAS ───
        st.subheader("📅 Generar Reporte de Resultados")
        with st.expander("Generar Reporte (Semanal, Mensual o Personalizado)", expanded=False):
            col_d1, col_d2, col_d3 = st.columns([2, 2, 1])
            with col_d1:
                # Por defecto selecciona los últimos 7 días
                fecha_inicio_input = st.date_input("Fecha Inicio", value=datetime.today().date() - timedelta(days=7))
            with col_d2:
                fecha_fin_input = st.date_input("Fecha Fin", value=datetime.today().date())
            with col_d3:
                st.write("") # Espaciador
                st.write("") # Espaciador
                generar_reporte = st.button("📊 Generar Reporte", use_container_width=True)
            
            if generar_reporte:
                if fecha_inicio_input > fecha_fin_input:
                    st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
                else:
                    # Convertir a datetime exactos para la consulta a la BD
                    dt_inicio = datetime.combine(fecha_inicio_input, datetime.min.time())
                    dt_fin = datetime.combine(fecha_fin_input, datetime.max.time())
                    
                    reporte = srv.obtener_reporte_por_fechas(dt_inicio, dt_fin)
                    
                    st.markdown("### 📋 Resultados del Reporte")
                    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                    r_col1.metric("Total Inversiones", reporte["total_inversiones"])
                    r_col2.metric("✅ Ganadas", reporte["ganadas"])
                    r_col3.metric("❌ Perdidas", reporte["perdidas"])
                    
                    pnl_valor = reporte['pnl_total']
                    r_col4.metric("💰 PnL Total", f"${pnl_valor:,.2f}", 
                                  delta=f"${pnl_valor:,.2f}" if pnl_valor >= 0 else f"-${abs(pnl_valor):,.2f}",
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
                    capital = st.number_input("Capital Invertido ($)", min_value=1.0, value=20.0, step=5.0)
                    ganancia_pot = st.number_input("Ganancia Total a Cobrar ($)", min_value=0.0, value=38.0, step=5.0, help="El total que paga el ticket (Inversión + Ganancia)")
                    perdida_pot = st.number_input("Pérdida Potencial ($)", min_value=0.0, value=20.0, step=5.0)
                
                notas = st.text_input("Notas o Análisis del partido")
                
                if st.form_submit_button("Registrar Inversión"):
                    if not objetivo:
                        st.error("Por favor ingresa un equipo o resultado.")
                    else:
                        srv.crear_inversion(deporte, tipo_merc, objetivo, capital, ganancia_pot, perdida_pot, notas)
                        st.success(f"Inversión registrada para: {objetivo}")
                        st.rerun()

        # ─── GRÁFICOS ANALÍTICOS (MODIFICADO PARA MOSTRAR SOLO LAS ÚLTIMAS 10) ───
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
                    text="pnl", title="Ganancia/Pérdida Cronológica (USD)"
                )
                fig_pnl.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
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
                        st.metric("Capital", f"${inv.capital_invertido}")
                    with r3:
                        st.write(f"🟢 **A ganar:** +${inv.ganancia_potencial}")
                        st.write(f"🔴 **A perder:** -${inv.perdida_potencial}")
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