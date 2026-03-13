import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# Configuración visual de la App
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro by marto")

# --- UNIVERSO DE VIGILANCIA ---
universo = {
    "Tecnología EUA": ["MSFT", "AAPL", "NVDA", "GOOGL", "ORCL", "ADBE"],
    "Chips": ["AMD", "TSM", "ASML", "AVGO"],
    "México (BMV)": ["WALMEX.MX", "AMX.MX", "GFNORTEO.MX", "FEMSAUBD.MX", "GMEXICOB.MX"],
    "Consumo": ["AMZN", "TSLA", "MELI", "NKE"]
}

# --- GESTIÓN DE ESTADO (PERSISTENCIA DE DATOS) ---
if 'df_radar' not in st.session_state:
    st.session_state.df_radar = None
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = None

# --- NAVEGACIÓN ---
tab1, tab2, tab3 = st.tabs(["🎯 RADAR SEMÁFORO", "🔍 AUDITORIA 360", "🌡️ SENTIMIENTO"])

# --- TAB 1: RADAR (CONTROL TOTAL DE RECURSOS) ---
with tab1:
    st.subheader("Radar de Oportunidades")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
    with col_btn1:
        btn_escanear = st.button("🚀 INICIAR ESCANEO", use_container_width=True)
    with col_btn2:
        if st.button("🗑️ LIMPIAR", use_container_width=True):
            st.session_state.df_radar = None
            st.session_state.ultima_actualizacion = None
            st.rerun()
    
    if st.session_state.ultima_actualizacion:
        st.caption(f"Última actualización: {st.session_state.ultima_actualizacion}")

    if btn_escanear:
        datos = []
        progreso = st.progress(0)
        total_t = sum(len(v) for v in universo.values())
        contador = 0
        
        with st.spinner('Auditando mercado global...'):
            for sector, tickers in universo.items():
                for t in tickers:
                    try:
                        s = yf.Ticker(t)
                        p = s.fast_info['lastPrice']
                        f_info = s.info
                        tj = f_info.get('targetMeanPrice') or (f_info.get('forwardPE', 15) * f_info.get('forwardEps', 1))
                        ebitda = f_info.get('ebitda', 0) or 0
                        m = ((tj - p) / p) * 100 if p else 0
                        
                        if m > 15 and ebitda > 0: estado = "🟢 COMPRA CLARA"
                        elif m > 5 and ebitda > 0: estado = "🟡 VIGILAR"
                        else: estado = "🔴 EVITAR / CARO"
                        
                        datos.append({"Ticker": t, "Estado V10": estado, "Precio": round(p, 2), "Margen %": round(m, 1), "Sector": sector})
                    except: continue
                    contador += 1
                    progreso.progress(contador / total_t)
            
            st.session_state.df_radar = pd.DataFrame(datos)
            st.session_state.ultima_actualizacion = datetime.now().strftime("%H:%M:%S")
            st.rerun()

    if st.session_state.df_radar is not None:
        df = st.session_state.df_radar
        for sector in universo.keys():
            with st.expander(f"📦 {sector}", expanded=True):
                sector_df = df[df['Sector'] == sector].drop(columns=['Sector'])
                st.dataframe(sector_df, use_container_width=True)
    else:
        st.info("Sistema en modo ahorro. Presiona 'INICIAR ESCANEO' para buscar oportunidades.")

# --- TAB 2: AUDITORIA (MOTOR COMPLETO) ---
with tab2:
    st.subheader("Análisis Individual Profundo")
    c1, c2 = st.columns([1, 2])
    with c1: mkt_opt = st.selectbox("Mercado:", ["EUA", "México (.MX)"])
    with c2: tk_in = st.text_input("Ingresa Ticker (ej: AMD, NVDA, ORCL):", "AMD").upper()

    t_final = tk_in if mkt_opt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if st.button("🔍 AUDITAR AHORA"):
        with st.spinner(f'Analizando {t_final}...'):
            acc = yf.Ticker(t_final)
            h = acc.history(period="1y")
            info = acc.info
            
            if not h.empty:
                # Cálculos V10
                h['RSI'] = ta.rsi(h['Close'], length=14)
                h['SMA200'] = ta.sma(h['Close'], length=200)
                p_act = h['Close'].iloc[-1]
                rsi_v = h['RSI'].iloc[-1] if not pd.isna(h['RSI'].iloc[-1]) else 50
                sma_v = h['SMA200'].iloc[-1] if not pd.isna(h['SMA200'].iloc[-1]) else p_act
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_act) * 100
                ebitda = info.get('ebitda', 0) or 0

                st.markdown(f"### 🏢 {info.get('longName', t_final)}")
                
                # Consola de Resultados
                rep = f"""
=================================================================
                  MÉTRICA           VALOR       ESTADO
-----------------------------------------------------------------
            Precio Actual         ${p_act:>8.2f}    Cotizando
Precio Justo de la Acción         ${p_justo:>8.2f}    Referencia
              Margen Seg.              {margen:>7.1f}%       {"✅" if margen > 15 else "❌"} { "DESCUENTO" if margen > 15 else "PRECIO ALTO"}
                RSI (14d)               {rsi_v:>7.1f}  {"📉" if rsi_v < 40 else "⚖️"} {"REBOTE" if rsi_v < 40 else "NEUTRAL"}
                  SMA 200         ${sma_v:>8.2f}    {"🚀" if p_act > sma_v else "⚠️"} {"ALCISTA" if p_act > sma_v else "BAJISTA"}
                   EBITDA          {ebitda:>14,}       {"✅" if ebitda > 0 else "⚠️"} Sólido
-----------------------------------------------------------------
📍 NIVELES DE COMPRA:  1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
"""
                st.code(rep, language="text")

                # Gráfico
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Precio")])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No se encontraron datos para este Ticker. Revisa si está bien escrito.")

# --- TAB 3: SENTIMIENTO ---
with tab3:
    st.subheader("Sentimiento del Mercado (SPY)")
    if st.button("🌡️ MEDIR PÁNICO/CODICIA"):
        spy = yf.Ticker("SPY")
        s_h = spy.history(period="1y")
        val = ta.rsi(s_h['Close'], length=14).iloc[-1]
        st.metric("RSI de Mercado", f"{val:.2f}")
        st.info("Lectura: < 30 Pánico | > 70 Euforia")
