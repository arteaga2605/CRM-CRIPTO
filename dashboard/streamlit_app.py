"""
Dashboard visual del CRM Crypto usando Streamlit.
Ejecuta: streamlit run dashboard/streamlit_app.py
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from noticias import mostrar_pagina_noticias
from datetime import datetime, timedelta
from p2p import mostrar_pagina_p2p
from streamlit_autorefresh import st_autorefresh
import time
from scipy.stats import pearsonr
import numpy as np
from deportes import mostrar_pagina_deportes

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Crypto CRM Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS PERSONALIZADO PARA SIDEBAR MEJORADO Y TEMA OSCURO PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Ocultar el radio group nativo de Streamlit en el sidebar */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: none !important;
    }

    /* Fondo del sidebar con gradiente oscuro premium */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 50%, #0d1117 100%) !important;
        border-right: 1px solid rgba(255,215,0,0.08) !important;
    }

    /* Ocultar el header del sidebar */
    [data-testid="stSidebar"] .css-1d391kg,
    [data-testid="stSidebar"] h1 {
        display: none !important;
    }

    /* Estilos para botones de navegacion personalizados */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        color: rgba(224,224,224,0.85) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        margin: 0 0 3px 0 !important;
        border-radius: 10px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
        background: rgba(255,255,255,0.04) !important;
        border: none !important;
        color: rgba(224,224,224,0.85) !important;
    }

    /* Boton activo (dorado) */
    .nav-active button[kind="secondary"] {
        background: linear-gradient(90deg, rgba(255,215,0,0.12) 0%, rgba(255,215,0,0.04) 100%) !important;
        border: 1px solid rgba(255,215,0,0.15) !important;
        color: #ffd700 !important;
        font-weight: 600 !important;
    }

    .nav-active button[kind="secondary"]:hover {
        background: linear-gradient(90deg, rgba(255,215,0,0.15) 0%, rgba(255,215,0,0.06) 100%) !important;
        border: 1px solid rgba(255,215,0,0.2) !important;
        color: #ffd700 !important;
    }

    /* Ocultar el label de los botones de navegacion */
    .nav-item-label {
        display: none !important;
    }

    /* Estilos para el contenido principal */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Scrollbar personalizada */
    [data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 4px;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: transparent;
    }
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(255,215,0,0.2);
        border-radius: 2px;
    }

    /* Ocultar el texto del radio nativo que queda */
    [data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0 !important;
    }

    /* Estilos para metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30,42,58,0.6) 0%, rgba(15,23,36,0.8) 100%);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 16px;
    }

    [data-testid="stMetric"] > div:first-child {
        color: rgba(176,196,222,0.6) !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stMetric"] > div:nth-child(2) {
        color: #fff !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    /* Estilos para expanders */
    [data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
        background: rgba(30,42,58,0.3) !important;
    }

    /* Estilos para dataframes */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* Estilos para botones primarios */
    button[kind="primary"] {
        background: linear-gradient(135deg, #ffd700 0%, #ffb800 100%) !important;
        color: #0a0e14 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(255,215,0,0.2) !important;
        transition: all 0.2s ease !important;
    }

    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(255,215,0,0.3) !important;
    }

    /* Estilos para selectbox y otros inputs */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stNumberInput"] > div > div,
    [data-testid="stTextInput"] > div > div {
        background: rgba(30,42,58,0.5) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }

    /* Estilos para tabs */
    [data-testid="stTabs"] [role="tablist"] {
        background: rgba(30,42,58,0.3) !important;
        border-radius: 12px !important;
        padding: 4px !important;
    }

    [data-testid="stTabs"] [role="tab"] {
        color: rgba(176,196,222,0.6) !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: rgba(255,215,0,0.1) !important;
        color: #ffd700 !important;
        font-weight: 600 !important;
    }

    /* Estilos para toast/notifications */
    .stToast {
        border-radius: 12px !important;
        border: 1px solid rgba(255,215,0,0.15) !important;
    }

    /* Estilos para el divider */
    hr {
        border-color: rgba(255,255,255,0.04) !important;
    }

    /* Estilos para checkbox */
    [data-testid="stCheckbox"] > label {
        color: rgba(224,224,224,0.85) !important;
    }

    /* Estilos para slider */
    [data-testid="stSlider"] > div {
        color: rgba(224,224,224,0.85) !important;
    }

    /* Estilos para date input */
    [data-testid="stDateInput"] > div > div {
        background: rgba(30,42,58,0.5) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }

    /* Estilos para text area */
    [data-testid="stTextArea"] > div > div {
        background: rgba(30,42,58,0.5) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }

    /* Estilos para form submit button */
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #ffd700 0%, #ffb800 100%) !important;
        color: #0a0e14 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
    }

    /* Estilos para download button */
    [data-testid="stDownloadButton"] > button {
        background: rgba(255,215,0,0.08) !important;
        border: 1px solid rgba(255,215,0,0.15) !important;
        color: #ffd700 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    [data-testid="stDownloadButton"] > button:hover {
        background: rgba(255,215,0,0.15) !important;
    }

    /* Estilos para info/alert boxes */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }

    .stAlert[data-baseweb="notification"] {
        background: rgba(30,42,58,0.5) !important;
    }

    /* Estilos para caption */
    .stCaption {
        color: rgba(176,196,222,0.5) !important;
    }

    /* Estilos para markdown h1, h2, h3 */
    .main h1 {
        color: #fff !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }

    .main h2 {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
    }

    .main h3 {
        color: rgba(224,224,224,0.9) !important;
        font-weight: 600 !important;
    }

    /* Estilos para spinner */
    .stSpinner > div {
        border-color: #ffd700 !important;
    }

    /* Estilos para progress bar */
    .stProgress > div > div {
        background-color: #ffd700 !important;
    }

    /* Estilos para el sidebar collapse button */
    [data-testid="stSidebarCollapseButton"] {
        color: rgba(176,196,222,0.6) !important;
    }

    [data-testid="stSidebarCollapseButton"]:hover {
        color: #ffd700 !important;
    }

    /* Ocultar footer y deploy button */
    footer, .stDeployButton, .stToolbar {
        display: none !important;
    }

    /* Estilos para dataframe headers */
    .stDataFrame th {
        background: rgba(30,42,58,0.8) !important;
        color: #ffd700 !important;
        font-weight: 600 !important;
        border-color: rgba(255,255,255,0.06) !important;
    }

    .stDataFrame td {
        border-color: rgba(255,255,255,0.03) !important;
    }

    .stDataFrame tr:hover td {
        background: rgba(255,255,255,0.02) !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (TODAS ORIGINALES, SIN MODIFICAR)
# ═══════════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PARA ANALISIS TECNICO (TODAS ORIGINALES)
# ═══════════════════════════════════════════════════════════════════════════════
def obtener_velas_binance(symbol, interval="1d", limit=30):
    """
    Obtiene velas OHLCV directamente desde Binance.
    Por defecto: interval="1d", limit=30 (ultimo mes)
    """
    try:
        pair = f"{symbol.upper()}USDT"
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
        }
        binance_interval = interval_map.get(interval, "1d")
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
    """Encuentra soportes (minimos locales) y resistencias (maximos locales) con ventana dinamica."""
    highs = [v["high"] for v in velas]
    lows = [v["low"] for v in velas]
    n = len(velas)
    window = max(2, min(5, n // 10))
    soportes = []
    resistencias = []
    for i in range(window, n - window):
        if all(lows[i] <= lows[i - j] for j in range(1, window+1)) and all(lows[i] <= lows[i + j] for j in range(1, window+1)):
            soportes.append(lows[i])
        if all(highs[i] >= highs[i - j] for j in range(1, window+1)) and all(highs[i] >= highs[i + j] for j in range(1, window+1)):
            resistencias.append(highs[i])
    soportes = sorted(list(set(soportes)), reverse=False)
    resistencias = sorted(list(set(resistencias)), reverse=True)
    precio_actual = velas[-1]["close"]
    soportes_cercanos = [s for s in soportes if s < precio_actual][-num_niveles:]
    if len(soportes_cercanos) < num_niveles and soportes:
        soportes_cercanos = soportes[-num_niveles:] if len(soportes) >= num_niveles else soportes
    resistencias_cercanas = [r for r in resistencias if r > precio_actual][:num_niveles]
    if len(resistencias_cercanas) < num_niveles and resistencias:
        resistencias_cercanas = resistencias[:num_niveles] if len(resistencias) >= num_niveles else resistencias
    return soportes_cercanos[:num_niveles], resistencias_cercanas[:num_niveles]

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PARA TENDENCIAS Y CORRELACIONES (TODAS ORIGINALES)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def obtener_simbolos_binance():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            symbols = [s["symbol"] for s in data["symbols"] if s["quoteAsset"] == "USDT"]
            return symbols
        else:
            return []
    except:
        return []

@st.cache_data(ttl=300)
def obtener_tendencias_coingecko():
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "coins" in data:
                trending = []
                for coin in data["coins"]:
                    item = coin["item"]
                    trending.append({
                        "id": item.get("id", ""),
                        "symbol": item.get("symbol", "").upper(),
                        "name": item.get("name", ""),
                        "score": item.get("score", 0),
                        "market_cap_rank": item.get("market_cap_rank", 0),
                        "thumb": item.get("thumb", "")
                    })
                return trending
            else:
                return None
        else:
            return None
    except Exception as e:
        st.error(f"Error conectando a CoinGecko: {e}")
        return None

@st.cache_data(ttl=300)
def obtener_precio_actual_coingecko(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if coin_id in data:
                return {
                    "price": data[coin_id].get("usd", 0),
                    "change_24h": data[coin_id].get("usd_24h_change", 0)
                }
        return {"price": 0, "change_24h": 0}
    except:
        return {"price": 0, "change_24h": 0}

@st.cache_data(ttl=3600)
def obtener_historicos_coingecko(coin_id, days=7):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            prices = data.get("prices", [])
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit='ms').dt.date
            daily_prices = df.groupby("date")["price"].last().reset_index()
            return daily_prices["price"].tolist()
        else:
            return []
    except:
        return []

def calcular_correlacion_con_btc(token_prices, btc_prices):
    if len(token_prices) < 2 or len(btc_prices) < 2:
        return None
    try:
        corr, _ = pearsonr(token_prices, btc_prices)
        return corr
    except:
        return None

# Categorias actualizadas (Binance)
CATEGORIAS = [
    "BNB Chain", "Solana", "RWA", "MEME", "Pagos", "IA",
    "Capa 1/Capa 2", "Fase semilla", "Launchpool", "New", "Megadrop",
    "Juegos", "DeFi", "En observacion", "Fan Token", "Infraestructura",
    "Almacenamiento", "NFT", "Launchpad", "Yzi", "desconocida"
]

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR MEJORADO - NAVEGACION POR BOTONES CON ESTILO PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

# Inicializar session_state para la pagina si no existe
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# Funcion helper para crear boton de navegacion con badge
def nav_button(label, icon, badge=None, badge_color="gold", key=None):
    """Crea un boton de navegacion estilizado para el sidebar."""
    is_active = st.session_state.page == label

    # Construir el texto del boton
    button_text = f"{icon}  {label}"
    if badge:
        button_text += f"  • {badge}"

    # CSS adicional para el estado activo
    if is_active:
        st.markdown(f'<div class="nav-active">', unsafe_allow_html=True)

    if st.button(button_text, key=key or f"nav_{label}", use_container_width=True, type="secondary"):
        st.session_state.page = label
        st.rerun()

    if is_active:
        st.markdown('</div>', unsafe_allow_html=True)

# Funcion para obtener datos del portfolio para el summary
def obtener_resumen_portfolio():
    """Obtiene datos resumidos del portfolio para mostrar en el sidebar."""
    try:
        data = fetch("/dashboard/resumen")
        if data and data.get("resumen"):
            return data["resumen"]
    except:
        pass
    return None

def obtener_contador_notificaciones():
    """Obtiene el contador de notificaciones no leidas."""
    try:
        notifs = fetch("/notifications?unread_only=true&limit=50")
        if notifs and isinstance(notifs, list):
            return len(notifs)
    except:
        pass
    return 0

def obtener_contador_tareas():
    """Obtiene el contador de tareas pendientes."""
    try:
        tareas = fetch("/tareas/pendientes")
        if tareas and isinstance(tareas, list):
            return len(tareas)
    except:
        pass
    return 0

def obtener_contador_oportunidades():
    """Obtiene el contador de oportunidades abiertas."""
    try:
        opps = fetch("/oportunidades/?estado=abierta")
        if opps and isinstance(opps, list):
            return len(opps)
    except:
        pass
    return 0

# ═══════════════════════════════════════════════════════════════════════════════
# RENDERIZAR SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ========== LOGO AREA ==========
    st.markdown("""
    <div style="padding: 8px 4px 16px 4px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 40px; height: 40px;
                background: linear-gradient(135deg, #ffd700 0%, #ffb800 100%);
                border-radius: 12px;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 4px 15px rgba(255,215,0,0.25), 0 0 30px rgba(255,215,0,0.1);
                font-size: 20px;
            ">🪙</div>
            <div>
                <div style="color: #ffd700; font-size: 18px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">Crypto CRM</div>
                <div style="color: rgba(176,196,222,0.6); font-size: 11px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">Portfolio Manager</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== MINI PORTFOLIO SUMMARY ==========
    resumen = obtener_resumen_portfolio()
    if resumen:
        pnl_total = resumen.get("pnl_total", 0)
        roi = resumen.get("roi_porcentaje", 0)
        activos = resumen.get("clientes_activos", 0)
        peligro = resumen.get("clientes_peligro", 0)

        pnl_color = "#00e676" if pnl_total >= 0 else "#ff6b6b"
        pnl_sign = "+" if pnl_total >= 0 else ""

        st.markdown(f"""
        <div style="
            margin: 0 0 16px 0;
            padding: 14px 16px;
            background: rgba(255,215,0,0.04);
            border: 1px solid rgba(255,215,0,0.1);
            border-radius: 14px;
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, #ffd700, transparent); opacity: 0.4;"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: rgba(176,196,222,0.7); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px;">PnL Total</span>
                <span style="color: {pnl_color}; font-size: 11px; font-weight: 700; background: rgba(0,230,118,0.1) if {pnl_total >= 0} else rgba(255,107,107,0.1); padding: 2px 8px; border-radius: 20px;">{pnl_sign}{roi:.1f}%</span>
            </div>
            <div style="color: #fff; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">${pnl_total:,.2f}</div>
            <div style="display: flex; gap: 12px; margin-top: 10px;">
                <div style="flex: 1; text-align: center; padding: 6px 0; background: rgba(0,0,0,0.2); border-radius: 8px;">
                    <div style="color: #ffd700; font-size: 13px; font-weight: 700;">{activos}</div>
                    <div style="color: rgba(176,196,222,0.5); font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px;">Activos</div>
                </div>
                <div style="flex: 1; text-align: center; padding: 6px 0; background: rgba(0,0,0,0.2); border-radius: 8px;">
                    <div style="color: #ff6b6b; font-size: 13px; font-weight: 700;">{peligro}</div>
                    <div style="color: rgba(176,196,222,0.5); font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px;">Alertas</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ========== NOTIFICACIONES TOAST ==========
    try:
        notificaciones = fetch("/notifications?unread_only=true&limit=10")
        if notificaciones and isinstance(notificaciones, list):
            unread_count = len(notificaciones)
            for notif in notificaciones:
                st.toast(notif["message"], icon="🔔")
        else:
            unread_count = 0
    except:
        unread_count = 0

    # ========== CONTROL DE ACTUALIZACION AUTOMATICA ==========
    st.markdown("""
    <div style="
        color: rgba(176,196,222,0.35);
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        padding: 8px 10px 4px;
    ">Sistema</div>
    """, unsafe_allow_html=True)

    auto_refresh = st.checkbox("🔄 Auto-refresh", value=False, key="auto_refresh_check")
    if auto_refresh:
        interval = st.selectbox("Intervalo (s)", [5, 10, 30, 60], index=1, key="refresh_interval", label_visibility="collapsed")
        st_autorefresh(interval=interval * 1000, key="auto_refresh")

    # ========== SECCION: PRINCIPAL ==========
    st.markdown("""
    <div style="
        color: rgba(176,196,222,0.35);
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        padding: 16px 10px 8px;
    ">Principal</div>
    """, unsafe_allow_html=True)

    # Obtener contadores dinamicos
    num_notifs = obtener_contador_notificaciones()
    num_tareas = obtener_contador_tareas()
    num_opps = obtener_contador_oportunidades()

    nav_button("Dashboard", "🏠", badge=str(num_notifs) if num_notifs > 0 else None, key="nav_dashboard")
    nav_button("Clientes", "👥", key="nav_clientes")
    nav_button("Interacciones", "💱", key="nav_interacciones")
    nav_button("Oportunidades", "🎯", badge=str(num_opps) if num_opps > 0 else None, key="nav_oportunidades")
    nav_button("Tareas", "✅", badge=f"{num_tareas} pend." if num_tareas > 0 else None, key="nav_tareas")
    nav_button("Lotes FIFO", "📦", key="nav_lotes")

    # ========== DIVIDER ==========
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent); margin: 12px 10px;"></div>
    """, unsafe_allow_html=True)

    # ========== SECCION: ANALISIS & MERCADO ==========
    st.markdown("""
    <div style="
        color: rgba(176,196,222,0.35);
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        padding: 8px 10px 8px;
    ">Analisis & Mercado</div>
    """, unsafe_allow_html=True)

    nav_button("Analytics", "📈", key="nav_analytics")
    nav_button("Mercado en Vivo", "📡", key="nav_mercado")
    nav_button("Tendencias", "🔥", key="nav_tendencias")
    nav_button("Eventos Binance", "📢", key="nav_eventos")
    nav_button("P2P Binance", "📊", key="nav_p2p")

    # ========== DIVIDER ==========
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent); margin: 12px 10px;"></div>
    """, unsafe_allow_html=True)

    # ========== SECCION: EXTRAS ==========
    st.markdown("""
    <div style="
        color: rgba(176,196,222,0.35);
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        padding: 8px 10px 8px;
    ">Extras</div>
    """, unsafe_allow_html=True)

    nav_button("Noticias", "📰", key="nav_noticias")
    nav_button("Inversiones Deportivas", "⚽", key="nav_deportes")
    nav_button("Configuracion", "⚙️", key="nav_config")

    # ========== FOOTER / API STATUS + USER ==========
    st.markdown("""
    <div style="
        padding: 16px 4px 8px;
        border-top: 1px solid rgba(255,255,255,0.04);
        margin-top: 16px;
    ">
        <div style="
            display: flex; align-items: center; gap: 8px;
            padding: 8px 12px;
            background: rgba(0,230,118,0.06);
            border: 1px solid rgba(0,230,118,0.1);
            border-radius: 10px;
            margin-bottom: 12px;
        ">
            <span style="width: 6px; height: 6px; background: #00e676; border-radius: 50%; box-shadow: 0 0 6px #00e676;"></span>
            <span style="color: rgba(0,230,118,0.8); font-size: 11px; font-weight: 600;">Binance API: Conectado</span>
        </div>

        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 34px; height: 34px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                color: white;
                font-size: 14px;
                font-weight: 700;
            ">Y</div>
            <div style="flex: 1; min-width: 0;">
                <div style="color: #e0e0e0; font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Yzi Trader</div>
                <div style="color: rgba(176,196,222,0.5); font-size: 10px;">v2.0.0 &bull; Pro</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Obtener la pagina actual de session_state
