import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import math
from pathlib import Path

# 1. Configuración de página
st.set_page_config(page_title="Dashboard de alternativas", layout="wide")

# 2. CSS (Forzando colores y eliminando TODOS los bordes)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Ocultar menús, footers y el botón Manage App de Streamlit */
    header { display: none !important; }
    footer { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stAppViewBlockContainer"] { padding-top: 0rem !important; }
    
    /* Forzar fondo blanco general para la app */
    .stApp { background-color: #f8fafc !important; }

    /* Eliminar todos los márgenes posibles de Streamlit */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin-top: 0rem !important;
        max-width: 100% !important;
    }

    /* --- BARRA SUPERIOR (Header Blanco Forzado) --- */
    .top-navbar {
        background-color: #ffffff !important;
        padding: 8px 25px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #e2e8f0;
        height: 65px; /* Header más fino */
        margin-bottom: 5px;
    }
    
    .main-title {
        color: #0f172a !important; /* Título Negro */
        font-size: 1.6rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
        min-width: 320px !important;
        max-width: 320px !important;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: white !important;
        border-radius: 8px;
    }
    
    .sidebar-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #334155;
    }
    .sidebar-title {
        color: #f8fafc !important;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; font-size: 0.8rem; color: #cbd5e1; }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; }

    /* --- ÁREA DEL MAPA Y KPIs --- */
    .content-padding {
        padding-left: 15px;
        padding-right: 15px;
        padding-top: 0px;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 5px 10px; /* Tarjetas más chatas */
        text-align: left;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .kpi-label { color: #64748b; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0px; }
    .kpi-value { color: #0f172a; font-size: 1.1rem; font-weight: 800; }
    .kpi-value-blue { color: #2563eb; font-size: 1.1rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# 3. BARRA SUPERIOR (Header)
logo_path = Path(__file__).parent / "data_encuentro.png"

st.markdown('<div class="top-navbar">', unsafe_allow_html=True)
col_logo, col_title = st.columns([1.5, 6])

with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=160) # Logo un poco más chico para ahorrar espacio
    else:
        # Respaldo
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 5px;">
            <svg style="width: 30px; height: 30px;" viewBox="0 0 24 24" fill="none" stroke="#c1121f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="2" x2="12" y2="22"></line>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
                <line x1="18" y1="6" x2="6" y2="18"></line>
            </svg>
            <span style="color: #c1121f; font-weight: 900; font-size: 1.5rem; letter-spacing: -1px; line-height: 0.9;">
                DATA<br><span style="font-size: 0.9rem; letter-spacing: 2px;">ENCUENTRO</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

with col_title:
    st.markdown("<h1 class='main-title'>DASHBOARD de alternativas</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 4. CARGA DE DATOS
base_path = Path(__file__).parent
archivo = base_path / "datos_logistica_27_nuevo_modelo_con_distancias.xlsx"

try:
    df_residuos = pd.read_excel(archivo, sheet_name="PROYECCION_RESIDUOS").dropna(how="all")
    df_infra = pd.read_excel(archivo, sheet_name="INFRAESTRUCTURA").dropna(how="all")
    df_escenarios = pd.read_excel(archivo, sheet_name="ESCENARIOS").dropna(how="all")
    df_dist = pd.read_excel(archivo, sheet_name="DISTANCIAS").dropna(how="all")
    df_distrib = pd.read_excel(archivo, sheet_name="DISTRIBUCION_INFRAESTRUCTURA").dropna(how="all")
    df_rellenos = pd.read_excel(archivo, sheet_name="FUTUROS_RELLENOS").dropna(how="all")

    for df in [df_residuos, df_infra, df_escenarios, df_dist, df_distrib, df_rellenos]:
        df.columns = df.columns.astype(str).str.strip()

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

    capacidad_t = 30
    precio_litro = 1100.0
    cons_cargado = 0.52
    cons_vacio = 0.30

    # 5. SIDEBAR
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-title">Configuración</div>
        <div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px; line-height: 1.3;">
            Seleccione el escenario y la ubicación para visualizar el flujo logístico.
        </div>
        """, unsafe_allow_html=True)
        
        escenario_sel = st.selectbox("Escenario Operativo", df_escenarios["ESCENARIO"].dropna().tolist())
        escenario_row = df_escenarios[df_escenarios["ESCENARIO"] == escenario_sel].iloc[0]
        es_actual = escenario_sel == "Actual 600"

        if es_actual:
            relleno_sel = "Actual Relleno Sanitario"
            relleno_id = "ET1"
            st.markdown(f'<div class="sidebar-card" style="text-align:center; padding:8px;"><b>Destino:</b><br>{relleno_sel}</div>', unsafe_allow_html=True)
        else:
            relleno_sel = st.selectbox("Futuro Relleno Sanitario", df_rellenos["NOMBRE"].dropna().tolist())
            relleno_id = df_rellenos[df_rellenos["NOMBRE"] == relleno_sel]["ID_RELLENO"].iloc[0]

        generacion_total = float(escenario_row["GENERACION_TOTAL"])
        ton_relleno = float(escenario_row["TON_A_RELLENO"])
        ton_et = float(escenario_row["TON_A_ET"])
        ton_planta = float(escenario_row["TON_A_PLANTA"])

        st.markdown(f"""
        <div class="sidebar-card" style="margin-top: 10px;">
            <div class="sidebar-title">Resumen de Flujo</div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 6px 0;">
                <span style="color:#94a3b8; font-size:0.8rem;">Generación Total</span>
                <span style="color:#f8fafc; font-weight:bold;">{generacion_total:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 6px 0;">
                <span style="color:#94a3b8; font-size:0.8rem;">A Futuro RS</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_relleno:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 6px 0;">
                <span style="color:#94a3b8; font-size:0.8rem;">A Estaciones (ET)</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_et:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 6px 0;">
                <span style="color:#94a3b8; font-size:0.8rem;">A Planta Energía</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_planta:.0f} t/día</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-card">
            <div class="sidebar-title">Leyenda</div>
            <div class="legend-item"><div class="legend-dot" style="background-color: #ef4444;"></div> Flujo Principal a Relleno</div>
            <div class="legend-item"><div class="legend-dot" style="background-color: #3b82f6;"></div> Flujo Secundario (Ciudad → ET)</div>
            <div class="legend-item"><div class="legend-dot" style="background-color: #10b981;"></div> Flujo a Planta Energía</div>
        </div>
        """, unsafe_allow_html=True)

    # 6. CÁLCULOS LOGÍSTICOS
    col_ton = "TON_ACTUAL_DIA" if generacion_total == 600 else "TON_PROYECTADA_800"
    df_origenes = df_residuos[["ORIGEN", col_ton]].copy()
    df_origenes.columns = ["ORIGEN", "TON_DIA"]
    df_origenes = df_origenes.dropna(subset=["ORIGEN"])
    df_origenes["TON_DIA"] = pd.to_numeric(df_origenes["TON_DIA"], errors="coerce").fillna(0)

    def km_lookup(tipo_flujo, origen=None, destino_id=None):
        temp = df_dist[df_dist["TIPO_FLUJO"] == tipo_flujo].copy()
        if origen is not None: temp = temp[temp["ORIGEN"] == origen]
        if destino_id is not None: temp = temp[temp["DESTINO_ID"] == destino_id]
        if temp.empty: return 0.0
        return float(temp["KM_USADO"].iloc[0])

    if es_actual:
        km_directo = sum(r["TON_DIA"] * km_lookup("Origen → ET", origen=r["ORIGEN"], destino_id="ET1") for _, r in df_origenes.iterrows()) / max(df_origenes["TON_DIA"].sum(), 1)
    else:
        km_directo = sum(r["TON_DIA"] * km_lookup("Origen → Futuro RS", origen=r["ORIGEN"], destino_id=relleno_id) for _, r in df_origenes.iterrows()) / max(df_origenes["TON_DIA"].sum(), 1)

    viajes_dia = math.ceil(ton_relleno / capacidad_t) if ton_relleno > 0 else 0
    km_totales = (km_directo * 2) * viajes_dia
    costo_viaje = ((km_directo * cons_cargado) + (km_directo * cons_vacio)) * precio_litro
    costo_diario = costo_viaje * viajes_dia

    # 7. ÁREA PRINCIPAL
    with st.container():
        st.markdown('<div class="content-padding">', unsafe_allow_html=True)
        
        # Mantener el estado del mapa
        if "map_center" not in st.session_state:
            st.session_state.map_center = [-31.63, -60.75]
        if "map_zoom" not in st.session_state:
            st.session_state.map_zoom = 12

        m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom, tiles="OpenStreetMap", attr="OpenStreetMap")

        centros_urbanos = {
            "Santa Fe": (-31.616772, -60.701032),
            "Santo Tomé": (-31.677154, -60.767621),
            "San José del Rincón": (-31.612126, -60.586906),
            "Recreo": (-31.493104, -60.731077),
            "Sauce Viejo": (-31.770770, -60.838399)
        }

        ciudad_a_et = {
            "Santa Fe": "ET1",
            "Santo Tomé": "ET2",
            "San José del Rincón": "ET4",
            "Recreo": "ET3",
            "Sauce Viejo": "ET2"
        }

        # A. Opciones de Relleno
        for _, rr in df_rellenos.iterrows():
            es_el_seleccionado = (rr["ID_RELLENO"] == relleno_id)
            color_icono = "red" if es_el_seleccionado else "gray"
            prefijo = "★ Futuro RS" if es_el_seleccionado else "Opción RS"
            
            folium.Marker(
                [rr["LATITUD"], rr["LONGITUD"]],
                tooltip=f"{prefijo}: {rr['NOMBRE']}",
                icon=folium.Icon(color=color_icono, icon="flag", prefix="fa")
            ).add_to(m)
            
            folium.Marker(
                [rr["LATITUD"], rr["LONGITUD"]],
                icon=folium.DivIcon(html=f'''
                    <div style="font-size: 11px; font-weight: bold; color: {'#ef4444' if es_el_seleccionado else '#64748b'}; background: rgba(255,255,255,0.9); padding: 2px 4px; border-radius: 4px; transform: translate(10px, -15px); white-space: nowrap; border: 1px solid {'#ef4444' if es_el_seleccionado else '#cbd5e1'};">
                        {rr["NOMBRE"]}
                    </div>
                ''')
            ).add_to(m)

        # B. Infraestructura (ETs sin Planta de Energía)
        nombres_et = {
            "ET1": "ET 1 - Actual Relleno",
            "ET2": "ET 2 - Santo Tomé",
            "ET3": "ET 3 - Recreo",
            "ET4": "ET 4 - Rincón"
        }
        df_infra_mapa = df_infra[~df_infra["ID"].astype(str).str.startswith("FRS") & (df_infra["ID"] != "PE1")].copy()
        
        for _, r in df_infra_mapa.iterrows():
            if pd.isna(r["LATITUD"]): continue
            nombre_mostrar = nombres_et.get(r["ID"], r["NOMBRE"])
            
            if r["ID"] == "ET1" and es_actual:
                nombre_mostrar = "Actual Relleno Sanitario (ET 1)"
                color = "red"
                icon = "flag"
            else:
                color = "blue"
                icon = "truck"
                
            folium.Marker([r["LATITUD"], r["LONGITUD"]], tooltip=nombre_mostrar, icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)
            
            folium.Marker(
                [r["LATITUD"], r["LONGITUD"]],
                icon=folium.DivIcon(html=f'''
                    <div style="font-size: 10px; font-weight: bold; color: #1e293b; background: rgba(255,255,255,0.9); padding: 2px 4px; border-radius: 4px; transform: translate(10px, -15px); white-space: nowrap; border: 1px solid #cbd5e1;">
                        {nombre_mostrar.split('-')[0].strip()}
                    </div>
                ''')
            ).add_to(m)

        # C. FLUJOS LOGÍSTICOS
        if es_actual:
            destino = df_infra[df_infra["ID"] == "ET1"].iloc[0]
            for ciudad, (lat, lon) in centros_urbanos.items():
                AntPath(locations=[[lat, lon], [destino["LATITUD"], destino["LONGITUD"]]], delay=800, color="#ef4444", weight=5, opacity=0.9).add_to(m)
                folium.CircleMarker([lat, lon], radius=6, color="#ef4444", fill=True, fill_opacity=0.8, tooltip=f"Origen: {ciudad}").add_to(m)
        
        elif escenario_sel == "Futuro 800 - Alternativa 1":
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            for ciudad, (lat, lon) in centros_urbanos.items():
                AntPath(locations=[[lat, lon], [rr["LATITUD"], rr["LONGITUD"]]], delay=800, color="#ef4444", weight=6, opacity=0.9).add_to(m)
                folium.CircleMarker([lat, lon], radius=6, color="#ef4444", fill=True, fill_opacity=0.8, tooltip=f"Origen: {ciudad}").add_to(m)

        else:
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
            ets_activas = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]["DESTINO_ID"].tolist()
            
            for ciudad, et_id in ciudad_a_et.items():
                if et_id not in ets_activas:
                    continue
                
                # Flujo Secundario
                lat_c, lon_c = centros_urbanos[ciudad]
                et = df_infra[df_infra["ID"] == et_id].iloc[0]
                AntPath(locations=[[lat_c, lon_c], [et["LATITUD"], et["LONGITUD"]]], delay=1200, color="#3b82f6", weight=3, opacity=0.6, dash_array="5, 5").add_to(m)
                folium.CircleMarker([lat_c, lon_c], radius=6, color="#3b82f6", fill=True, fill_opacity=0.8, tooltip=f"Origen: {ciudad}").add_to(m)
                
                # Flujo Principal
                AntPath(locations=[[et["LATITUD"], et["LONGITUD"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=800, color="#ef4444", weight=6, opacity=0.9).add_to(m)

            if escenario_sel == "Futuro 800 - Alternativa 3":
                planta = df_infra[df_infra["ID"] == "PE1"].iloc[0]
                for ciudad, (lat, lon) in centros_urbanos.items():
                    AntPath(locations=[[lat, lon], [planta["LATITUD"], planta["LONGITUD"]]], delay=800, color="#10b981", weight=4, opacity=0.8).add_to(m)

        # Capas WMS
        wms_url = "https://aswe.santafe.gov.ar/idesf/wms"
        for layers, name in [
            ("areas_de_riesgo_hidrico", "🌊 Riesgo hídrico"),
            ("ma_otbn_2021", "🌳 Bosques nativos"),
            ("ind_produccion", "🌾 Productividad del suelo")
        ]:
            folium.raster_layers.WmsTileLayer(url=wms_url, layers=layers, name=name, fmt="image/png", transparent=True, overlay=True, control=True, show=False).add_to(m)

        folium.LayerControl(collapsed=True, position='topright').add_to(m)
        
        # MAPA AJUSTADO A LA PANTALLA (Height=440)
        map_data = st_folium(m, width="100%", height=440, key="mapa_encuentro")

        if map_data and map_data.get("center"):
            st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
            st.session_state.map_zoom = map_data["zoom"]

        # KPIs Inferiores (Ajustados para no cortarse)
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Km ida a RS</div><div class="kpi-value">{km_directo:.1f} km</div></div>''', unsafe_allow_html=True)
        with k2: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Viaje Redondo</div><div class="kpi-value">{km_directo*2:.1f} km</div></div>''', unsafe_allow_html=True)
        with k3: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Viajes Diarios</div><div class="kpi-value">{viajes_dia}</div></div>''', unsafe_allow_html=True)
        with k4: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Km Totales / Día</div><div class="kpi-value">{km_totales:,.0f} km</div></div>''', unsafe_allow_html=True)
        with k5: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Costo / Viaje</div><div class="kpi-value">$ {costo_viaje:,.0f}</div></div>''', unsafe_allow_html=True)
        with k6: st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Costo Diario</div><div class="kpi-value-blue">$ {costo_diario:,.0f}</div></div>''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en los datos: {e}")
