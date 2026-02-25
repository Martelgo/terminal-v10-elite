import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración visual de la App
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10: Inteligencia de Mercados")

# Universo de vigilancia (Puedes agregar más aquí)
universo = {
    "Tecnología": ["MSFT", "CRM", "ADBE", "ORCL", "SAP"],
    "Chips": ["AMD", "TSM", "NVDA", "ASML", "AVGO"],
    "Salud": ["NVO", "LLY", "UNH", "PFE"],
    "Consumo": ["AMZN", "BABA", "MELI", "NKE"],
    "Finanzas": ["PYPL", "V", "MA", "BAC"]
}

# --- BARRA LATERAL (Filtros rápidos) ---
st.sidebar.header("Configuración de Radar")
margen_min = st.sidebar.slider("Margen Mínimo %", 0, 100, 25)

# Función para obtener datos (Caché de 1 hora para rapidez)
@st.cache_data(ttl=3600)
def cargar_datos():
    lista_final = []
    for sector, tickers in universo.items():
        for t in tickers:
            try:
                acc = yf.Ticker(t)
                info = acc.info
                p_act = info.get('currentPrice') or info.get('regularMarketPrice')
                target = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((target - p_act) / p_act) * 100
                lista_final.append({"Ticker": t, "Sector": sector, "Precio": p_act, "Margen %": round(margen, 2)})
            except: continue
    return pd.DataFrame(lista_final)

df_global = cargar_datos()

# --- NAVEGACIÓN POR PESTAÑAS (Táctil) ---
tab1, tab2, tab3 = st.tabs(["🎯 RADAR", "🔥 MAPA", "🔍 V10 DETALLE"])

# TAB 1: RADAR DE SECTORES
with tab1:
    st.subheader("Top 3 Oportunidades por Sector")
    # Filtramos por el margen del slider
    df_filtrado = df_global[df_global['Margen %'] >= margen_min]
    # Mostramos el Top 3 de cada sector
    for sector in universo.keys():
        st.write(f"**Sector: {sector}**")
        top_sector = df_filtrado[df_filtrado['Sector'] == sector].sort_values(by="Margen %", ascending=False).head(3)
        if not top_sector.empty:
            st.dataframe(top_sector, use_container_width=True)
        else:
            st.info(f"Sin oportunidades con >{margen_min}% de margen en {sector}")

# TAB 2: MAPA DE CALOR
with tab2:
    st.subheader("Mapa de Calor: Margen de Seguridad")
    fig = px.treemap(df_global, path=['Sector', 'Ticker'], values='Precio',
                     color='Margen %', color_continuous_scale='RdYlGn',
                     color_continuous_midpoint=0)
    st.plotly_chart(fig, use_container_width=True)

# TAB 3: AUDITORÍA V10 DETALLADA
with tab3:
    st.subheader("Análisis 360° de Activo")
    ticker_input = st.text_input("Introduce Ticker:", "ORCL").upper()
    
    if ticker_input:
        acc_v10 = yf.Ticker(ticker_input)
        h = acc_v10.history(period="1y")
        if not h.empty:
            p_actual = h['Close'].iloc[-1]
            # Cálculos V10
            n1, n2, n3 = p_actual * 0.95, p_actual * 0.90, p_actual * 0.85
            
            # Métricas rápidas
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio Actual", f"${round(p_actual, 2)}")
            c2.metric("Nivel 1 (Compra)", f"${round(n1, 2)}")
            c3.metric("Nivel 3 (Pánico)", f"${round(n3, 2)}")
            
            # Gráfico interactivo
            fig_chart = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
            fig_chart.update_layout(xaxis_rangeslider_visible=False, height=400)
            st.plotly_chart(fig_chart, use_container_width=True)
