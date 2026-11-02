import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import math
from pathlib import Path

# 1. Configuración de página
st.set_page_config(page_title="Flujo Logístico GIRSU", layout="wide")

# 2. CSS para una interfaz limpia, sin scroll y profesional
st.markdown("""
<style>
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    h3 { margin-top: 0rem !important; margin-bottom: 0.5rem !important; font-size: 1.4rem !important; color: #1f2937; }
    
    /* Tarjetas de métricas abajo */
    [data-testid="stMetric"] { 
        padding: 5px 10px !important; 
        background-color: #f8fafc; 
        border-radius: 8px; 
        border: 1px solid #e2e8f0; 
        min-height: 60px !important;
    }
    [data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 700 !important; font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.8rem !important; }
    
    /* Sidebar compacto */
    [data-testid="stSidebar"] { min-width: 310px !important; max-width: 310px !important; }
    [data-testid="stSidebar"] [data-testid="stMetric"] { 
        padding: 2px 10px !important; min-height: 45px !important; margin-bottom: 2px !important;
        background-color: #ffffff; border: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 🚛 Flujo Logístico GIRSU - Área Metropolitana")

# 3. CARGA DE DATOS
base_path = Path(__file__).parent
archivo = base_path / "datos_logistica_27_nuevo_modelo_con_distancias.xlsx"

try:
    df_residuos = pd.read_excel(archivo, sheet_name="PROYECCION_RESIDUOS").dropna(how="all")
    df_infra = pd.read_excel(archivo, sheet_name="INFRAESTRUCTURA").dropna(how="all")
    df_escenarios = pd.read_excel(archivo, sheet_name="ESCENARIOS").dropna(how="all")
    df_dist = pd.read_excel(archivo, sheet_name="DISTANCIAS").dropna(how="all")
    df_distrib = pd.read_excel(archivo, sheet_name="DISTRIBUCION_INFRAESTRUCTURA").dropna(how="all")
    df_rellenos = pd.read_excel(archivo, sheet_name="FUTUROS_RELLENOS").dropna(how="all")

    # Limpieza
    for df in [df_residuos, df_infra, df_escenarios, df_dist, df_distrib, df_rellenos]:
        df.columns = df.columns.astype(str).str.strip()

    # Coordenadas
    df_infra["LATITUD"] = pd.to_numeric(df_infra["LATITUD"], errors="coerce")
    df_infra["LONGITUD"] = pd.to_numeric(df_infra["LONGITUD"], errors="coerce")
    df_rellenos["LATITUD"] = pd.to_numeric(df_rellenos["LATITUD"], errors="coerce")
    df_rellenos["LONGITUD"] = pd.to_numeric(df_rellenos["LONGITUD"], errors="coerce")

    df_residuos["TON_ACTUAL_DIA"] = pd.to_numeric(df_residuos["TON_ACTUAL_DIA"], errors="coerce").fillna(0)
    df_residuos["TON_PROYECTADA_800"] = pd.to_numeric(df_residuos["TON_PROYECTADA_800"], errors="coerce").fillna(0)

    df_dist["KM_LINEAL"] = pd.to_numeric(df_dist["KM_LINEAL"], errors="coerce")
    df_dist["FACTOR_RUTA"] = pd.to_numeric(df_dist["FACTOR_RUTA"], errors="coerce").fillna(1.25)
    df_dist["KM_OPERATIVO"] = pd.to_numeric(df_dist["KM_OPERATIVO"], errors="coerce")
    df_dist["KM_RUTA_REAL"] = pd.to_numeric(df_dist["KM_RUTA_REAL"], errors="coerce")
    df_dist["KM_USADO"] = df_dist["KM_RUTA_REAL"].fillna(df_dist["KM_OPERATIVO"]).fillna(df_dist["KM_LINEAL"] * df_dist["FACTOR_RUTA"])

    # Parámetros fijos
    capacidad_t = 30
    precio_litro = 1100.0
    cons_cargado = 0.52
    cons_vacio = 0.30

    # 4. SIDEBAR
    with st.sidebar:
        st.markdown("#### ⚙️ Configuración")
        
        escenario_sel = st.selectbox("Escenario operativo:", df_escenarios["ESCENARIO"].dropna().tolist())
        escenario_row = df_escenarios[df_escenarios["ESCENARIO"] == escenario_sel].iloc[0]
        es_actual = escenario_sel == "Actual 600"

        if es_actual:
            relleno_sel = "Actual Relleno Sanitario"
            relleno_id = "ET1" # Usamos ET1 como el relleno actual
        else:
            relleno_sel = st.selectbox("Ubicación Futuro Relleno:", df_rellenos["NOMBRE"].dropna().tolist())
            relleno_id = df_rellenos[df_rellenos["NOMBRE"] == relleno_sel]["ID_RELLENO"].iloc[0]

        st.markdown("---")
        
        # Variables del escenario
        generacion_total = float(escenario_row["GENERACION_TOTAL"])
        ton_relleno = float(escenario_row["TON_A_RELLENO"])
        ton_et = float(escenario_row["TON_A_ET"])
        ton_planta = float(escenario_row["TON_A_PLANTA"])
        
        # RESUMEN EN SIDEBAR
        st.markdown("#### 📊 Resumen")
        st.metric("Generación total", f"{generacion_total:.0f} t/día", border=True)
        st.metric("A Futuro RS", f"{ton_relleno:.0f} t/día", f"{ton_relleno/generacion_total:.0%}", border=True)
        st.metric("A ET", f"{ton_et:.0f} t/día", f"{ton_et/generacion_total:.0%}", border=True)
        st.metric("A Planta Energía", f"{ton_planta:.0f} t/día", f"{ton_planta/generacion_total:.0%}", border=True)
        st.metric("Valorización", f"{ton_planta/generacion_total:.1%}", border=True)

    # 5. CÁLCULO DE INDICADORES LOGÍSTICOS
    col_ton = "TON_ACTUAL_DIA" if generacion_total == 600 else "TON_PROYECTADA_800"
    df_origenes = df_residuos[["ORIGEN", col_ton]].copy()
    df_origenes.columns = ["ORIGEN", "TON_DIA"]
    df_origenes = df_origenes.dropna(subset=["ORIGEN"])
    df_origenes["TON_DIA"] = pd.to_numeric(df_origenes["TON_DIA"], errors="coerce").fillna(0)
    
    # Función auxiliar para buscar distancias
    def km_lookup(tipo_flujo, origen=None, destino=None, origen_id=None, destino_id=None):
        temp = df_dist[df_dist["TIPO_FLUJO"] == tipo_flujo].copy()
        if origen is not None: temp = temp[temp["ORIGEN"] == origen]
        if destino is not None: temp = temp[temp["DESTINO"] == destino]
        if origen_id is not None: temp = temp[temp["ORIGEN_ID"] == origen_id]
        if destino_id is not None: temp = temp[temp["DESTINO_ID"] == destino_id]
        if temp.empty: return 0.0
        return float(temp["KM_USADO"].iloc[0])

    # Cálculo simple para los KPIs de abajo
    if es_actual:
        km_directo = sum(r["TON_DIA"] * km_lookup("Origen → ET", origen=r["ORIGEN"], destino_id="ET1") for _, r in df_origenes.iterrows()) / max(df_origenes["TON_DIA"].sum(), 1)
    else:
        km_directo = sum(r["TON_DIA"] * km_lookup("Origen → Futuro RS", origen=r["ORIGEN"], destino_id=relleno_id) for _, r in df_origenes.iterrows()) / max(df_origenes["TON_DIA"].sum(), 1)

    viajes_dia = math.ceil(ton_relleno / capacidad_t) if ton_relleno > 0 else 0
    km_totales = (km_directo * 2) * viajes_dia
    costo_viaje = ((km_directo * cons_cargado) + (km_directo * cons_vacio)) * precio_litro
    costo_diario = costo_viaje * viajes_dia

    # 6. MAPA DE FLUJOS
    # Centramos el mapa en el área metropolitana
    m = folium.Map(location=[-31.63, -60.75], zoom_start=11, tiles="CartoDB positron", attr="CartoDB")

    # A. Dibujar Orígenes (Santa Fe, Santo Tomé, OA Metrop)
    origenes_coords = df_dist[["ORIGEN", "ORIGEN_LAT", "ORIGEN_LON"]].drop_duplicates()
    for _, o in origenes_coords.iterrows():
        folium.Marker(
            [o["ORIGEN_LAT"], o["ORIGEN_LON"]],
            icon=folium.DivIcon(html=f'''
                <div style="font-size: 12px; font-weight: bold; color: #0f172a; background: #e2e8f0; border-radius: 4px; padding: 4px 8px; border: 1px solid #94a3b8; transform: translate(-50%, -50%);">
                    🏙️ {o["ORIGEN"]}
                </div>
            ''')
        ).add_to(m)

    # B. Dibujar Infraestructura (ETs, Planta)
    df_infra_mapa = df_infra[~df_infra["ID"].astype(str).str.startswith("FRS")].copy()
    for _, r in df_infra_mapa.iterrows():
        if pd.isna(r["LATITUD"]): continue
        
        # Renombrar ET1 si es el escenario actual
        nombre = "Actual Relleno Sanitario" if (r["ID"] == "ET1" and es_actual) else r["NOMBRE"]
        color = "green" if str(r["TIPO"]).lower() == "planta" else "blue"
        icon = "bolt" if color == "green" else "truck"
        
        folium.Marker(
            [r["LATITUD"], r["LONGITUD"]],
            tooltip=nombre,
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(m)

    # C. Dibujar Futuro Relleno
    if not es_actual:
        rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
        folium.Marker(
            [rr["LATITUD"], rr["LONGITUD"]],
            tooltip=f"Futuro RS: {rr['NOMBRE']}",
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(m)

    # D. LÓGICA DE FLUJOS (Animaciones)
    if es_actual:
        # Todo va a ET1
        destino = df_infra[df_infra["ID"] == "ET1"].iloc[0]
        for _, o in origenes_coords.iterrows():
            AntPath(
                locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [destino["LATITUD"], destino["LONGITUD"]]],
                delay=800, color="#3b82f6", weight=4, opacity=0.8
            ).add_to(m)
            
    elif escenario_sel == "Futuro 800 - Alternativa 1":
        # Todo directo al Futuro RS
        rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
        for _, o in origenes_coords.iterrows():
            AntPath(
                locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [rr["LATITUD"], rr["LONGITUD"]]],
                delay=800, color="#ef4444", weight=4, opacity=0.8
            ).add_to(m)
            
    else:
        # Alternativas 2 y 3
        # 1. Flujo directo de Origenes al Futuro RS
        rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
        for _, o in origenes_coords.iterrows():
            AntPath(
                locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [rr["LATITUD"], rr["LONGITUD"]]],
                delay=800, color="#ef4444", weight=3, opacity=0.6
            ).add_to(m)
            
        # 2. Flujo de Origenes a ETs y de ETs al Futuro RS
        distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
        et_ids = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]["DESTINO_ID"].tolist()
        
        for et_id in et_ids:
            et = df_infra[df_infra["ID"] == et_id].iloc[0]
            # Origenes a ET
            for _, o in origenes_coords.iterrows():
                AntPath(
                    locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [et["LATITUD"], et["LONGITUD"]]],
                    delay=800, color="#3b82f6", weight=3, opacity=0.8
                ).add_to(m)
            # ET al Relleno
            AntPath(
                locations=[[et["LATITUD"], et["LONGITUD"]], [rr["LATITUD"], rr["LONGITUD"]]],
                delay=800, color="#ef4444", weight=4, opacity=0.9
            ).add_to(m)

        # 3. Flujo a Planta de Energía (Solo Alternativa 3)
        if escenario_sel == "Futuro 800 - Alternativa 3":
            planta = df_infra[df_infra["ID"] == "PE1"].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(
                    locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [planta["LATITUD"], planta["LONGITUD"]]],
                    delay=800, color="#10b981", weight=4, opacity=0.8
                ).add_to(m)

    # Capas GIS (WMS)
    wms_url = "https://aswe.santafe.gov.ar/idesf/wms"
    for layers, name in [
        ("areas_de_riesgo_hidrico", "🌊 Riesgo hídrico"),
        ("ma_otbn_2021", "🌳 Bosques nativos"),
        ("ind_produccion", "🌾 Productividad del suelo")
    ]:
        folium.raster_layers.WmsTileLayer(
            url=wms_url, layers=layers, name=name, fmt="image/png",
            transparent=True, overlay=True, control=True, show=False
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # 7. RENDERIZAR MAPA E INDICADORES
    st_folium(m, width="100%", height=480, key="mapa_flujos")

    st.markdown("### 🚚 Indicadores logísticos de la flota")
    
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    g1.metric("Km ida a RS", f"{km_directo:.1f} km", border=True)
    g2.metric("Viaje redondo", f"{km_directo*2:.1f} km", border=True)
    g3.metric("Viajes diarios", f"{viajes_dia}", border=True)
    g4.metric("Km totales diarios", f"{km_totales:,.0f} km", border=True)
    g5.metric("Costo/viaje", f"$ {costo_viaje:,.0f}", border=True)
    g6.metric("Costo diario", f"$ {costo_diario:,.0f}", border=True)

except Exception as e:
    st.error(f"Error en los datos: {e}")
