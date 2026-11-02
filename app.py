import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import math
from pathlib import Path
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="Dashboard de alternativas", layout="wide")

# 2. CSS (Corregido para que el mapa se vea y con la estética pedida)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Reset y fuentes */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Fondo general claro para el área del mapa */
    .stApp { background-color: #f1f5f9; }

    /* Márgenes mínimos */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* --- BARRA SUPERIOR (Header) --- */
    .top-navbar {
        background-color: #0f172a;
        padding: 10px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .title-container {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .main-title {
        color: #f8fafc;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    /* Logo ENCUENTRO (fondo blanco para que resalte en el header oscuro) */
    .logo-box {
        background-color: white;
        padding: 5px 15px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* --- SIDEBAR (Panel Izquierdo) --- */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
        min-width: 330px !important;
        max-width: 330px !important;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: white !important;
        border-radius: 8px;
    }
    
    /* Tarjetas en Sidebar */
    .sidebar-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #334155;
    }
    .sidebar-title {
        color: #f8fafc !important;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    /* Leyenda */
    .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 0.85rem; color: #cbd5e1; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; }

    /* --- CONTENEDOR DEL MAPA Y KPIs --- */
    .content-padding {
        padding-left: 30px;
        padding-right: 30px;
    }

    /* KPIs Inferiores */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 15px;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-label { color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
    .kpi-value { color: #0f172a; font-size: 1.3rem; font-weight: 800; }
    .kpi-value-blue { color: #2563eb; font-size: 1.3rem; font-weight: 800; }

</style>
""", unsafe_allow_html=True)

# 3. BARRA SUPERIOR (Header)
now = datetime.now().strftime("%d-%b, %H:%M %p")
logo_path = Path(__file__).parent / "encuentro.jpeg"

# Usamos columnas de Streamlit para alinear el logo y el título
col_logo, col_title, col_status = st.columns([1, 4, 2])

with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=150)
    else:
        st.markdown("<div class='logo-box'><b>ENCUENTRO</b></div>", unsafe_allow_html=True)

with col_title:
    st.markdown("<h1 class='main-title'>DASHBOARD de alternativas</h1>", unsafe_allow_html=True)

with col_status:
    st.markdown(f"""
    <div style="text-align: right; color: #94a3b8; font-size: 0.85rem; padding-top: 15px;">
        <span style="color: #10b981; margin-right: 15px;">🟢 Estado: Óptimo</span>
        {now}
    </div>
    """, unsafe_allow_html=True)

# Separador visual
st.markdown("<hr style='border-color: #1e293b; margin-top: 0; margin-bottom: 20px;'>", unsafe_allow_html=True)


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
        <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 15px; line-height: 1.4;">
            Seleccione el escenario y la ubicación para visualizar el flujo logístico.
        </div>
        """, unsafe_allow_html=True)
        
        escenario_sel = st.selectbox("Escenario Operativo", df_escenarios["ESCENARIO"].dropna().tolist())
        escenario_row = df_escenarios[df_escenarios["ESCENARIO"] == escenario_sel].iloc[0]
        es_actual = escenario_sel == "Actual 600"

        if es_actual:
            relleno_sel = "Actual Relleno Sanitario"
            relleno_id = "ET1"
            st.markdown(f'<div class="sidebar-card" style="text-align:center; padding:10px;"><b>Destino:</b><br>{relleno_sel}</div>', unsafe_allow_html=True)
        else:
            relleno_sel = st.selectbox("Futuro Relleno Sanitario", df_rellenos["NOMBRE"].dropna().tolist())
            relleno_id = df_rellenos[df_rellenos["NOMBRE"] == relleno_sel]["ID_RELLENO"].iloc[0]

        generacion_total = float(escenario_row["GENERACION_TOTAL"])
        ton_relleno = float(escenario_row["TON_A_RELLENO"])
        ton_et = float(escenario_row["TON_A_ET"])
        ton_planta = float(escenario_row["TON_A_PLANTA"])

        st.markdown(f"""
        <div class="sidebar-card" style="margin-top: 15px;">
            <div class="sidebar-title">Resumen de Flujo</div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 8px 0;">
                <span style="color:#94a3b8; font-size:0.85rem;">Generación Total</span>
                <span style="color:#f8fafc; font-weight:bold;">{generacion_total:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 8px 0;">
                <span style="color:#94a3b8; font-size:0.85rem;">A Futuro RS</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_relleno:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding: 8px 0;">
                <span style="color:#94a3b8; font-size:0.85rem;">A Estaciones (ET)</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_et:.0f} t/día</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                <span style="color:#94a3b8; font-size:0.85rem;">A Planta Energía</span>
                <span style="color:#f8fafc; font-weight:bold;">{ton_planta:.0f} t/día</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-card">
            <div class="sidebar-title">Leyenda</div>
            <div class="legend-item"><div class="legend-dot" style="background-color: #3b82f6;"></div> Flujo Origen → ET</div>
            <div class="legend-item"><div class="legend-dot" style="background-color: #ef4444;"></div> Flujo a Relleno Sanitario</div>
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

    # 7. ÁREA PRINCIPAL (Mapa y KPIs)
    # Envolvemos el mapa en un contenedor con padding para que no quede pegado a los bordes
    with st.container():
        st.markdown('<div class="content-padding">', unsafe_allow_html=True)
        
        m = folium.Map(location=[-31.63, -60.75], zoom_start=11, tiles="CartoDB positron", attr="CartoDB")

        # Orígenes
        origenes_coords = df_dist[["ORIGEN", "ORIGEN_LAT", "ORIGEN_LON"]].drop_duplicates()
        for _, o in origenes_coords.iterrows():
            folium.Marker(
                [o["ORIGEN_LAT"], o["ORIGEN_LON"]],
                icon=folium.DivIcon(html=f'''
                    <div style="font-size: 12px; font-weight: 700; color: #0f172a; background: #e2e8f0; border-radius: 4px; padding: 4px 8px; border: 1px solid #94a3b8; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transform: translate(-50%, -50%);">
                        🏙️ {o["ORIGEN"]}
                    </div>
                ''')
            ).add_to(m)

        # Infraestructura
        df_infra_mapa = df_infra[~df_infra["ID"].astype(str).str.startswith("FRS")].copy()
        for _, r in df_infra_mapa.iterrows():
            if pd.isna(r["LATITUD"]): continue
            nombre = "Actual Relleno Sanitario" if (r["ID"] == "ET1" and es_actual) else r["NOMBRE"]
            color = "green" if str(r["TIPO"]).lower() == "planta" else "blue"
            icon = "bolt" if color == "green" else "truck"
            folium.Marker([r["LATITUD"], r["LONGITUD"]], tooltip=nombre, icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)

        # Futuro Relleno
        if not es_actual:
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            folium.Marker([rr["LATITUD"], rr["LONGITUD"]], tooltip=f"Futuro RS: {rr['NOMBRE']}", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)

        # Flujos
        if es_actual:
            destino = df_infra[df_infra["ID"] == "ET1"].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [destino["LATITUD"], destino["LONGITUD"]]], delay=800, color="#3b82f6", weight=5, opacity=0.8).add_to(m)
        elif escenario_sel == "Futuro 800 - Alternativa 1":
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=800, color="#ef4444", weight=5, opacity=0.8).add_to(m)
        else:
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=800, color="#ef4444", weight=4, opacity=0.6).add_to(m)
                
            distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
            et_ids = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]["DESTINO_ID"].tolist()
            for et_id in et_ids:
                et = df_infra[df_infra["ID"] == et_id].iloc[0]
                for _, o in origenes_coords.iterrows():
                    AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [et["LATITUD"], et["LONGITUD"]]], delay=800, color="#3b82f6", weight=4, opacity=0.8).add_to(m)
                AntPath(locations=[[et["LATITUD"], et["LONGITUD"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=800, color="#ef4444", weight=5, opacity=0.9).add_to(m)

            if escenario_sel == "Futuro 800 - Alternativa 3":
                planta = df_infra[df_infra["ID"] == "PE1"].iloc[0]
                for _, o in origenes_coords.iterrows():
                    AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [planta["LATITUD"], planta["LONGITUD"]]], delay=800, color="#10b981", weight=5, opacity=0.8).add_to(m)

        # Capas WMS
        wms_url = "https://aswe.santafe.gov.ar/idesf/wms"
        for layers, name in [
            ("areas_de_riesgo_hidrico", "🌊 Riesgo hídrico"),
            ("ma_otbn_2021", "🌳 Bosques nativos"),
            ("ind_produccion", "🌾 Productividad del suelo")
        ]:
            folium.raster_layers.WmsTileLayer(url=wms_url, layers=layers, name=name, fmt="image/png", transparent=True, overlay=True, control=True, show=False).add_to(m)

        folium.LayerControl(collapsed=True, position='topright').add_to(m)

        # Renderizar Mapa
        st_folium(m, width="100%", height=450, key="mapa_encuentro")

        # KPIs Inferiores
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
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
