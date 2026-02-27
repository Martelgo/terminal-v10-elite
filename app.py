import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# Configuración visual de la App para móvil y PC
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro")

# --- UNIVERSO DE VIGILANCIA (EUA y México) ---
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
                # Obtenemos precio y calculamos precio justo
                p = s.info.get('currentPrice') or s.info.get('regularMarketPrice', 0)
                tj = s.info.get('targetMeanPrice') or (s.info.get('forwardPE', 15) * s.info.get('forwardEps', 1))
                m = ((tj - p) / p) * 100 if p else 0
                datos.append({"Ticker": t, "Sector": sector, "Precio": round(p, 2), "Margen %": round(m, 2)})
            except: continue
    return pd.DataFrame(datos)

# --- NAVEGACIÓN POR PESTAÑAS ---
tab1, tab2 = st.tabs(["🎯 RADAR DE OPORTUNIDADES", "🔍 AUDITORIA V10"])

# --- TAB 1: RADAR ---
with tab1:
    df_radar = cargar_radar()
    if not df_radar.empty:
        for sector in universo.keys():
            st.write(f"### {sector}")
            st.dataframe(df_radar[df_radar['Sector'] == sector], use_container_width=True)

# --- TAB 2: AUDITORIA (CON CONSOLA INTELIGENTE) ---
with tab2:
    st.subheader("Análisis 360 de Activo")
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1:
        mkt = st.radio("Mercado:", ["EUA", "México (.MX)"])
    with c_i2:
        tk_in = st.text_input("Introduce Ticker:", "MSFT").upper()

    # Manejo automático de sufijos para México
    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if ticker_final:
        with st.spinner(f'Procesando {ticker_final}...'):
            acc = yf.Ticker(ticker_final)
            h = acc.history(period="1y")
            info = acc.info
            
            if not h.empty:
                # --- CÁLCULOS TÉCNICOS ---
                h['RSI'] = ta.rsi(h['Close'], length=14)
                h['SMA200'] = ta.sma(h['Close'], length=200)
                
                p_act = h['Close'].iloc[-1]
                rsi_v = h['RSI'].iloc[-1] if not pd.isna(h['RSI'].iloc[-1]) else 50
                sma_v = h['SMA200'].iloc[-1] if not pd.isna(h['SMA200'].iloc[-1]) else p_act
                
                # --- CÁLCULOS FUNDAMENTALES ---
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_act) * 100 if p_act else 0
                
                # Lógica de EBITDA Inteligente (Tu observación)
                ebitda = info.get('ebitda', 0)
                if ebitda is None: ebitda = 0
                est_ebitda = "Sólido" if ebitda > 0 else "RIESGO (Negativo)"
                icon_ebitda = "✅" if ebitda > 0 else "⚠️"
                
                # --- LÓGICA DE ESTADOS V10 ---
                est_m = "DESCUENTO" if margen > 15 else "CARO"
                est_r = "SOBREVENTA" if rsi_v < 35 else ("SOBRECOMPRA" if rsi_v > 65 else "NEUTRAL")
                est_t = "ALCISTA" if p_act > sma_v else "BAJISTA"
                estrategia = "REBOTE" if rsi_v < 40 else "CONTINUACION"

                # --- REPORTE VISUAL (CONSOLA) ---
                st.markdown(f"### 🏢 {info.get('longName', ticker_final)}")
                st.markdown(f"**📡 ESTRATEGIA: {estrategia} (Acción en {est_m.lower()})**")
                
                reporte_consola = f"""
=================================================================
                  MÉTRICA           VALOR       ESTADO
-----------------------------------------------------------------
            Precio Actual         ${p_act:.2f}    Cotizando
Precio Justo de la Acción         ${p_justo:.2f}   Referencia
              Margen Seg.           {margen:.1f}%       {"✅" if est_m=="DESCUENTO" else "❌"} {est_m}
                RSI (14d)            {rsi_v:.1f}  {"📉" if rsi_v<35 else "⚖️"} {est_r}
                  SMA 200         ${sma_v:.2f}   {"🚀" if est_t=="ALCISTA" else "⚠️"} {est_t}
                   EBITDA          {ebitda:,}       {icon_ebitda} {est_ebitda}
-----------------------------------------------------------------
📍 NIVELES DE COMPRA:  1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
"""
                st.code(reporte_consola, language="text")

                # --- GRÁFICO INTERACTIVO ---
                fig = go.Figure(data=[go.Candlestick(
                    x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Precio"
                )])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No se encontraron datos para este Ticker en este mercado.")
