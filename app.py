import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")
st.title("🛰️ Terminal V10 Pro by marto")

# --- NAVEGACIÓN (Simplificada a 2 herramientas) ---
tab1, tab2 = st.tabs(["🔍 AUDITORIA 360", "🌡️ SENTIMIENTO"])

# --- TAB 1: AUDITORIA (ANÁLISIS DE PRECISIÓN) ---
with tab1:
    st.subheader("Auditoría Individual de Activos")
    
    # Controles de entrada
    c_i1, c_i2 = st.columns([1, 2])
    with c_i1: 
        mkt = st.radio("Selecciona Mercado:", ["EUA", "México (.MX)"], horizontal=True)
    with c_i2: 
        tk_in = st.text_input("Ingresa Ticker (ej: AMD, NVDA, WALMEX):", "AMD").upper()

    ticker_final = tk_in if mkt == "EUA" else (f"{tk_in}.MX" if ".MX" not in tk_in else tk_in)

    if st.button("🔍 INICIAR AUDITORÍA V10", use_container_width=True):
        with st.spinner(f'Analizando {ticker_final}...'):
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
                # Precio justo basado en Target de analistas o métrica V10 (PE * EPS)
                p_justo = info.get('targetMeanPrice') or (info.get('forwardPE', 15) * info.get('forwardEps', 1))
                margen = ((p_justo - p_act) / p_act) * 100
                ebitda = info.get('ebitda', 0) or 0
                
                # Definición de Estados
                est_m = "DESCUENTO" if margen > 15 else "PRECIO ALTO"
                est_r = "SOBREVENTA" if rsi_v < 35 else ("SOBRECOMPRA" if rsi_v > 65 else "NEUTRAL")
                est_t = "ALCISTA" if p_act > sma_v else "BAJISTA"
                est_e = "Sólido" if ebitda > 0 else "RIESGO"

                # Título del Activo
                st.markdown(f"### 🏢 {info.get('longName', ticker_final)}")
                
                # --- REPORTE ESTILO CONSOLA ---
                reporte = f"""
=================================================================
                  MÉTRICA           VALOR       ESTADO
-----------------------------------------------------------------
            Precio Actual         ${p_act:>8.2f}    Cotizando
Precio Justo de la Acción         ${p_justo:>8.2f}    Referencia
              Margen Seg.              {margen:>7.1f}%       {"✅" if margen > 15 else "❌"} {est_m}
                RSI (14d)               {rsi_v:>7.1f}  {"📉" if rsi_v<35 else "⚖️"} {est_r}
                  SMA 200         ${sma_v:>8.2f}    {"🚀" if p_act > sma_v else "⚠️"} {est_t}
                   EBITDA          {ebitda:>14,}       {"✅" if ebitda > 0 else "⚠️"} {est_e}
-----------------------------------------------------------------
📍 NIVELES DE COMPRA:  1: ${p_act*0.96:.2f} | 2: ${p_act*0.92:.2f} | 3: ${p_act*0.88:.2f}
=================================================================
"""
                st.code(reporte, language="text")

                # --- GRÁFICO TÉCNICO ---
                fig = go.Figure(data=[go.Candlestick(
                    x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Precio"
                )])
                fig.add_trace(go.Scatter(x=h.index, y=h['SMA200'], line=dict(color='orange', width=2), name="SMA 200"))
                
                fig.update_layout(
                    template="plotly_dark", 
                    height=500, 
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No se encontraron datos. Verifica el Ticker.")

# --- TAB 2: SENTIMIENTO (EL PULSO DEL MERCADO) ---
with tab2:
    st.subheader("Indicador de Sentimiento Global (SPY)")
    
    if st.button("🌡️ MEDIR PÁNICO / CODICIA", use_container_width=True):
        with st.spinner('Calculando...'):
            spy = yf.Ticker("SPY")
            spy_h = spy.history(period="1y")
            spy_h['RSI'] = ta.rsi(spy_h['Close'], length=14)
            val = spy_h['RSI'].iloc[-1]
            
            # Lógica de color y etiqueta
            if val < 30: etiq, col = "PÁNICO EXTREMO", "red"
            elif val < 45: etiq, col = "MIEDO", "orange"
            elif val < 60: etiq, col = "NEUTRAL", "gray"
            elif val < 75: etiq, col = "CODICIA", "lightgreen"
            else: etiq, col = "EUFORIA EXTREMA", "green"

            st.metric("RSI del Mercado (SPY)", f"{val:.2f}", etiq)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': col},
                    'steps': [
                        {'range': [0, 30], 'color': "red"},
                        {'range': [30, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "green"}
                    ]
                }
            ))
            fig_gauge.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.info("Estrategia V10: Comprar en Pánico (Rojo) / Cautela en Euforia (Verde).")
