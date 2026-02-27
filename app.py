import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# Configuración visual
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro")

# --- UNIVERSO DE VIGILANCIA ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO"],
    "Consumo": ["AMZN", "TSLA", "MELI", "NKE"]
}

@st.cache_data(ttl=600)
def cargar_radar():
    datos = []
    for sector, tickers in universo.items():
        for t in tickers:
            try:
                s = yf.Ticker(t)
                p = s.info.get('currentPrice') or s.info.get('regularMarketPrice', 0)
                tj = s.info.get('targetMeanPrice') or (s.info.get('forwardPE', 15) * s.info.get('forwardEps', 1))
                m = ((tj - p) / p) * 100 if p else 0
                datos.append({"Ticker": t, "Sector": sector, "Precio": round(p, 2), "Margen %": round(m, 2)})
            except: continue
    return pd.DataFrame(datos)

# --- NAVEGACIÓN ---
tab1, tab2, tab3 = st.tabs(["🎯 RADAR", "🔍 AUDITORIA", "🌡️ SENTIMIENTO"])

# --- TAB 1: RADAR ---
with tab1:
    df_radar = cargar_radar()
    if not df_radar.empty:
        for sector in universo.keys():
            st.write(f"### {sector}")
            st.dataframe(df_radar[df_radar['Sector'] == sector], use_container_width=True)

# --- TAB 2: AUDITORIA ---
with tab2:
    st.subheader("Análisis 360 de Activo")
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1: mkt = st.radio("Mercado:", ["EUA", "México (.MX)"])
    with c_i2: tk_in = st.text_input("Ticker:", "MSFT").upper()

    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if ticker_final:
        with st.spinner('Procesando...'):
            acc = yf.Ticker(ticker_final)
            h = acc.history(period="1y")
            info = acc.info
            if not h.empty:
                h['RSI'] = ta.rsi(h['Close'], length=14)
                h['SMA200'] = ta.sma(h['Close'], length=200)
                p_act, rsi_v, sma_v = h['Close'].iloc[-1], h['RSI'].iloc[-1], h['SMA200'].iloc[-1]
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_act) * 100
                ebitda = info.get('ebitda', 0) or 0
                est_m, est_r, est_t = "DESCUENTO" if margen > 15 else "CARO", "SOBREVENTA" if rsi_v < 35 else ("SOBRECOMPRA" if rsi_v > 65 else "NEUTRAL"), "ALCISTA" if p_act > sma_v else "BAJISTA"
                
                st.code(f"""
🏢 {info.get('longName', ticker_final)}
=================================================================
PRECIO: ${p_act:.2f} | MARGEN: {margen:.1f}% ({est_m})
RSI: {rsi_v:.1f} ({est_r}) | SMA 200: ${sma_v:.2f} ({est_t})
EBITDA: {ebitda:,} ({"✅ Sólido" if ebitda > 0 else "⚠️ RIESGO"})
-----------------------------------------------------------------
📍 COMPRA: 1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
""", language="text")

# --- TAB 3: SENTIMIENTO (AJUSTE PARA MÓVIL) ---
with tab3:
    st.subheader("Indicador de Pánico y Codicia")
    
    spy = yf.Ticker("SPY")
    spy_h = spy.history(period="1y")
    spy_h['RSI'] = ta.rsi(spy_h['Close'], length=14)
    val = spy_h['RSI'].iloc[-1]
    
    if val < 30: etiq, col = "PÁNICO EXTREMO", "red"
    elif val < 45: etiq, col = "MIEDO", "orange"
    elif val < 60: etiq, col = "NEUTRAL", "gray"
    elif val < 75: etiq, col = "CODICIA", "lightgreen"
    else: etiq, col = "EUFORIA EXTREMA", "green"

    # Medidor con fuente reducida para móvil
    fig_sent = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        number = {'font': {'size': 40}}, # Número más pequeño para que no se corte
        title = {'text': f"Estado: {etiq}", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': col},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "gray"},
                {'range': [70, 100], 'color': "green"}]
        }
    ))
    # Ajuste de márgenes para que quepa en el ancho del teléfono
    fig_sent.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20), template="plotly_dark")
    st.plotly_chart(fig_sent, use_container_width=True)
    
    st.info("💡 **Pánico (Rojo) = Oportunidad** | **Euforia (Verde) = Cautela**")
