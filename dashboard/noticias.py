"""
Página de noticias cripto usando feeds RSS con headers realistas y respaldo manual.
"""
import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime

# Headers para simular un navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Lista de feeds (primero los más estables)
FEEDS = [
    {
        "url": "https://www.criptonoticias.com/feed/",
        "nombre": "CriptoNoticias",
        "dominio": "www.criptonoticias.com",
        "parser": "xml"
    },
    {
        "url": "https://www.diariobitcoin.com/feed/",
        "nombre": "DiarioBitcoin",
        "dominio": "www.diariobitcoin.com",
        "parser": "xml"
    },
    {
        "url": "https://es.cointelegraph.com/rss",
        "nombre": "Cointelegraph en Español",
        "dominio": "es.cointelegraph.com",
        "parser": "xml"
    }
]

def fetch_feed_with_retry(url, max_retries=2):
    """Intenta obtener el contenido del feed con reintentos."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                return response.text
            else:
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"Error al obtener {url}: {e}")
    return None

def parse_rss_xml(content):
    """Parsea XML RSS manualmente con ElementTree (fallback cuando feedparser falla)."""
    try:
        root = ET.fromstring(content)
        # Buscar items en diferentes namespaces
        items = []
        # Buscar elementos 'item' en todo el árbol
        for item in root.findall('.//item'):
            title = item.find('title')
            link = item.find('link')
            pubDate = item.find('pubDate')
            description = item.find('description')
            items.append({
                "title": title.text if title is not None else "Sin título",
                "link": link.text if link is not None else "#",
                "pubDate": pubDate.text if pubDate is not None else "",
                "description": description.text if description is not None else ""
            })
        return items
    except Exception as e:
        print(f"Error parseando XML: {e}")
        return []

def obtener_noticias_rss():
    """Obtiene noticias desde múltiples feeds RSS con reintentos y parsing manual."""
    for feed_info in FEEDS:
        contenido = fetch_feed_with_retry(feed_info["url"])
        if contenido:
            noticias = []
            # Intentar primero con feedparser (si está disponible)
            try:
                import feedparser
                feed = feedparser.parse(contenido)
                if feed.entries:
                    for entry in feed.entries[:20]:
                        noticias.append({
                            "titulo": entry.get("title", "Sin título"),
                            "descripcion": entry.get("summary", ""),
                            "fuente": feed_info["nombre"],
                            "url": entry.get("link", "#"),
                            "fecha": entry.get("published", ""),
                            "dominio": feed_info["dominio"]
                        })
            except ImportError:
                # Si feedparser no está instalado, usar parsing manual
                items = parse_rss_xml(contenido)
                for item in items[:20]:
                    noticias.append({
                        "titulo": item.get("title", "Sin título"),
                        "descripcion": item.get("description", ""),
                        "fuente": feed_info["nombre"],
                        "url": item.get("link", "#"),
                        "fecha": item.get("pubDate", ""),
                        "dominio": feed_info["dominio"]
                    })
            except Exception as e:
                # Fallback a parsing manual
                items = parse_rss_xml(contenido)
                for item in items[:20]:
                    noticias.append({
                        "titulo": item.get("title", "Sin título"),
                        "descripcion": item.get("description", ""),
                        "fuente": feed_info["nombre"],
                        "url": item.get("link", "#"),
                        "fecha": item.get("pubDate", ""),
                        "dominio": feed_info["dominio"]
                    })
            
            if noticias:
                # Limpiar descripciones de etiquetas HTML
                for n in noticias:
                    if n["descripcion"]:
                        import re
                        n["descripcion"] = re.sub(r'<[^>]+>', '', n["descripcion"])
                return noticias[:20]
    return []

def mostrar_pagina_noticias():
    st.title("📰 Noticias del mundo cripto")
    st.markdown("Fuentes: **CriptoNoticias, DiarioBitcoin, Cointelegraph en Español**")
    
    if st.button("🔄 Recargar noticias ahora", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Cargando últimas noticias..."):
        noticias = obtener_noticias_rss()
    
    if not noticias:
        st.warning("No se pudieron cargar noticias automáticamente. Puedes consultar las fuentes directamente:")
        # Mostrar enlaces manuales
        for feed in FEEDS:
            st.markdown(f"- [{feed['nombre']}]({feed['url']})")
        st.info("Es posible que el sitio esté bloqueando solicitudes automáticas. Intenta más tarde o usa los enlaces directos.")
        return
    
    for idx, noticia in enumerate(noticias):
        with st.expander(f"🔹 {noticia['titulo'][:100]}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{noticia['titulo']}**")
                if noticia['descripcion']:
                    st.write(noticia['descripcion'][:300] + "...")
                # Formatear fecha
                fecha_str = noticia['fecha']
                if fecha_str and len(fecha_str) > 16:
                    fecha_str = fecha_str[:16]
                st.caption(f"Fuente: {noticia['fuente']} | {fecha_str if fecha_str else 'Fecha desconocida'}")
                st.markdown(f"[Leer más]({noticia['url']})", unsafe_allow_html=True)
            with col2:
                try:
                    st.image(f"https://www.google.com/s2/favicons?domain={noticia['dominio']}", width=32)
                except:
                    pass
        st.divider()
    
    st.caption("Noticias obtenidas de múltiples fuentes. Si no ves contenido, usa el botón de recarga manual.")