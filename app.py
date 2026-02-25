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
    "Chips": ["AMD", "TSM", "ASML", "AVGO"]
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
                m = ((tj - p) / tj) * 100 if tj else 0
                datos.append({"Ticker": t, "Sector": sector, "Precio": round(p, 2), "Margen %": round(m, 2)})
            except: continue
    return pd.DataFrame(datos)

tab1, tab2 = st.tabs(["🎯 RADAR DE OPORTUNIDADES", "🔍 AUDITORIA V10"])

# --- TAB 1: RADAR ---
with tab1:
    df_radar = cargar_radar()
    if not df_radar.empty:
        for sector in universo.keys():
            st.write(f"### {sector}")
            st.dataframe(df_radar[df_radar['Sector'] == sector], use_container_width=True)

# --- TAB 2: AUDITORIA (CON CONSOLA VISUAL) ---
with tab2:
    st.subheader("Análisis 360 de Activo")
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1:
        mkt = st.radio("Mercado:", ["EUA", "México (.MX)"])
    with c_i2:
        tk_in = st.text_input("Ticker:", "MSFT").upper()

    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if ticker_final:
        with st.spinner('Procesando datos...'):
            acc = yf.Ticker(ticker_final)
            h = acc.history(period="1y")
            info = acc.info
            
            if not h.empty:
                # Cálculos Técnicos
                h['RSI'] = ta.rsi(h['Close'], length=14)
                h['SMA200'] = ta.sma(h['Close'], length=200)
                
                p_act = h['Close'].iloc[-1]
                rsi_v = h['RSI'].iloc[-1]
                sma_v = h['SMA200'].iloc[-1]
                moneda = info.get('currency', 'USD')
                ebitda = info.get('ebitda', 0)
                
                # Precio Justo y Margen
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_justo) * 100 if p_justo else 0
                
                # Lógica de Estados
                est_m = "DESCUENTO" if margen > 15 else "CARO"
                est_r = "SOBREVENTA" if rsi_v < 35 else ("SOBRECOMPRA" if rsi_v > 65 else "NEUTRAL")
                est_t = "ALCISTA" if p_act > sma_v else "BAJISTA"
                estrategia = "REBOTE" if rsi_v < 40 else "CONTINUACION"

                # --- LA CONSOLA QUE QUERÍAS ---
                st.markdown(f"### 🏢 {info.get('longName', ticker_final)}")
                st.markdown(f"**📡 ESTRATEGIA: {estrategia} (Acción en {est_m.lower()})**")
                
                # Usamos st.code para mantener el formato de terminal alineado
                reporte = f"""
=================================================================
                  MÉTRICA           VALOR       ESTADO
-----------------------------------------------------------------
            Precio Actual         ${p_act:.2f}    Cotizando
Precio Justo de la Acción         ${p_justo:.2f}   Referencia
              Margen Seg.           {margen:.1f}%       {"✅" if est_m=="DESCUENTO" else "❌"} {est_m}
                RSI (14d)            {rsi_v:.1f}  {"📉" if rsi_v<35 else "⚖️"} {est_r}
                  SMA 200         ${sma_v:.2f}   {"🚀" if est_t=="ALCISTA" else "⚠️"} {est_t}
                   EBITDA          {ebitda:,}       Sólido
-----------------------------------------------------------------
📍 NIVELES DE COMPRA:  1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
"""
                st.code(reporte, language="text")

                # Gráfico
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
