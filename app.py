import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro by marto")

# --- UNIVERSO DE VIGILANCIA ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL", "ORCL", "ADBE"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"]
}

# 2. INICIALIZAR MEMORIA (IMPORTANTE)
if 'radar_data' not in st.session_state:
    st.session_state.radar_data = pd.DataFrame()

# 3. NAVEGACIÓN
tab2, tab3 = st.tabs(["🔍 AUDITORIA", "🌡️ SENTIMIENTO"])

# --- TAB 2: AUDITORIA (ANÁLISIS INDIVIDUAL) ---
with tab2:
    st.subheader("Análisis 360 de Activo")
    c1, c2 = st.columns([1, 2])
    with c1: mkt = st.radio("Mercado:", ["EUA", "MX"])
    with c2: tk_in = st.text_input("Ticker:", "MSFT").upper()
    
    if st.button("🔍 AUDITAR AHORA"):
        tk_final = tk_in if mkt == "EUA" else f"{tk_in}.MX"
        with st.spinner('Analizando...'):
            acc = yf.Ticker(tk_final)
            h = acc.history(period="1y")
            if not h.empty:
                # Cálculos rápidos para el reporte
                p_act = h['Close'].iloc[-1]
                h['SMA200'] = ta.sma(h['Close'], length=200)
                sma_v = h['SMA200'].iloc[-1]
                
                st.write(f"### Reporte V10: {tk_final}")
                st.metric("Precio Actual", f"${p_act:.2f}", f"{'ALCISTA' if p_act > sma_v else 'BAJISTA'}")
                
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
