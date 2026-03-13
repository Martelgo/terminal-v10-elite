import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# Configuración visual de la App
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro by marto")

# --- UNIVERSO DE VIGILANCIA (S&P 500 y Nasdaq) ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL", "ORCL", "ADBE"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO", "INTC", "MU"],
    "Consumo/Otros": ["AMZN", "TSLA", "MELI", "NKE", "META"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"]
}

# Inicializar estados de sesión para no "quemar balas"
if 'df_radar' not in st.session_state:
    st.session_state.df_radar = pd.DataFrame()
if 'ejecutado' not in st.session_state:
    st.session_state.ejecutado = False

def cargar_radar_manual():
    datos = []
    progreso = st.progress(0)
    total_tickers = sum(len(v) for v in universo.values())
    contador = 0
    
    for sector, tickers in universo.items():
        for t in tickers:
            try:
                s = yf.Ticker(t)
                # Usamos fast_info para no saturar la API
                p = s.fast_info['lastPrice']
                info = s.info
                tj = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                ebitda = info.get('ebitda', 0) or 0
                m = ((tj - p) / p) * 100 if p else 0
                
                if m > 15 and ebitda > 0: estado = "🟢 COMPRA CLARA"
                elif m > 5 and ebitda > 0: estado = "🟡 VIGILAR"
                else: estado = "🔴 EVITAR / CARO"
                
                datos.append({
                    "Ticker": t, 
                    "Estado V10": estado,
                    "Precio": round(p, 2), 
                    "Margen %": round(m, 1),
                    "Sector": sector
                })
            except: continue
            contador += 1
            progreso.progress(contador / total_tickers)
    
    st.session_state.df_radar = pd.DataFrame(datos)
    st.session_state.ejecutado = True

# --- NAVEGACIÓN ---
tab1, tab2, tab3 = st.tabs(["🎯 RADAR SEMÁFORO", "🔍 AUDITORIA 360", "🌡️ SENTIMIENTO"])

# --- TAB 1: RADAR (MANUAL) ---
with tab1:
    st.subheader("Radar de Oportunidades Global")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🚀 INICIAR ESCANEO"):
            cargar_radar_manual()
    
    if st.session_state.ejecutado:
        df = st.session_state.df_radar
        for sector in universo.keys():
            with st.expander(f"📦 Sector: {sector}", expanded=True):
                sector_df = df[df['Sector'] == sector].drop(columns=['Sector'])
                st.dataframe(sector_df, use_container_width=True)
        
        if st.button("🗑️ Limpiar Radar"):
            st.session_state.df_radar = pd.DataFrame()
            st.session_state.ejecutado = False
            st.rerun()
    else:
        st.info("Presiona el botón para escanear el mercado. El sistema está en reposo para ahorrar recursos.")

# --- TAB 2: AUDITORIA (INDEPENDIENTE) ---
with tab2:
    st.subheader("Auditoría de Activo Individual")
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1: mkt = st.radio("Mercado:", ["EUA", "México (.MX)"])
    with c_i2: tk_in = st.text_input("Ticker para Auditar:", "AMD").upper()

    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if st.button("🔍 AUDITAR AHORA"):
        with st.spinner(f'Consultando {ticker_final}...'):
            acc = yf.Ticker(ticker_final)
            h = acc.history(period="1y")
            info = acc.info
            if not h.empty:
                h['RSI'] = ta.rsi(h['Close'], length=14)
                h['SMA200'] = ta.sma(h['Close'], length=200)
                p_act = h['Close'].iloc[-1]
                rsi_v = h['RSI'].iloc[-1] if not pd.isna(h['RSI'].iloc[-1]) else 50
                sma_v = h['SMA200'].iloc[-1] if not pd.isna(h['SMA200'].iloc[-1]) else p_act
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_act) * 100
                ebitda = info.get('ebitda', 0) or 0
                
                est_m = "DESCUENTO" if margen > 15 else "CARO"
                est_r = "SOBREVENTA" if rsi_v < 35 else ("SOBRECOMPRA" if rsi_v > 65 else "NEUTRAL")
                est_t = "ALCISTA" if p_act > sma_v else "BAJISTA"
                
                st.markdown(f"### 🏢 {info.get('longName', ticker_final)}")
                reporte_v2 = f"""
=================================================================
                  MÉTRICA           VALOR       ESTADO
-----------------------------------------------------------------
            Precio Actual         ${p_act:>8.2f}    Cotizando
Precio Justo de la Acción         ${p_justo:>8.2f}    Referencia
              Margen Seg.              {margen:>7.1f}%       {"✅" if est_m=="DESCUENTO" else "❌"} {est_m}
                RSI (14d)               {rsi_v:>7.1f}  {"📉" if rsi_v<35 else "⚖️"} {est_r}
                  SMA 200         ${sma_v:>8.2f}    {"🚀" if est_t=="ALCISTA" else "⚠️"} {est_t}
                   EBITDA          {ebitda:>14,}       ✅ Sólido
-----------------------------------------------------------------
📍 NIVELES DE COMPRA:  1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
"""
                st.code(reporte_v2, language="text")
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: SENTIMIENTO ---
with tab3:
    if st.button("🌡️ REFRESCAR SENTIMIENTO"):
        spy = yf.Ticker("SPY")
        val = ta.rsi(spy.history(period="1y")['Close'], length=14).iloc[-1]
        st.metric("RSI SPY (Market Sentiment)", f"{val:.2f}")
        st.progress(val/100)
