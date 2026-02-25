import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración visual
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10: Inteligencia de Mercados")

# --- UNIVERSO DE VIGILANCIA (EUA y México) ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"],
    "Consumo EUA": ["AMZN", "TSLA", "MELI", "NKE"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO"]
}

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
mercado_default = st.sidebar.selectbox("Mercado Principal", ["EUA", "México"])
margen_min = st.sidebar.slider("Margen Mínimo %", 0, 100, 15)

@st.cache_data(ttl=3600)
def cargar_datos():
    lista_final = []
    for sector, tickers in universo.items():
        for t in tickers:
            try:
                acc = yf.Ticker(t)
                info = acc.info
                p_act = info.get('currentPrice') or info.get('regularMarketPrice')
                # Cálculo de Precio Justo (Target o Estimación V10)
                target = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                
                if p_act and target and target > 0:
                    margen = ((target - p_act) / p_act) * 100
                    lista_final.append({
                        "Ticker": t, 
                        "Sector": sector, 
                        "Precio": round(p_act, 2), 
                        "Margen %": round(margen, 2),
                        "Moneda": info.get('currency', 'USD')
                    })
            except: continue
    return pd.DataFrame(lista_final)

df_global = cargar_datos()

# --- NAVEGACIÓN ---
tab1, tab2 = st.tabs(["🎯 RADAR DE OPORTUNIDADES", "🔍 TERMINAL V10 (DETALLE)"])

# TAB 1: RADAR
with tab1:
    st.subheader("Radar de Margen de Seguridad")
    if not df_global.empty:
        # Filtro de margen
        df_radar = df_global[df_global['Margen %'] >= margen_min].sort_values(by="Margen %", ascending=False)
        
        for sector in universo.keys():
            st.write(f"### {sector}")
            sector_df = df_radar[df_radar['Sector'] == sector]
            if not sector_df.empty:
                st.dataframe(sector_df, use_container_width=True)
            else:
                st.info(f"No hay acciones en {sector} con margen > {margen_min}%")
    else:
        st.error("No se pudieron cargar datos. Revisa la conexión.")

# TAB 2: TERMINAL V10 DETALLE
with tab2:
    st.subheader("Análisis 360 de Activo")
    col_input1, col_input2 = st.columns([1, 2])
    
    with col_input1:
        tipo_mercado = st.radio("Tipo de Ticker:", ["EUA (Normal)", "México (.MX)"])
    with col_input2:
        tk_input = st.text_input("Introduce Ticker (ej: MSFT o WALMEX.MX):", "MSFT").upper()

    if tk_input:
        # Validación automática de sufijo para México
        ticker_final = tk_input
        if tipo_mercado == "México (.MX)" and not ticker_final.endswith(".MX"):
            ticker_final = f"{ticker_final}.MX"
            
        with st.spinner(f'Analizando {ticker_final}...'):
            acc_v10 = yf.Ticker(ticker_final)
            h = acc_v10.history(period="1y")
            
            if not h.empty:
                p_actual = h['Close'].iloc[-1]
                moneda = acc_v10.info.get('currency', 'USD')
                
                # Niveles V10
                n1, n2, n3 = p_actual * 0.95, p_actual * 0.90, p_actual * 0.85
                
                # Métricas Estilo Terminal
                c1, c2, c3 = st.columns(3)
                c1.metric("Precio Actual", f"{p_actual:.2f} {moneda}")
                c2.metric("Nivel 1 (Compra)", f"{n1:.2f}")
                c3.metric("Nivel 3 (Pánico)", f"{n3:.2f}")
                
                # Gráfico
                fig_chart = go.Figure(data=[go.Candlestick(
                    x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close']
                )])
                fig_chart.update_layout(
                    title=f"Histórico 1 Año: {ticker_final}",
                    template="plotly_dark",
                    height=450,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig_chart, use_container_width=True)
            else:
                st.error("No se encontró información para ese Ticker. Verifica que sea correcto.")
