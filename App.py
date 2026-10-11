import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración del Dashboard Profesional
st.set_page_config(
    page_title="Sivigila - Intento de Suicidio", layout="wide", page_icon="🧠"
)

# Estilos CSS para las tarjetas de reporte
st.markdown(
    """
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4A90E2;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🧠 Dashboard Epidemiológico: Intento de Suicidio en Colombia")
st.caption("Análisis de datos consolidados de Vigilancia en Salud Pública (Sivigila) | Período 2016 - 2025")
st.markdown("---")

# 2. SISTEMA DE CARGA DIRECTA DESDE RELEASES PÚBLICAS
@st.cache_data
def cargar_datos_sivigila_directo():
    # Enlace de respaldo seguro que contiene exactamente tu base unificada de 315.832 filas
    url_directa_excel = "https://github.com"

    try:
        # Descarga y procesa la matriz masiva en la nube usando el motor calamine
        df_raw = pd.read_excel(url_directa_excel, engine="calamine")
        
        # Limpieza estándar de nombres de columnas
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        
        # Homologar la variable SEXO
        if "SEXO" in df_raw.columns:
            df_raw["SEXO"] = (
                df_raw["SEXO"]
                .astype(str)
                .str.upper()
                .replace({"1": "MASCULINO", "2": "FEMENINO", "M": "MASCULINO", "F": "FEMENINO"})
            )
        return df_raw
    except Exception as e:
        st.error(f"Error al procesar el archivo unificado de las Releases: {e}")
        return None

# Ejecutar la carga directa
df = cargar_datos_sivigila_directo()

# 3. CONSTRUCCIÓN DEL INFORME (Se ejecuta solo si la descarga es exitosa)
if df is not None:
    # --- PANEL LATERAL DE FILTROS ---
    st.sidebar.header("🔍 Filtros de Población")

    # Filtro 1: Año (Descendente)
    lista_años = (
        sorted(df["ANO"].dropna().unique().astype(int).tolist(), reverse=True)
        if "ANO" in df.columns
        else []
    )
    años_sel = st.sidebar.multiselect("Filtrar por Año(s):", lista_años, default=lista_años)

    # Filtro 2: Departamento de Residencia (Ascendente)
    lista_dptos = (
        sorted(df["Departamento_residencia"].dropna().unique().tolist())
        if "Departamento_residencia" in df.columns
        else []
    )
    dptos_sel = st.sidebar.multiselect("Filtrar por Departamento:", lista_dptos)

    # Filtro 3: Selectores de Vulnerabilidades de Sivigila
    st.sidebar.markdown("---")
    st.sidebar.subheader("👥 Grupos de Riesgo y Vulnerabilidad")
    
    diccionario_vulnerabilidades = {
        "Ninguno": "Ninguno",
        "GP_PSIQUIA": "🧠 Con Antecedente Psiquiátrico",
        "GP_VIC_VIO": "🛡️ Víctima de Violencia",
        "GP_DESPLAZ": "🏃 Desplazados por Violencia",
        "GP_MIGRANT": "🧳 Población Migrante",
        "GP_DISCAPA": "♿ Persona con Discapacidad",
        "GP_CARCELA": "🔒 Población Privada de la Libertad",
        "GP_GESTAN": "🤰 Mujeres Gestantes",
        "GP_INDIGEN": "🏹 Población Indígena",
        "GP_POBICFB": "👶 Población bajo protección del ICFB",
        "GP_MAD_COM": "🏡 Madres Comunitarias",
        "GP_DESMOVI": "🪖 Población Desmovilizada",
        "GP_OTROS": "📁 Otros Grupos Especiales"
    }
    
    vulnerabilidad_elegida = st.sidebar.selectbox(
        "Filtrar por Factor Específico (Solo Casos = SI):",
        options=list(diccionario_vulnerabilidades.values())
    )

    # --- APLICACIÓN DE LOS FILTROS ---
    df_filtrado = df.copy()
    if años_sel:
        df_filtrado = df_filtrado[df_filtrado["ANO"].isin(años_sel)]
    if dptos_sel:
        df_filtrado = df_filtrado[df_filtrado["Departamento_residencia"].isin(dptos_sel)]
    if vulnerabilidad_elegida != "Ninguno":
        columna_tecnica = [k for k, v in diccionario_vulnerabilidades.items() if v == vulnerabilidad_elegida]
        if columna_tecnica and columna_tecnica[0] in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[columna_tecnica[0]].astype(str).str.startswith(('1', '1.0'))]

    # --- INDICADORES CLAVE (KPIs) ---
    st.markdown("### 📊 Indicadores Clave del Período Seleccionado")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f"<div class='metric-box'><h5>📉 Total Casos</h5><h2>{len(df_filtrado):,}</h2></div>", unsafe_allow_html=True)

    with kpi2:
        if "EDAD" in df_filtrado.columns:
            edad_prom = pd.to_numeric(df_filtrado["EDAD"], errors="coerce").mean()
            val_edad = f"{edad_prom:.1f} años" if not pd.isna(edad_prom) else "N/A"
        else:
            val_edad = "N/A"
        st.markdown(f"<div class='metric-box'><h5>🧑‍⚕️ Promedio de Edad</h5><h2>{val_edad}</h2></div>", unsafe_allow_html=True)

    with kpi3:
        if "SEXO" in df_filtrado.columns and len(df_filtrado) > 0:
            mujeres = len(df_filtrado[df_filtrado["SEXO"] == "FEMENINO"])
            porc_mujeres = (mujeres / len(df_filtrado)) * 100
            val_sexo = f"{porc_mujeres:.1f}%"
        else:
            val_sexo = "N/A"
        st.markdown(f"<div class='metric-box'><h5>👩 % Casos Mujeres</h5><h2>{val_sexo}</h2></div>", unsafe_allow_html=True)

    with kpi4:
        if "PAC_HOS" in df_filtrado.columns and len(df_filtrado) > 0:
            hosp = len(df_filtrado[df_filtrado["PAC_HOS"].astype(str).str.startswith(("1", "S", "s"))])
            porc_hosp = (hosp / len(df_filtrado)) * 100
            val_hosp = f"{porc_hosp:.1f}%"
        else:
            val_hosp = "N/A"
        st.markdown(f"<div class='metric-box'><h5>🏥 % Hospitalización</h5><h2>{val_hosp}</h2></div>", unsafe_allow_html=True)

    # --- SECCIÓN DE GRÁFICOS INTERACTIVOS ---
    st.markdown("---")
    st.markdown("### 📈 Visualización y Análisis Epidemiológico")

    pestana1, pestana2, pestana_mapa, pestana3 = st.tabs([
        "📈 Tendencia & Demografía", "📊 Análisis Geográfico", "🗺️ Mapa de Calor (Colombia)", "👥 Factores Vulnerables"
    ])

    with pestana1:
        g1, g2 = st.columns(2)
        with g1:
            if "ANO" in df_filtrado.columns:
                df_linea = df_filtrado.groupby(["ANO", "SEXO"]).size().reset_index(name="Casos")
                fig_linea = px.line(df_linea, x="ANO", y="Casos", color="SEXO", title="Evolución Histórica de Casos por Sexo", markers=True)
                st.plotly_chart(fig_linea, use_container_width=True)
        with g2:
            if "EDAD" in df_filtrado.columns:
                fig_hist = px.histogram(df_filtrado, x="EDAD", color="SEXO", nbins=20, title="Distribución de Casos por Edad y Sexo", barmode="group")
                st.plotly_chart(fig_hist, use_container_width=True)

    with pestana2:
        if "Departamento_residencia" in df_filtrado.columns:
            df_mapa = df_filtrado.groupby("Departamento_residencia").size().reset_index(name="Casos").sort_values(by="Casos", ascending=False)
            fig_mapa = px.bar(df_mapa.head(15), x="Casos", y="Departamento_residencia", orientation="h", title="Top 15 Departamentos con Mayor Reporte", color="Casos", color_continuous_scale="Reds")
            fig_mapa.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_mapa, use_container_width=True)

    with pestana_mapa:
        st.write("#### 🗺️ Distribución Geográfica Nacional de Casos")
        if "Departamento_residencia" in df_filtrado.columns:
            df_geo = df_filtrado.groupby("Departamento_residencia").size().reset_index(name="Total Casos")
            df_geo["Departamento_residencia"] = df_geo["Departamento_residencia"].astype(str).str.upper().str.strip()
            
            coordenadas_colombia = {
                "AMAZONAS": [1.4469, -71.5222], "ANTIOQUIA": [6.2442, -75.5812], "ARAUCA": [7.0847, -70.7591],
                "ATLANTICO": [10.9639, -74.7964], "BOGOTA": [4.7110, -74.0721], "BOGOTA D.C.": [4.7110, -74.0721], "BOGOTÁ, D.C.": [4.7110, -74.0721],
                "BOLIVAR": [10.3997, -75.5144], "BOYACA": [5.5353, -73.3678], "CALDAS": [5.0689, -75.5174],
                "CAQUETA": [1.6144, -75.6062], "CASANARE": [5.3378, -72.3959], "CAUCA": [2.4419, -76.6063],
                "CESAR": [10.4631, -73.2532], "CHOCO": [5.6919, -76.6583], "CORDOBA": [8.7479, -75.8814],
                "CUNDINAMARCA": [4.6097, -74.0817], "GUAINIA": [3.8653, -67.9239], "GUAVIARE": [2.5668, -72.6459],
                "HUILA": [2.9273, -75.2819], "LA GUAJIRA": [11.5444, -72.9069], "MAGDALENA": [11.2408, -74.1990],
                "META": [4.1420, -73.6266], "NARIÑO": [1.2136, -77.2811], "NORTE DE SANTANDER": [7.8939, -72.5078],
                "PUTUMAYO": [1.1494, -76.6461], "QUINDIO": [4.5350, -75.6757], "RISARALDA": [4.8133, -75.6961],
                "SAN ANDRES": [12.5833, -81.7000], "SANTANDER": [7.1254, -73.1198], "SUCRE": [9.3047, -75.3978],
                "TOLIMA": [4.4389, -75.2322], "VALLE DEL CAUCA": [3.4516, -76.5320], "VAUPES": [1.1984, -70.1733], "VICHADA": [6.1848, -67.4858]
            }
            
            df_geo["latitud"] = df_geo["Departamento_residencia"].map(lambda x: coordenadas_colombia.get(x, [None, None]))
            df_geo["longitud"] = df_geo["Departamento_residencia"].map(lambda x: coordenadas_colombia.get(x, [None, None]))
            df_geo = df_geo.dropna(subset=["latitud", "longitud"])
            
            fig_mapa_seguro = px.scatter_geo(
                df_geo, lat="latitud", lon="longitud", size="Total Casos", color="Total Casos",
                hover_name="Departamento_residencia", color_continuous_scale="Reds", title="Focos Epidemiológicos de Intento de Suicidio en Colombia", size_max=40
            )


            fig_mapa_seguro.update_geos(center=dict(lon=-74.0, lat=4.5), projection_scale=6, showcountries=True, countrycolor="Silver", showland=True, landcolor="White")
            fig_mapa_seguro.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_mapa_seguro, use_container_width=True)

    with pestana3:
        # Nota cómo todas las líneas de abajo llevan una sangría extra hacia la derecha
        g3, g4 = st.columns(2)
        with g3:
            if "nom_grupo" in df_filtrado.columns:
                df_grupo = df_filtrado.groupby("nom_grupo").size().reset_index(name="Casos").sort_values(by="Casos", ascending=False)
                fig_grupo = px.pie(df_grupo.head(7), names="nom_grupo", values="Casos", title="Distribución por Grupos Poblacionales Especiales")
                st.plotly_chart(fig_grupo, use_container_width=True)
        with g4:
            if "estrato" in df_filtrado.columns:
                df_estrato = df_filtrado.groupby("estrato").size().reset_index(name="Casos")
                fig_estrato = px.bar(df_estrato, x="estrato", y="Casos", title="Frecuencia de Casos por Estrato Socioeconómico", text_auto=True)
                st.plotly_chart(fig_estrato, use_container_width=True)

    # --- BUSCADOR COMPLETO ---
    st.markdown("---")
    with st.expander("🔍 Buscador de Registros Clínicos Completos (Fila por Fila)"):
        st.dataframe(df_filtrado.head(500), use_container_width=True)
else:
    st.error("No se pudo inicializar la base de datos de Sivigila.")

