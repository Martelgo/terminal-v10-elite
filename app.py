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
tab1, tab2, tab3 = st.tabs(["🎯 RADAR SEMÁFORO", "🔍 AUDITORIA", "🌡️ SENTIMIENTO"])

# --- TAB 1: RADAR (CON BOTÓN DE CONTROL) ---
with tab1:
    st.subheader("Radar de Oportunidades")
    
    # ESTE ES EL BLOQUE DEL BOTÓN. DEBE ESTAR ARRIBA DE LAS TABLAS.
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        # Al presionar este botón, se activa el escaneo
        ejecutar = st.button("🚀 INICIAR ESCANEO", use_container_width=True)
    
    if ejecutar:
        datos = []
        progreso = st.progress(0)
        total = sum(len(v) for v in universo.values())
        contador = 0
        
        with st.spinner('Escaneando mercado...'):
            for sector, tickers in universo.items():
                for t in tickers:
                    try:
                        s = yf.Ticker(t)
                        p = s.fast_info['lastPrice']
                        info = s.info
                        tj = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                        ebitda = info.get('ebitda', 0) or 0
                        m = ((tj - p) / p) * 100 if p else 0
                        
                        estado = "🟢 COMPRA CLARA" if m > 15 and ebitda > 0 else ("🟡 VIGILAR" if m > 5 and ebitda > 0 else "🔴 EVITAR / CARO")
                        
                        datos.append({"Ticker": t, "Estado V10": estado, "Precio": round(p, 2), "Margen %": round(m, 1), "Sector": sector})
                    except: continue
                    contador += 1
                    progreso.progress(contador / total)
            
            st.session_state.radar_data = pd.DataFrame(datos)
            st.rerun() # Forzamos recarga para mostrar resultados

    # LÓGICA DE VISUALIZACIÓN
    if not st.session_state.radar_data.empty:
        df_radar = st.session_state.radar_data
        for sector in universo.keys():
            st.write(f"### {sector}")
            sector_df = df_radar[df_radar['Sector'] == sector].drop(columns=['Sector'])
            st.dataframe(sector_df, use_container_width=True)
    else:
        st.info("⚠️ El Radar está en espera. Haz clic en el botón de arriba para iniciar el escaneo global.")

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
