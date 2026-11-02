import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import math
from pathlib import Path

# 1. Configuración de página
st.set_page_config(page_title="Dashboard de alternativas", layout="wide")

# 2. CSS para compactar y evitar el scroll
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    h3 { margin-top: 0rem !important; margin-bottom: 0.5rem !important; font-size: 1.4rem !important; }
    /* Estilo para los cuadros de métricas */
    [data-testid="stMetric"] { 
        padding: 10px 15px !important; 
        background-color: #f0f2f6; 
        border-radius: 10px; 
        border: 1px solid #d1d5db; 
    }
    [data-testid="stMetricValue"] { color: #1a1a1a !important; font-weight: bold !important; font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] { color: #4a4a4a !important; font-size: 0.9rem !important; }
    /* Compactar el sidebar */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("### Dashboard de alternativas")

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

    for col in ["NOMBRE", "DESTINO"]:
        if col in df_infra.columns:
            df_infra[col] = df_infra[col].replace({"Planta de Energía - Actual RS": "Planta de Energía", "Planta de Energia - Actual RS": "Planta de Energía", "Planta Energia - Actual RS": "Planta de Energía"})
        if col in df_distrib.columns:
            df_distrib[col] = df_distrib[col].replace({"Planta de Energía - Actual RS": "Planta de Energía", "Planta de Energia - Actual RS": "Planta de Energía", "Planta Energia - Actual RS": "Planta de Energía"})

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
    df_dist["KM_ESTIMADO"] = df_dist["KM_LINEAL"] * df_dist["FACTOR_RUTA"]
    df_dist["KM_USADO"] = df_dist["KM_RUTA_REAL"].fillna(df_dist["KM_OPERATIVO"]).fillna(df_dist["KM_ESTIMADO"])

    # 4. SIDEBAR (Controles + Resumen apilado)
    with st.sidebar:
        st.markdown("#### 📍 Escenario operativo")
        escenarios = df_escenarios["ESCENARIO"].dropna().tolist()
        escenario_sel = st.selectbox("Seleccionar escenario:", escenarios, label_visibility="collapsed")
        escenario_row = df_escenarios[df_escenarios["ESCENARIO"] == escenario_sel].iloc[0]
        es_actual = escenario_sel == "Actual 600"

        st.markdown("#### 🗺️ Futuro Relleno Sanitario")
        if es_actual:
            relleno_sel = "Actual Relleno Sanitario"
            relleno_id = None
            st.info("Escenario actual.")
        else:
            relleno_sel = st.selectbox("Seleccionar ubicación:", df_rellenos["NOMBRE"].dropna().tolist(), label_visibility="collapsed")
            relleno_id = df_rellenos[df_rellenos["NOMBRE"] == relleno_sel]["ID_RELLENO"].iloc[0]

        st.markdown("---")
        
        # CÁLCULOS DEL ESCENARIO (Para mostrar en el sidebar)
        generacion_total = float(escenario_row["GENERACION_TOTAL"])
        ton_relleno = float(escenario_row["TON_A_RELLENO"])
        ton_et = float(escenario_row["TON_A_ET"])
        ton_planta = float(escenario_row["TON_A_PLANTA"])
        porcentaje_relleno = ton_relleno / generacion_total if generacion_total else 0
        porcentaje_et = ton_et / generacion_total if generacion_total else 0
        porcentaje_planta = ton_planta / generacion_total if generacion_total else 0
        porcentaje_valorizacion = porcentaje_planta

        # RESUMEN APILADO AQUÍ
        st.markdown("#### 📊 Resumen del escenario")
        st.metric("Generación total", f"{generacion_total:.0f} t/día", border=True)
        st.metric("A Futuro RS", f"{ton_relleno:.0f} t/día", f"{porcentaje_relleno:.1%}", border=True)
        st.metric("A ET", f"{ton_et:.0f} t/día", f"{porcentaje_et:.1%}", border=True)
        st.metric("A Planta Energía", f"{ton_planta:.0f} t/día", f"{porcentaje_planta:.1%}", border=True)
        st.metric("Valorización energética", f"{porcentaje_valorizacion:.1%}", border=True)
        
        st.markdown("---")
        st.markdown("#### ⚙️ Parámetros")
        capacidad_t = st.selectbox("Capacidad batea (TN):", [30, 25, 20], label_visibility="collapsed")
        precio_litro = st.number_input("Precio gasoil ($):", value=1100.0, label_visibility="collapsed")
        cons_cargado = st.number_input("Consumo cargado (L/km):", value=0.52, label_visibility="collapsed")
        cons_vacio = st.number_input("Consumo vacío (L/km):", value=0.30, label_visibility="collapsed")
        
        mostrar_rutas = st.checkbox("Mostrar líneas de flujo", value=True)
        mostrar_radios = st.checkbox("Mostrar radios", value=False)

    # 5. CÁLCULOS LOGÍSTICOS
    col_ton = "TON_ACTUAL_DIA" if generacion_total == 600 else "TON_PROYECTADA_800"
    df_origenes = df_residuos[["ORIGEN", col_ton]].copy()
    df_origenes.columns = ["ORIGEN", "TON_DIA"]
    df_origenes = df_origenes.dropna(subset=["ORIGEN"])
    df_origenes["TON_DIA"] = pd.to_numeric(df_origenes["TON_DIA"], errors="coerce").fillna(0)

    def km_lookup(tipo_flujo, origen=None, destino=None, origen_id=None, destino_id=None):
        temp = df_dist[df_dist["TIPO_FLUJO"] == tipo_flujo].copy()
        if origen is not None: temp = temp[temp["ORIGEN"] == origen]
        if destino is not None: temp = temp[temp["DESTINO"] == destino]
        if origen_id is not None: temp = temp[temp["ORIGEN_ID"] == origen_id]
        if destino_id is not None: temp = temp[temp["DESTINO_ID"] == destino_id]
        if temp.empty: return 0.0
        return float(temp["KM_USADO"].iloc[0])

    def weighted_km_direct_to_relleno():
        if es_actual:
            total = 0
            for _, r in df_origenes.iterrows():
                km = km_lookup("Origen → ET", origen=r["ORIGEN"], destino_id="ET1")
                total += r["TON_DIA"] * km
            return total / max(df_origenes["TON_DIA"].sum(), 1)
        total = 0
        for _, r in df_origenes.iterrows():
            km = km_lookup("Origen → Futuro RS", origen=r["ORIGEN"], destino_id=relleno_id)
            total += r["TON_DIA"] * km
        return total / max(df_origenes["TON_DIA"].sum(), 1)

    def km_promedio_origen_a_et():
        distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
        distrib_esc = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]
        if distrib_esc.empty: return 0
        total_ton_km = 0
        total_ton = 0
        for _, dest in distrib_esc.iterrows():
            destino_id = dest["DESTINO_ID"]
            ton_destino = float(dest["TON_DIA"])
            for _, origen in df_origenes.iterrows():
                proporcion = origen["TON_DIA"] / max(df_origenes["TON_DIA"].sum(), 1)
                ton_asignada = ton_destino * proporcion
                km = km_lookup("Origen → ET", origen=origen["ORIGEN"], destino_id=destino_id)
                total_ton_km += ton_asignada * km
                total_ton += ton_asignada
        return total_ton_km / max(total_ton, 1)

    def km_promedio_et_a_relleno():
        if es_actual or relleno_id is None: return 0
        distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
        distrib_esc = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]
        if distrib_esc.empty: return 0
        total_ton_km = 0
        total_ton = 0
        for _, dest in distrib_esc.iterrows():
            origen_id = dest["DESTINO_ID"]
            ton_destino = float(dest["TON_DIA"])
            km = km_lookup("ET → Futuro RS", origen_id=origen_id, destino_id=relleno_id)
            total_ton_km += ton_destino * km
            total_ton += ton_destino
        return total_ton_km / max(total_ton, 1)

    km_directo = weighted_km_direct_to_relleno()
    km_origen_et = km_promedio_origen_a_et()
    km_et_relleno = km_promedio_et_a_relleno()

    km_promedio_ponderado = 0
    if es_actual or escenario_sel == "Futuro 800 - Alternativa 1":
        km_promedio_ponderado = km_directo
    elif escenario_sel == "Futuro 800 - Alternativa 2":
        km_promedio_ponderado = ((ton_relleno * km_directo) + (ton_et * (km_origen_et + km_et_relleno))) / generacion_total
    elif escenario_sel == "Futuro 800 - Alternativa 3":
        km_planta = 0
        for _, origen in df_origenes.iterrows():
            km = km_lookup("Origen → Planta Energía", origen=origen["ORIGEN"], destino_id="PE1")
            km_planta += origen["TON_DIA"] * km
        km_planta = km_planta / max(df_origenes["TON_DIA"].sum(), 1)
        km_promedio_ponderado = ((ton_relleno * km_directo) + (ton_et * (km_origen_et + km_et_relleno)) + (ton_planta * km_planta)) / generacion_total

    toneladas_batea = ton_relleno
    km_batea_ida = km_directo
    distancia_viaje_redondo = km_batea_ida * 2
    viajes_dia = math.ceil(toneladas_batea / capacidad_t) if toneladas_batea > 0 else 0
    litros_por_viaje = km_batea_ida * cons_cargado + km_batea_ida * cons_vacio
    costo_por_viaje = litros_por_viaje * precio_litro
    km_totales_dia = distancia_viaje_redondo * viajes_dia
    costo_total_dia = costo_por_viaje * viajes_dia

    # 6. MAPA (Área central)
    if not es_actual:
        rr_center = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
        map_center = [rr_center["LATITUD"], rr_center["LONGITUD"]]
    else:
        map_center = [-31.62, -60.75]

    m = folium.Map(location=map_center, zoom_start=11, tiles="OpenStreetMap", attr="OpenStreetMap")

    def agregar_etiqueta_mapa(lat, lon, texto):
        folium.Marker([lat, lon], icon=folium.DivIcon(html=f'<div style="font-size: 11px; font-weight: 700; color: #1f2937; background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(31, 41, 55, 0.25); border-radius: 6px; padding: 2px 5px; white-space: nowrap; box-shadow: 0 1px 4px rgba(0,0,0,0.25); transform: translate(15px, -10px);">{texto}</div>')).add_to(m)

    if mostrar_radios:
        centro = df_infra[df_infra["ID"] == "ET1"].iloc[0]
        for radio, color in [(20000, "blue"), (35000, "orange"), (50000, "red")]:
            folium.Circle([centro["LATITUD"], centro["LONGITUD"]], radius=radio, color=color, fill=True, fill_opacity=0.06).add_to(m)

    df_infra_mapa = df_infra[~df_infra["ID"].astype(str).str.startswith("FRS")].copy()
    for _, r in df_infra_mapa.iterrows():
        if pd.isna(r["LATITUD"]) or pd.isna(r["LONGITUD"]): continue
        color = "green" if str(r["TIPO"]).lower() == "planta" else "blue"
        icon = "bolt" if color == "green" else "truck"
        folium.Marker([r["LATITUD"], r["LONGITUD"]], tooltip=f"{r['ID']} - {r['NOMBRE']}", popup=f"{r['NOMBRE']}<br>Tipo: {r['TIPO']}<br>Capacidad: {r['CAPACIDAD_TN_DIA']} t/día", icon=folium.Icon(color=color, icon=icon, prefix="fa")).add_to(m)
        agregar_etiqueta_mapa(r["LATITUD"], r["LONGITUD"], r["NOMBRE"])

    if not es_actual:
        rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
        folium.Marker([rr["LATITUD"], rr["LONGITUD"]], tooltip=f"Futuro RS - {rr['NOMBRE']}", popup=f"Futuro Relleno Sanitario<br>{rr['NOMBRE']}", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)
        agregar_etiqueta_mapa(rr["LATITUD"], rr["LONGITUD"], rr["NOMBRE"])

    if mostrar_rutas:
        origenes_coords = df_dist[df_dist["TIPO_FLUJO"] == "Origen → Futuro RS"][["ORIGEN", "ORIGEN_LAT", "ORIGEN_LON"]].drop_duplicates()
        if es_actual:
            destino = df_infra[df_infra["ID"] == "ET1"].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [destino["LATITUD"], destino["LONGITUD"]]], delay=1000, color="blue", weight=4).add_to(m)
        elif escenario_sel == "Futuro 800 - Alternativa 1":
            rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
            for _, o in origenes_coords.iterrows():
                AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=1000, color="red", weight=4).add_to(m)
        else:
            distrib_esc = df_distrib[df_distrib["ESCENARIO"] == escenario_sel]
            et_ids = distrib_esc[distrib_esc["DESTINO_ID"].astype(str).str.startswith("ET")]["DESTINO_ID"].tolist()
            for et_id in et_ids:
                et = df_infra[df_infra["ID"] == et_id].iloc[0]
                for _, o in origenes_coords.iterrows():
                    AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [et["LATITUD"], et["LONGITUD"]]], delay=1000, color="blue", weight=3).add_to(m)
                rr = df_rellenos[df_rellenos["ID_RELLENO"] == relleno_id].iloc[0]
                AntPath(locations=[[et["LATITUD"], et["LONGITUD"]], [rr["LATITUD"], rr["LONGITUD"]]], delay=1000, color="red", weight=5).add_to(m)
            if escenario_sel == "Futuro 800 - Alternativa 3":
                planta = df_infra[df_infra["ID"] == "PE1"].iloc[0]
                for _, o in origenes_coords.iterrows():
                    AntPath(locations=[[o["ORIGEN_LAT"], o["ORIGEN_LON"]], [planta["LATITUD"], planta["LONGITUD"]]], delay=1000, color="green", weight=4).add_to(m)

    # CAPAS WMS SANTA FE
    wms_url = "https://aswe.santafe.gov.ar/idesf/wms"
    capas_wms = [
        {"layers": "areas_de_riesgo_hidrico", "name": "🌊 Riesgo hídrico"},
        {"layers": "ma_otbn_2021", "name": "🌳 Bosques nativos"},
        {"layers": "ind_produccion", "name": "🌾 Productividad del suelo"},
    ]
    for capa in capas_wms:
        folium.raster_layers.WmsTileLayer(url=wms_url, layers=capa["layers"], name=capa["name"], fmt="image/png", transparent=True, overlay=True, control=True, show=False).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Renderizar Mapa (Altura ajustada para que quepa la pantalla)
    st_folium(m, width="100%", height=480, key="mapa_modelo_nuevo")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # 7. INDICADORES LOGÍSTICOS (Debajo del mapa, simétricos)
    st.markdown("### 🚚 Indicadores logísticos estimados")
    
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    g1.metric("Km ida batea", f"{km_batea_ida:.1f} km", border=True)
    g2.metric("Viaje redondo", f"{distancia_viaje_redondo:.1f} km", border=True)
    g3.metric("Viajes diarios", f"{viajes_dia}", border=True)
    g4.metric("Km totales diarios", f"{km_totales_dia:,.0f} km", border=True)
    g5.metric("Costo/viaje", f"$ {costo_por_viaje:,.0f}", border=True)
    g6.metric("Costo diario", f"$ {costo_total_dia:,.0f}", border=True)

except Exception as e:
    st.error(f"Hubo un inconveniente con los datos: {e}")
