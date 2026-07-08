import sys
import os

# SOLUCIÓN AL ERROR: Incluir la carpeta raíz del proyecto en el path de búsqueda
# Esto permite que Python encuentre los módulos en 'app/' desde 'dashboard/'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session
from app.models import SessionLocal, InversionDeportiva, EstadoInversionDeportiva
from app.services.deportes_service import DeportesService

def mostrar_pagina_deportes():
    st.title("⚽ Inversiones y Apuestas Deportivas")
    st.markdown("Gestión de capital (*Bankroll*) independiente del portafolio cripto.")

    db = SessionLocal()
    try:
        srv = DeportesService(db)
        stats = srv.obtener_resumen_y_estadisticas()

        # ─── METRICAS PRINCIPALES ───
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("PnL Neto Realizado", f"${stats['pnl_neto']:,.2f}", delta_color="normal")
        col2.metric("Tasa Aciertos (Win Rate)", f"{stats['win_rate']}%")
        col3.metric("Capital en Juego", f"${stats['capital_en_juego']:,.2f}")
        col4.metric("Equipo Más Rentable", str(stats['equipo_mas_rentable']), delta=f"${stats['max_ganancia_equipo']:,.2f}")
        col5.metric("Total Apuestas", f"{stats['total_inversiones']} ({stats['ganadas']}G / {stats['perdidas']}P)")

        st.divider()

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
                    
                    cuota = st.number_input("Cuota / Odds (Opcional)", min_value=0.0, value=1.90, step=0.05)
                with c3:
                    capital = st.number_input("Capital Invertido ($)", min_value=1.0, value=20.0, step=5.0)
                    ganancia_pot = st.number_input("Ganancia Potencial ($)", min_value=0.0, value=18.0, step=5.0)
                    perdida_pot = st.number_input("Pérdida Potencial ($)", min_value=0.0, value=20.0, step=5.0)
                
                notas = st.text_input("Notas o Análisis del partido")
                
                if st.form_submit_button("Registrar Inversión"):
                    if not objetivo:
                        st.error("Por favor ingresa un equipo o resultado.")
                    else:
                        srv.crear_inversion(deporte, tipo_merc, objetivo, capital, ganancia_pot, perdida_pot, cuota, notas)
                        st.success(f"Inversión registrada para: {objetivo}")
                        st.rerun()

        # ─── GRÁFICOS ANALÍTICOS ───
        desglose = stats["desglose_por_objetivo"]
        if desglose:
            df_desglose = pd.DataFrame(desglose)
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.subheader("🏆 Ganancias y Pérdidas por Equipo/Objetivo")
                fig_pnl = px.bar(
                    df_desglose.sort_values("pnl", ascending=True),
                    x="pnl", y="objetivo", orientation="h",
                    color="pnl", color_continuous_scale="RdYlGn",
                    text="pnl", title="Rendimiento Acumulado (USD)"
                )
                fig_pnl.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
                st.plotly_chart(fig_pnl, use_container_width=True)
                
            with g_col2:
                st.subheader("📊 Frecuencia de Inversión por Deporte/Equipo")
                fig_veces = px.bar(
                    df_desglose.sort_values("veces", ascending=False),
                    x="objetivo", y="veces", color="deporte",
                    text="veces", title="Cantidad de Apuestas Realizadas"
                )
                st.plotly_chart(fig_veces, use_container_width=True)
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