page = st.session_state.page

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
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

        # ========== NUEVA SECCION P2P CON TOP 20 CRIPTO ==========
        # ========== NUEVA SECCION P2P CON RECOMENDACION ==========
        st.subheader("📊 Oportunidad P2P en tiempo real")

        @st.cache_data(ttl=3600)
        def obtener_top_20_criptos():
            try:
                url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return [coin["symbol"].upper() for coin in data]
                else:
                    return ["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "LINK", "MATIC", "SHIB", "TRX", "AVAX", "UNI", "ATOM", "LTC", "NEAR", "ALGO", "ICP"]
            except:
                return ["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "LINK", "MATIC", "SHIB", "TRX", "AVAX", "UNI", "ATOM", "LTC", "NEAR", "ALGO", "ICP"]

        top_20 = obtener_top_20_criptos()

        col_a, col_b, col_c = st.columns([2, 1, 2])
        with col_a:
            fiat_sel = st.selectbox("Moneda fiat", ["ARS", "MXN", "COP", "PEN", "CLP", "BRL", "VES", "USD"], index=0, key="p2p_fiat_dash")
        with col_b:
            asset_sel = st.selectbox("Cripto", top_20, index=0, key="p2p_asset_dash")
        with col_c:
            if st.button("🔄 Actualizar oportunidad P2P", key="p2p_refresh_dash"):
                st.cache_data.clear()
                st.rerun()

        try:
            r = requests.get(f"{API_URL}/p2p/best-prices", params={"asset": asset_sel, "fiat": fiat_sel}, timeout=5)
            if r.status_code == 200:
                p2p_data = r.json()
                if p2p_data:
                    buy_price = p2p_data.get("buy_price", 0)
                    sell_price = p2p_data.get("sell_price", 0)
                    spread = p2p_data.get("spread_pct", 0)

                    # Verificar si hay datos validos (ambos precios > 0)
                    tiene_datos = buy_price > 0 and sell_price > 0

                    if tiene_datos:
                        col1p, col2p, col3p = st.columns(3)
                        with col1p:
                            st.markdown(f"""
                            <div style="background-color: #1e2a3a; padding: 15px; border-radius: 10px; border-left: 4px solid #00ff88;">
                                <h4 style="color: #00ff88; margin:0;">⬆ COMPRAR</h4>
                                <p style="font-size: 1.5rem; color: white; margin:0;">${buy_price:.2f}</p>
                                <p style="color: #b0c4de; margin:0;">{asset_sel}/{fiat_sel}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2p:
                            st.markdown(f"""
                            <div style="background-color: #1e2a3a; padding: 15px; border-radius: 10px; text-align: center;">
                                <h4 style="color: #ffd700; margin:0;">Spread</h4>
                                <p style="font-size: 1.5rem; color: white; margin:0;">{spread:.2f}%</p>
                                <p style="color: #b0c4de; margin:0;">{asset_sel}/{fiat_sel}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        with col3p:
                            st.markdown(f"""
                            <div style="background-color: #1e2a3a; padding: 15px; border-radius: 10px; border-left: 4px solid #ff4444;">
                                <h4 style="color: #ff4444; margin:0;">⬇ VENDER</h4>
                                <p style="font-size: 1.5rem; color: white; margin:0;">${sell_price:.2f}</p>
                                <p style="color: #b0c4de; margin:0;">{asset_sel}/{fiat_sel}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # ========== RECOMENDACION ==========
                        st.divider()
                        st.subheader("💡 Recomendacion P2P")

                        ganancia_por_unidad = sell_price - buy_price
                        ganancia_pct = (ganancia_por_unidad / buy_price) * 100 if buy_price > 0 else 0

                        if ganancia_pct > 1.0:
                            recomendacion = "COMPRAR"
                            color = "#00ff88"
                            mensaje = f"✅ **Recomendado COMPRAR** a ${buy_price:.2f} y vender a ${sell_price:.2f} en spot/P2P."
                            detalle = f"Ganancia potencial: ${ganancia_por_unidad:.2f} por unidad ({ganancia_pct:.2f}%)"
                        elif ganancia_pct < -1.0:
                            recomendacion = "VENDER"
                            color = "#ff4444"
                            mensaje = f"✅ **Recomendado VENDER** a ${sell_price:.2f} (actualmente esta por encima del precio de compra)."
                            detalle = f"Puedes vender ahora y recomprar cuando baje. Diferencia: ${abs(ganancia_por_unidad):.2f} por unidad ({abs(ganancia_pct):.2f}%)"
                        else:
                            recomendacion = "NEUTRO"
                            color = "#ffd700"
                            mensaje = f"⚠️ **Spread bajo ({ganancia_pct:.2f}%). No hay oportunidad clara.**"
                            detalle = "Espera a que el spread supere el 1% para obtener una ganancia significativa."

                        st.markdown(f"""
                        <div style="background-color: #1e2a3a; padding: 20px; border-radius: 10px; border-left: 4px solid {color};">
                            <h4 style="color: {color}; margin:0;">{mensaje}</h4>
                            <p style="color: #b0c4de; margin:5px 0 0 0;">{detalle}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        col_r1, col_r2, col_r3 = st.columns(3)
                        col_r1.metric("Precio Compra", f"${buy_price:.2f}")
                        col_r2.metric("Precio Venta", f"${sell_price:.2f}")
                        col_r3.metric("Ganancia por unidad", f"${ganancia_por_unidad:.2f}", 
                                      delta=f"{ganancia_pct:.2f}%" if abs(ganancia_pct) > 0 else None,
                                      delta_color="normal" if ganancia_pct > 0 else "inverse")
                        # ========== FIN RECOMENDACION ==========
                    else:
                        # No hay datos para esta moneda/fiat
                        st.warning(f"⚠️ No hay anuncios activos para **{asset_sel}/{fiat_sel}** en este momento.")
                        st.info("Prueba con otra moneda o fiat, o actualiza mas tarde.")
                else:
                    st.warning("No se obtuvieron datos P2P.")
            else:
                st.warning("No se pudo conectar con el servicio P2P.")
        except Exception as e:
            st.warning(f"Error al obtener datos P2P: {e}")

        st.divider()
        # ========== FIN SECCION P2P ==========
        # ========== FIN SECCION P2P ==========

        st.subheader("📊 Ganancias y Perdidas Realizadas")
        pnl_summary = fetch("/analytics/realized-pnl-summary")
        if pnl_summary:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("💰 Ganancias Realizadas", f"${pnl_summary.get('ganancias_realizadas', 0):,.2f}")
            col_b.metric("💸 Perdidas Realizadas", f"${pnl_summary.get('perdidas_realizadas', 0):,.2f}", delta_color="inverse")
            col_c.metric("📈 Neto Realizado", f"${pnl_summary.get('neto_realizado', 0):,.2f}",
                         delta=f"${pnl_summary.get('neto_realizado', 0):,.2f}" if pnl_summary.get('neto_realizado') >= 0 else f"-${abs(pnl_summary.get('neto_realizado', 0)):,.2f}",
                         delta_color="normal")
        else:
            st.info("No hay datos de ganancias/perdidas realizadas todavia.")

        st.subheader("📈 Evolucion de PnL Realizado (Ultimos 7 dias)")
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
                fig.update_layout(title="PnL Realizado por Dia", xaxis_title="Fecha", yaxis_title="PnL (USD)", height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de PnL para los ultimos 7 dias.")
        else:
            st.info("No se pudieron cargar los datos de PnL diario.")

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Distribucion del Portafolio")
            if distribucion:
                df_dist = pd.DataFrame(distribucion)
                fig = px.pie(df_dist, values="porcentaje", names="symbol", hole=0.4, title="Por Valor de Mercado")
                st.plotly_chart(fig, use_container_width=True)
        with col_right:
            st.subheader("Top Performers")
            if top:
                df_top = pd.DataFrame(top)
                fig = px.bar(df_top, x="symbol", y="roi", color="roi", color_continuous_scale="RdYlGn", title="ROI por Moneda")
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

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: CLIENTES (con precio promedio sin fee y PnL ajustado)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Clientes":
    st.title("👥 Gestion de Clientes (Criptomonedas)")
    st.markdown("""
    - **Costo Promedio (con fee)**: incluye comisiones prorrateadas (costo real).
    - **Precio Promedio (sin fee)**: promedio de los precios de compra sin comisiones.
    - **PnL FIFO Real**: calculado con FIFO y comisiones (ganancia/perdida real).
    - **PnL No Realizado (sin fee)**: basado en el precio promedio sin comisiones (lo que ves en el exchange).
    - **Los precios se actualizan automaticamente con los datos de Binance cada hora, o manualmente con los botones de abajo.**
    """)

    # ========== ACTUALIZAR TODOS ==========
    if st.button("🔄 Actualizar todos los precios desde Binance"):
        with st.spinner("Actualizando precios..."):
            clientes_actualizar = fetch("/clientes/")
            if clientes_actualizar:
                for c in clientes_actualizar:
                    precio_real = obtener_precio_real(c["symbol"])
                    if precio_real > 0:
                        resp = post(f"/clientes/{c['symbol']}/actualizar-precio", {"precio": precio_real})
                        if not resp:
                            st.error(f"Error actualizando {c['symbol']}")
                    else:
                        st.warning(f"No se pudo obtener precio para {c['symbol']}")
                st.success("¡Precios actualizados correctamente!")
                # Forzar recarga completa
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("No se pudieron obtener los clientes")

    # ========== OBTENER CLIENTES ==========
    clientes = fetch("/clientes/")
    if not clientes:
        st.warning("No hay clientes registrados. Crea uno nuevo en la pestana '➕ Nuevo Cliente'")
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

            # Interacciones de compra para precio promedio sin fee
            interacciones = fetch(f"/interacciones/cliente/{symbol}")
            compras = [i for i in interacciones if i.get("tipo") == "compra"] if interacciones else []
            suma_cantidad = sum(float(i["cantidad"]) for i in compras) if compras else 0
            suma_precio_cantidad = sum(float(i["cantidad"]) * float(i["precio_unitario"]) for i in compras) if compras else 0
            precio_promedio_sin_fee = suma_precio_cantidad / suma_cantidad if suma_cantidad > 0 else 0

            # FIFO (con fee)
            lotes_cliente = lotes_data.get(symbol, [])
            cantidad_restante_fifo = 0.0
            costo_total_fifo = 0.0
            for lote in lotes_cliente:
                cant = lote["cantidad_restante"]
                cantidad_restante_fifo += cant
                costo_total_fifo += cant * lote["precio_unitario"]

            valor_actual_fifo = cantidad_restante_fifo * precio_actual
            pnl_no_realizado_fifo = valor_actual_fifo - costo_total_fifo

            # PnL sin fee
            pnl_no_realizado_sin_fee = cantidad_total * (precio_actual - precio_promedio_sin_fee)

            costo_prom_con_fee = float(c.get("costo_promedio", 0))

            df_data.append({
                "symbol": symbol,
                "nombre": c.get("nombre", ""),
                "categoria": c.get("categoria", ""),
                "estado": c.get("estado", ""),
                "cantidad_total": cantidad_total,
                "precio_prom_sin_fee": precio_promedio_sin_fee,
                "costo_prom_con_fee": costo_prom_con_fee,
                "precio_actual": precio_actual,
                "valor_mercado": float(c.get("valor_mercado", 0)),
                "pnl_realizado": float(c.get("pnl_total", 0)),
                "roi_realizado_pct": float(c.get("roi_porcentaje", 0)),
                "pnl_fifo_no_realizado": pnl_no_realizado_fifo,
                "pnl_sin_fee_no_realizado": pnl_no_realizado_sin_fee,
                "roi_fifo_pct": (pnl_no_realizado_fifo / costo_total_fifo * 100) if costo_total_fifo > 0 else 0,
                "roi_sin_fee_pct": (pnl_no_realizado_sin_fee / (cantidad_total * precio_promedio_sin_fee) * 100) if cantidad_total > 0 and precio_promedio_sin_fee > 0 else 0,
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
            "precio_prom_sin_fee": st.column_config.NumberColumn("Precio Promedio (sin fee)", format="$%.8f", disabled=True),
            "costo_prom_con_fee": st.column_config.NumberColumn("Costo Promedio (con fee)", format="$%.8f", disabled=True),
            "precio_actual": st.column_config.NumberColumn("Precio Actual (USD)", format="$%.8f", disabled=True),
            "valor_mercado": st.column_config.NumberColumn("Valor Mercado (USD)", format="$%.2f", disabled=True),
            "pnl_realizado": st.column_config.NumberColumn("PnL Realizado (USD)", format="$%.2f", disabled=True),
            "roi_realizado_pct": st.column_config.NumberColumn("ROI Realizado %", format="%.2f%%", disabled=True),
            "pnl_fifo_no_realizado": st.column_config.NumberColumn("PnL FIFO Real (USD)", format="$%.2f"),
            "pnl_sin_fee_no_realizado": st.column_config.NumberColumn("PnL No Realizado (sin fee)", format="$%.2f"),
            "roi_fifo_pct": st.column_config.NumberColumn("ROI FIFO %", format="%.2f%%"),
            "roi_sin_fee_pct": st.column_config.NumberColumn("ROI sin fee %", format="%.2f%%"),
            "prioridad": st.column_config.NumberColumn("Prioridad", min_value=1, max_value=5, step=1),
            "tags": st.column_config.TextColumn("Tags"),
            "notas": st.column_config.TextColumn("Notas")
        }

        edited_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key="clientes_editor",
            disabled=["symbol", "precio_prom_sin_fee", "costo_prom_con_fee", "precio_actual", "valor_mercado", "pnl_realizado", "roi_realizado_pct", "pnl_fifo_no_realizado", "pnl_sin_fee_no_realizado", "roi_fifo_pct", "roi_sin_fee_pct"]
        )

        if st.button("Guardar cambios realizados"):
            for idx, row in edited_df.iterrows():
                original = df.iloc[idx]
                if not row.equals(original):
                    symbol = row["symbol"]
                    update_data = {}
                    for col in ["nombre", "categoria", "estado", "cantidad_total", "prioridad", "tags", "notas"]:
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

        # ========== ELIMINAR CLIENTE ==========
        st.divider()
        st.subheader("🗑️ Eliminar Cliente")
        col_del1, col_del2 = st.columns([3, 1])
        with col_del1:
            cliente_a_eliminar = st.selectbox(
                "Selecciona cliente a eliminar",
                [c["symbol"] for c in clientes] if clientes else [],
                key="cliente_eliminar"
            )
        with col_del2:
            if st.button("🗑️ Eliminar Cliente", type="primary"):
                if cliente_a_eliminar:
                    if st.checkbox(f"Confirmar eliminacion de {cliente_a_eliminar} (todos sus datos seran borrados)"):
                        resp = delete(f"/clientes/{cliente_a_eliminar}")
                        if resp:
                            st.success(f"Cliente {cliente_a_eliminar} eliminado exitosamente")
                            st.rerun()
                        else:
                            st.error("Error al eliminar cliente")
        # ======================================

        # ========== ACTUALIZAR PRECIO INDIVIDUAL (con validacion) ==========
        st.subheader("Actualizar Precio Individual y Ver Detalle FIFO")
        col_sel, col_btn = st.columns([3,1])
        with col_sel:
            selected_symbol = st.selectbox("Selecciona un cliente", [c["symbol"] for c in clientes] if clientes else [])
        with col_btn:
            if st.button("Actualizar precio desde Binance"):
                if selected_symbol:
                    precio_real = obtener_precio_real(selected_symbol)
                    if precio_real > 0:
                        with st.spinner(f"Actualizando precio de {selected_symbol}..."):
                            try:
                                r = requests.post(f"{API_URL}/clientes/{selected_symbol}/actualizar-precio", json={"precio": precio_real})
                                if r.status_code == 200:
                                    resp = r.json()
                                    nuevo_precio = resp.get("precio_actual", 0)
                                    st.success(f"✅ Precio de {selected_symbol} actualizado a ${nuevo_precio:.8f}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error {r.status_code}: {r.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ Excepcion: {e}")
                    else:
                        st.error("No se pudo obtener precio de Binance para este simbolo")

        # ========== CORREGIR CAPITAL MANUALMENTE ==========
        st.divider()
        st.subheader("🛠️ Corregir Capital Invertido Manualmente")
        st.info("Usa esta opcion si el sistema calculo mal el capital invertido historico y necesitas ajustarlo.")
        col_corr1, col_corr2, col_corr3 = st.columns([2, 2, 1])
        with col_corr1:
            sym_corregir = st.selectbox("Selecciona moneda a corregir", [c["symbol"] for c in clientes] if clientes else [], key="sym_corr")
        with col_corr2:
            nueva_inv = st.number_input("Nuevo Capital Invertido ($)", min_value=0.0, step=1.0, format="%.2f")
        with col_corr3:
            st.write("")
            st.write("")
            if st.button("Aplicar Correccion", type="primary"):
                if sym_corregir:
                    resp = post(f"/clientes/{sym_corregir}/corregir-inversion", {"nueva_inversion": nueva_inv})
                    if resp:
                        st.success(f"Capital de {sym_corregir} corregido a ${nueva_inv:.2f}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Error al aplicar la correccion.")

        # ========== MOSTRAR LOTES (FIFO) ==========
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
                st.dataframe(df_lotes, use_container_width=True)
            else:
                st.info("No hay lotes activos para este cliente.")

    # ========== NUEVO CLIENTE ==========
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

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: INTERACCIONES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Interacciones":
    st.title("💱 Registro de Interacciones (FIFO para ventas)")

    with st.form("nueva_interaccion"):
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Symbol del cliente").upper()
        with col2:
            tipo = st.selectbox("Tipo", ["compra", "venta", "staking", "unstaking", "dividendo", "airdrop"])
        exchange = st.text_input("Exchange", value="binance")
        cantidad = st.number_input("Cantidad", min_value=0.0, step=0.00000001, format="%.8f")
        precio = st.number_input("Precio unitario (USD)", min_value=0.0, step=0.00000001, format="%.8f")
        fee = st.number_input("Fee", min_value=0.0, step=0.00000001, format="%.8f")
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
                    st.write(f"${float(row.get('precio_unitario', 0)):.8f}")
                with col4:
                    st.write(f"${float(row.get('monto_usd', 0)):.2f}")
                with col5:
                    st.write(row.get("timestamp", "")[:16])
                with col6:
                    st.write(f"${float(row.get('pnl_realizado', 0)):.2f}")
                with col7:
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        if st.checkbox(f"Confirmar eliminacion de {row['tipo']} {row['cantidad']} @ ${row['precio_unitario']}", key=f"confirm_{row['id']}"):
                            resp = delete(f"/interacciones/{row['id']}")
                            if resp:
                                st.success(f"Interaccion {row['id']} eliminada")
                                st.rerun()
                st.divider()
        else:
            st.info("No hay interacciones para este cliente.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: OPORTUNIDADES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Oportunidades":
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
                    st.error("Debes ingresar un simbolo de cliente")
                elif symbol not in simbolos_clientes:
                    st.error(f"El cliente '{symbol}' no existe. Registralo primero en la seccion Clientes.")
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
            "Fecha Creacion": o.get("fecha_creacion", "")[:16] if o.get("fecha_creacion") else "",
            "Notas": o.get("notas_analisis", "")[:50]
        } for o in oportunidades])
        st.dataframe(df_opp, use_container_width=True)

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

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: TAREAS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Tareas":
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
            dias = st.number_input("Dias para completar", min_value=0, max_value=30, value=1)
            prioridad = st.slider("Prioridad (1=alta, 5=baja)", 1, 5, 2)
            submitted = st.form_submit_button("Crear Tarea")
            if submitted:
                if not symbol:
                    st.error("Debes ingresar un simbolo de cliente")
                elif symbol not in simbolos_clientes:
                    st.error(f"El cliente '{symbol}' no existe. Registralo primero en la seccion Clientes.")
                elif not descripcion:
                    st.error("La descripcion es obligatoria")
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
                        st.caption(f"Cliente ID: {cliente_id} | Limite: {t.get('fecha_limite', '')}")
                    else:
                        st.caption(f"Limite: {t.get('fecha_limite', '')}")
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
        st.success("No hay tareas pendientes. ¡Todo al dia! 🎉")

    with st.expander("📜 Ver tareas completadas (ultimas 10)"):
        with st.spinner("Cargando historial de tareas completadas..."):
            tareas_completadas = fetch("/tareas/completadas?limit=10")
            if tareas_completadas:
                if isinstance(tareas_completadas, list) and len(tareas_completadas) > 0:
                    df_completadas = pd.DataFrame([{
                        "ID": t["id"],
                        "Cliente ID": t.get("cliente_id", ""),
                        "Tipo": t.get("tipo_tarea", ""),
                        "Descripcion": t.get("descripcion", ""),
                        "Completada el": t.get("fecha_completada", "")[:16] if t.get("fecha_completada") else "Fecha no registrada"
                    } for t in tareas_completadas])
                    st.dataframe(df_completadas, use_container_width=True)
                else:
                    st.info("No hay tareas completadas para mostrar.")
            else:
                st.info("No se pudieron cargar las tareas completadas. Asegurate de que la API este corriendo.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: LOTES FIFO
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Lotes FIFO":
    st.title("📦 Lotes de Compra (FIFO)")
    st.info("Cada compra genera un lote. Las ventas consumen lotes desde el mas antiguo (FIFO).")

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
            st.dataframe(df_lotes, use_container_width=True)
            total_restante = df_lotes["Cantidad Restante"].sum()
            costo_total_restante = sum(df_lotes["Cantidad Restante"] * df_lotes["Precio Compra (incluye fee)"])
            st.metric("Cantidad total remanente", f"{total_restante:.8f}")
            st.metric("Costo promedio ponderado restante", f"${costo_total_restante/total_restante:.4f}" if total_restante>0 else "$0")
        else:
            st.write("No hay lotes para este cliente.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    st.title("📈 Analytics y Reportes")

    st.subheader("🔥 Heatmap: Rendimiento por Categoria (ROI %)")
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
                title="ROI Promedio por Categoria"
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=300, width=800)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de categorias aun. Registra clientes con categorias.")
    else:
        st.info("No se pudieron cargar los datos de rendimiento por categoria.")

    data = fetch("/dashboard/resumen")
    if data:
        resumen = data.get("resumen", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invertido", f"${resumen.get('total_invertido',0):,.2f}")
        col2.metric("Valor Mercado", f"${resumen.get('total_valor_mercado',0):,.2f}")
        col3.metric("PnL Total", f"${resumen.get('pnl_total',0):,.2f}")

    st.subheader("Distribucion del Portafolio")
    distribucion = fetch("/dashboard/resumen").get("distribucion",[]) if data else []
    if distribucion:
        df_dist = pd.DataFrame(distribucion)
        fig = px.pie(df_dist, values="porcentaje", names="symbol", title="Composicion Actual")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Evolucion de PnL Realizado (Ultimos 7 dias)")
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
            fig.update_layout(title="PnL Realizado por Dia", xaxis_title="Fecha", yaxis_title="PnL (USD)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de PnL para los ultimos 7 dias.")
    else:
        st.info("No se pudieron cargar los datos de PnL diario.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: MERCADO EN VIVO
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Mercado en Vivo":
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
            sentimiento = "🔴 Bajista / Preocupacion"
        else:
            sentimiento = "🔴 Muy bajista / Panico"

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
            st.metric("Maximo 24h", f"${ticker.get('high', 0):,.4f}")
            st.metric("Minimo 24h", f"${ticker.get('low', 0):,.4f}")
            st.metric("Volumen (24h)", f"{ticker.get('volume', 0):,.2f}")
        with detalle_col2:
            st.metric("Ask", f"${ticker.get('ask', 0):,.4f}")
            st.metric("Bid", f"${ticker.get('bid', 0):,.4f}")
            st.metric("Ultima actualizacion", ticker.get('timestamp', '')[:19])

        st.subheader("Grafico de Velas (OHLCV)")
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se pudieron obtener velas para este simbolo.")
    else:
        st.error("No se pudo obtener informacion del ticker. Intenta con otro simbolo.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: TENDENCIAS DE MERCADO (CoinGecko)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Tendencias":
    st.title("🔥 Tendencias de Mercado (CoinGecko)")
    st.markdown("Criptomonedas mas buscadas y con mayor tendencia actualmente.")

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
                    "Correlacion BTC": correlation,
                    "Logo": thumb,
                    "ID": token_id
                })
                progress_bar.progress((i + 1) / len(tendencias))

            df_trend = pd.DataFrame(df_list)
            if not df_trend.empty:
                display_cols = ["Token", "Nombre", "Score", "Market Cap Rank", "En Binance", "Cambio 24h (%)", "Tendencia", "Correlacion BTC"]
                st.dataframe(df_trend[display_cols], use_container_width=True)

                fig = px.bar(df_trend, x="Token", y="Score", color="Score",
                             color_continuous_scale="Blues", title="Score de Tendencia")
                st.plotly_chart(fig, use_container_width=True)

                fig2 = go.Figure()
                colors = ['green' if x > 0 else 'red' for x in df_trend["Cambio 24h (%)"]]
                fig2.add_trace(go.Bar(
                    x=df_trend["Token"],
                    y=df_trend["Cambio 24h (%)"],
                    marker_color=colors,
                    text=df_trend["Cambio 24h (%)"].apply(lambda x: f"{x:.2f}%"),
                    textposition='auto'
                ))
                fig2.update_layout(title="Variacion 24h por Token", xaxis_title="Token", yaxis_title="Cambio (%)")
                st.plotly_chart(fig2, use_container_width=True)

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
            st.error("No se pudieron obtener datos de tendencias. Intenta mas tarde.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: EVENTOS BINANCE (solo enlace manual)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Eventos Binance":
    st.title("📢 Eventos Binance - Launchpool, Megadrop y Nuevos Listados")
    st.markdown("""
    **⚠️ Actualizacion automatica desactivada** Debido a restricciones tecnicas (bloqueo de scraping por parte de Binance), esta seccion ya no intenta obtener eventos de forma automatica.

    Para estar al dia de los ultimos lanzamientos (Launchpool, Megadrop, nuevos listados), visita directamente la pagina oficial de anuncios:
    """)
    st.markdown(
        "[🔗 Abrir pagina de anuncios de Binance](https://www.binance.com/en/support/announcement/c-48?c=48&navId=48)",
        unsafe_allow_html=True
    )
    st.info("Puedes revisar manualmente los anuncios y luego registrar tus oportunidades o tareas en el CRM.")

    # Mostrar eventos antiguos si existen (por si quedaron en la BD)
    eventos = fetch("/binance-events?limit=10")
    if eventos and isinstance(eventos, list) and len(eventos) > 0:
        with st.expander("📦 Eventos anteriores (guardados en la base de datos)"):
            df_events = pd.DataFrame(eventos)
            if "detected_at" in df_events.columns:
                df_events["detected_at"] = pd.to_datetime(df_events["detected_at"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df_events[["title", "event_type", "detected_at", "url"]], use_container_width=True)

    with st.expander("ℹ️ ¿Por que ya no se actualizan automaticamente?"):
        st.markdown("""
        - Binance ha bloqueado el acceso automatizado a su feed RSS y a las paginas de anuncios (codigos 202/404/403).
        - Para evitar errores y mantener la estabilidad de la aplicacion, se ha optado por redirigir al usuario a la fuente oficial.
        - Si en el futuro Binance ofrece una API publica para eventos, se podra reactivar la automatizacion.
        """)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: ANALISIS Y TRADING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Analisis y Trading":
    st.title("📈 Analisis Tecnico e Historial de Trading")

    tab_analisis, tab_historial = st.tabs(["📊 Analisis Tecnico", "📜 Historial de Transacciones"])

    # ========== PESTANA 1: ANALISIS TECNICO ==========
    with tab_analisis:
        st.subheader("Analisis de Soportes y Resistencias")
        col1, col2 = st.columns(2)
        with col1:
            symbol_analisis = st.text_input("Simbolo de la moneda (ej: BTC, ETH, XRP)", value="BTC", key="analisis_symbol").upper()
        with col2:
            temporalidad = st.selectbox("Temporalidad", ["1H", "4H", "1D", "1S (Semana)", "1M (Mes)"], index=2, key="analisis_temporalidad")

        if st.button("Generar Analisis", key="analisis_btn"):
            if not symbol_analisis:
                st.error("Ingresa un simbolo de moneda valido")
            else:
                if temporalidad == "1H":
                    intervalo = "1h"
                    limite = 168
                    periodo_texto = "ultima semana (velas de 1 hora)"
                elif temporalidad == "4H":
                    intervalo = "4h"
                    limite = 42
                    periodo_texto = "ultima semana (velas de 4 horas)"
                elif temporalidad == "1D":
                    intervalo = "1d"
                    limite = 30
                    periodo_texto = "ultimo mes (velas diarias)"
                elif temporalidad == "1S (Semana)":
                    intervalo = "1w"
                    limite = 12
                    periodo_texto = "ultimos 3 meses (velas semanales)"
                else:  # "1M (Mes)"
                    intervalo = "1d"
                    limite = 30
                    periodo_texto = "ultimo mes (velas diarias)"

                with st.spinner(f"Obteniendo datos de {symbol_analisis} desde Binance ({periodo_texto})..."):
                    velas = obtener_velas_binance(symbol_analisis, interval=intervalo, limit=limite)
                    if velas and len(velas) >= 5:
                        soportes, resistencias = encontrar_soportes_resistencias(velas, num_niveles=3)
                        df_velas = pd.DataFrame(velas)
                        df_velas['timestamp'] = pd.to_datetime(df_velas['timestamp'], unit='ms')

                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=df_velas['timestamp'],
                            open=df_velas['open'],
                            high=df_velas['high'],
                            low=df_velas['low'],
                            close=df_velas['close'],
                            name='Precio'
                        ))
                        for i, s in enumerate(soportes):
                            fig.add_hline(y=s, line_dash="dash", line_color="green",
                                          annotation_text=f"Soporte {i+1} (${s:.2f})",
                                          annotation_position="bottom right")
                        for i, r in enumerate(resistencias):
                            fig.add_hline(y=r, line_dash="dash", line_color="red",
                                          annotation_text=f"Resistencia {i+1} (${r:.2f})",
                                          annotation_position="top right")
                        fig.update_layout(
                            title=f"{symbol_analisis}/USDT - {periodo_texto.capitalize()}",
                            xaxis_title="Fecha",
                            yaxis_title="Precio (USD)",
                            height=600,
                            template="plotly_dark"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        col_s, col_r = st.columns(2)
                        with col_s:
                            st.subheader("📉 Soportes detectados")
                            if soportes:
                                st.write(pd.DataFrame({"Soporte (USD)": [f"${s:.2f}" for s in soportes]}))
                            else:
                                st.info("No se detectaron soportes claros en el periodo.")
                        with col_r:
                            st.subheader("📈 Resistencias detectadas")
                            if resistencias:
                                st.write(pd.DataFrame({"Resistencia (USD)": [f"${r:.2f}" for r in resistencias]}))
                            else:
                                st.info("No se detectaron resistencias claras en el periodo.")
                    else:
                        st.error(f"No se pudieron obtener datos de {symbol_analisis}. Verifica el simbolo o intentalo mas tarde.")

    # ========== PESTANA 2: HISTORIAL DE TRANSACCIONES ==========
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
                    st.dataframe(df_hist, use_container_width=True)

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
                    st.info("No hay transacciones de compra/venta registradas todavia.")
            else:
                st.info("No hay clientes registrados aun.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINAS EXTERNAS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Noticias":
    mostrar_pagina_noticias()

elif page == "P2P Binance":
    mostrar_pagina_p2p()    

elif page == "Inversiones Deportivas":
    mostrar_pagina_deportes()    

# ═══════════════════════════════════════════════════════════════════════════════
# PAGINA: CONFIGURACION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Configuracion":
    st.title("⚙️ Configuracion")
    st.info("Configuracion de Exchange y alertas (simulada).")
    with st.form("exchange_config"):
        exchange = st.selectbox("Exchange", ["binance", "coinbase", "kraken", "bybit"])
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        st.form_submit_button("Guardar")

    st.divider()
    st.subheader("💾 Respaldo de Base de Datos")
    st.markdown("Descarga un respaldo completo de la base de datos (archivo .db).")
    if st.button("📥 Descargar respaldo de base de datos"):
        try:
            r = requests.get(f"{API_URL}/export-db")
            if r.status_code == 200:
                st.download_button(
                    label="💾 Descargar crypto_crm_backup.db",
                    data=r.content,
                    file_name="crypto_crm_backup.db",
                    mime="application/x-sqlite3"
                )
                st.success("Respaldo generado correctamente.")
            else:
                st.error(f"Error al exportar: {r.text}")
        except Exception as e:
            st.error(f"Error: {e}")
    st.info("Para restaurar un respaldo, reemplaza manualmente el archivo crypto_crm.db en la carpeta del proyecto y reinicia la aplicacion.")
