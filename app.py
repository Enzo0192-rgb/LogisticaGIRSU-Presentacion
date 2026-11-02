import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Configuración ancha
st.set_page_config(layout="wide", page_title="Dashboard de alternativas")

# 2. CSS para eliminar márgenes y forzar que todo quepa en una pantalla
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        h3 {
            margin-top: 0rem !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Título pequeño
st.markdown("### Dashboard de alternativas")

# 4. BARRA LATERAL (Controles)
with st.sidebar:
    st.markdown("#### 📍 Escenario operativo")
    escenario = st.selectbox(
        "Seleccionar escenario:",
        ["Actual 600", "Futuro 800 - Alternativa 1", "Futuro 800 - Alternativa 2", "Futuro 800 - Alternativa 3"],
        label_visibility="collapsed"
    )
    
    st.markdown("#### 🏞️ Futuro Relleno Sanitario")
    ubicacion = st.selectbox(
        "Seleccionar ubicación:",
        ["Colonia San José", "Empalme San Carlos", "Sauce Viejo"],
        label_visibility="collapsed"
    )

# 5. MAPA
# --- REEMPLAZA ESTA PARTE CON TU CÓDIGO REAL DE FOLIUM ---
m = folium.Map(location=[-31.6, -60.7], zoom_start=11, control_scale=True)

# Capa 1
fg_agua = folium.FeatureGroup(name="🌊 Riesgo hídrico")
folium.Marker([-31.61, -60.71], popup="Zona Riesgo Hídrico").add_to(fg_agua)
fg_agua.add_to(m)

# Capa 2
fg_bosques = folium.FeatureGroup(name="🌳 Bosques nativos")
folium.Marker([-31.65, -60.65], popup="Bosque Nativo").add_to(fg_bosques)
fg_bosques.add_to(m)

# Capa 3
fg_suelo = folium.FeatureGroup(name="🌾 Productividad del suelo")
folium.Marker([-31.58, -60.68], popup="Suelo Productivo").add_to(fg_suelo)
fg_suelo.add_to(m)

# Capa 4: Ubicaciones
fg_ubicaciones = folium.FeatureGroup(name="📍 Ubicaciones RS")
folium.Marker([-31.63, -60.72], popup=ubicacion, icon=folium.Icon(color="red")).add_to(fg_ubicaciones)
fg_ubicaciones.add_to(m)

# Control de capas (collapsed=True para que ocupe poco espacio)
folium.LayerControl(collapsed=True).add_to(m) 
# ---------------------------------------------------------

# Renderizar mapa (Height fijado para que quepa en pantalla)
st_folium(m, width="100%", height=380, use_container_width=True)

# 6. RESÚMENES DEBAJO DEL MAPA
st.markdown("### 📊 Resumen del escenario seleccionado")

with st.container(horizontal=True):
    st.metric("Generación total", "800 t/día", border=True)
    st.metric("A Futuro RS", "500 t/día", "↑ 62.5%", border=True)
    st.metric("A ET", "300 t/día", "↑ 37.5%", border=True)
    st.metric("A Planta Energía", "0 t/día", "↑ 0.0%", border=True)
    st.metric("Valorización energética", "0.0%", border=True)

st.markdown("### 🚚 Indicadores logísticos estimados")

col_log1, col_log2, col_destino = st.columns([1.2, 1.2, 1])

with col_log1:
    with st.container(horizontal=True):
        st.metric("Km ida batea", "18.1 km", border=True)
        st.metric("Viaje redondo", "36.1 km", border=True)
        st.metric("Viajes diarios", "17", border=True)

with col_log2:
    with st.container(horizontal=True):
        st.metric("Km totales diarios", "614 km", border=True)
        st.metric("Costo/viaje", "$ 16,284", border=True)
        st.metric("Costo diario", "$ 276,826", border=True)

with col_destino:
    st.markdown("**📍 Destino seleccionado**")
    st.success(f"Futuro Relleno Sanitario: **{ubicacion}**")
    
