"""
Página de mercado P2P de Binance.
Muestra mejores precios, spreads y oportunidades.
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://localhost:8000"

@st.cache_data(ttl=300)
def obtener_datos_p2p(asset, fiat):
    try:
        r = requests.get(f"{API_URL}/p2p/best-prices", params={"asset": asset, "fiat": fiat}, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error {r.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def mostrar_pagina_p2p():
    st.title("📊 Mercado P2P Binance")
    st.markdown("Monitorea spreads entre compra y venta para detectar oportunidades de arbitraje.")

    col1, col2 = st.columns(2)
    with col1:
        asset = st.selectbox("Criptomoneda", ["USDT", "BTC", "ETH", "BNB"], index=0)
    with col2:
        fiat = st.selectbox("Moneda fiat", ["ARS", "MXN", "COP", "PEN", "CLP", "BRL", "VES", "USD"], index=0)

    if st.button("🔄 Actualizar ahora"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Consultando Binance P2P..."):
        data = obtener_datos_p2p(asset, fiat)

    if not data:
        st.warning("No se pudieron obtener datos. Intenta más tarde.")
        return

    # Métricas principales
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("💰 Comprar (SELL)", f"${data['buy_price']:.2f}", delta=f"${data['buy_price']:.2f}")
    col_b.metric("💰 Vender (BUY)", f"${data['sell_price']:.2f}", delta=f"${data['sell_price']:.2f}")
    col_c.metric("Spread absoluto", f"${data['spread_abs']:.2f}")
    col_d.metric("Spread %", f"{data['spread_pct']:.2f}%", 
                 delta=f"{data['spread_pct']:.2f}%" if data['spread_pct'] > 0 else None)

    st.divider()

    # Oportunidad
    if data['spread_pct'] > 1.0:
        st.success(f"📢 **Oportunidad de arbitraje!** Comprar a ${data['buy_price']:.2f} y vender a ${data['sell_price']:.2f} → ganancia de ${data['spread_abs']:.2f} por unidad ({data['spread_pct']:.2f}%).")
    else:
        st.info("Spread bajo. No hay oportunidad clara en este momento.")

    # Órdenes de compra (anuncios BUY)
    st.subheader("📈 Órdenes de compra (ellos compran, nosotros vendemos)")
    buy_orders = data.get("buy_orders", [])
    if buy_orders:
        df_buy = pd.DataFrame([{
            "Precio": float(o["adv"]["price"]),
            "Monto mínimo": float(o["adv"]["minSingleTransAmount"]),
            "Monto máximo": float(o["adv"]["maxSingleTransAmount"]),
            "Métodos de pago": ", ".join([p["payType"] for p in o["adv"].get("payTypes", [])])
        } for o in buy_orders])
        st.dataframe(df_buy, width='stretch')
    else:
        st.info("No hay órdenes de compra.")

    # Órdenes de venta (anuncios SELL)
    st.subheader("📉 Órdenes de venta (ellos venden, nosotros compramos)")
    sell_orders = data.get("sell_orders", [])
    if sell_orders:
        df_sell = pd.DataFrame([{
            "Precio": float(o["adv"]["price"]),
            "Monto mínimo": float(o["adv"]["minSingleTransAmount"]),
            "Monto máximo": float(o["adv"]["maxSingleTransAmount"]),
            "Métodos de pago": ", ".join([p["payType"] for p in o["adv"].get("payTypes", [])])
        } for o in sell_orders])
        st.dataframe(df_sell, width='stretch')
    else:
        st.info("No hay órdenes de venta.")

    st.caption(f"Última actualización: {data.get('timestamp', '')}")