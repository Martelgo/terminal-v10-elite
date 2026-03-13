import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro by marto")

# --- UNIVERSO DE VIGILANCIA ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL", "ORCL", "ADBE"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"],
    "Consumo": ["AMZN", "TSLA", "MELI", "NKE"]
}

# 2. GESTIÓN DE MEMORIA (SESSION STATE)
# Esto evita que los datos se borren al cambiar de pestaña
if 'radar_data' not in st.session_state:
    st.session_state.radar_data = pd.DataFrame()

# 3. MOTOR DEL RADAR (SOLO SE ACTIVA POR BOTÓN)
def ejecutar_escaneo_global():
    datos = []
    progreso = st.progress(0)
    total_tickers = sum(len(v) for v in universo.values())
    contador = 0
    
    with st.spinner('Auditando mercado global...'):
        for sector, tickers in universo.items():
            for t in tickers:
                try:
                    s = yf.Ticker(t)
                    # Usamos fast_info para el precio actual (más rápido)
                    p = s.fast_info['lastPrice']
                    info = s.info
                    # Lógica V10 de Precio Justo
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
    
    return pd.DataFrame(datos)

# --- NAVEGACIÓN POR PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["🎯 RADAR SEMÁFORO", "🔍 AUDITORIA 360", "🌡️ SENTIMIENTO"])

# --- TAB 1: RADAR (CONTROL MANUAL) ---
with tab1:
    st.subheader("Radar de Oportunidades")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        # AQUÍ ESTÁ EL CANDADO: Solo corre si haces clic
        if st.button("🚀 INICIAR ESCANEO"):
            st.session_state.radar_data = ejecutar_escaneo_global()
    
    # Mostrar datos guardados si existen
    if not st.session_state.radar_data.empty:
        df_res = st.session_state.radar_data
        for sector in universo.keys():
            with st.expander(f"📦 {sector}", expanded=True):
                sector_df = df_res[df_res['Sector'] == sector].drop(columns=['Sector'])
                st.dataframe(sector_df, use_container_width=True)
    else:
        st.info("El Radar está en reposo. Presiona 'INICIAR ESCANEO' para auditar el mercado global.")
    
    st.caption("🟢 Margen > 15% + EBITDA Sólido | 🟡 Margen 5-15% | 🔴 Caro o Riesgo")

# --- TAB 2: AUDITORIA (INDEPENDIENTE Y RÁPIDA) ---
with tab2:
    st.subheader("Análisis Individual Profundo")
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1: mkt = st.radio("Mercado:", ["EUA", "México (.MX)"])
    with c_i2: tk_in = st.text_input("Ticker:", "AMD").upper()

    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if st.button("🔍 AUDITAR AHORA"):
        with st.spinner(f'Analizando {ticker_final}...'):
            acc = yf.Ticker(ticker_final)
            h = acc.history(period="1y")
            info = acc.info
            
            if not h.empty:
                # Cálculos Técnicos y Fundamentales
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
                
                # REPORTE ESTILO CONSOLA V10
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

                # GRÁFICO DE VELAS
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Precio")])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Ticker no encontrado o sin datos.")

# --- TAB 3: SENTIMIENTO ---
with tab3:
    st.subheader("Sentimiento del Mercado")
    if st.button("🌡️ REFRESCAR SENTIMIENTO"):
        spy = yf.Ticker("SPY")
        spy_h = spy.history(period="1y")
        val = ta.rsi(spy_h['Close'], length=14).iloc[-1]
        st.metric("RSI Mercado (SPY)", f"{val:.2f}")
        st.info("Pánico < 30 | Neutral 50 | Euforia > 70")
