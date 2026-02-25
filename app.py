import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta # Para RSI y SMA
import plotly.graph_objects as go

st.set_page_config(page_title="V10 Elite Terminal", layout="wide")

# --- LÓGICA DE CÁLCULO AVANZADO ---
def auditar_v10(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    h = stock.history(period="1y")
    
    # 1. Análisis Técnico (RSI y SMA)
    h['RSI'] = ta.rsi(h['Close'], length=14)
    h['SMA_200'] = ta.sma(h['Close'], length=200)
    rsi_actual = h['RSI'].iloc[-1]
    sma_200 = h['SMA_200'].iloc[-1]
    precio_actual = h['Close'].iloc[-1]

    # 2. Análisis Fundamental (Precio Justo y EBITDA)
    ebitda = info.get('ebitda', "N/A")
    fwd_pe = info.get('forwardPE', 15)
    eps = info.get('forwardEps', 1)
    precio_justo = fwd_pe * eps
    margen_seguridad = ((precio_justo - precio_actual) / precio_justo) * 100

    # 3. Estrategia V10
    condicion = "SOBREVENTA" if rsi_actual < 30 else "SOBRECOMPRA" if rsi_actual > 70 else "NEUTRAL"
    estrategia = "REBOTE" if precio_actual < sma_200 and rsi_actual < 35 else "CONTINUACIÓN" if precio_actual > sma_200 else "ESPERAR"

    return {
        "precio": precio_actual, "rsi": rsi_actual, "sma": sma_200,
        "justo": precio_justo, "margen": margen_seguridad, "ebitda": ebitda,
        "condicion": condicion, "estrategia": estrategia, "historia": h
    }

# --- INTERFAZ ---
st.title("🛰️ Terminal V10 Pro")
tab1, tab2, tab3 = st.tabs(["🎯 RADAR", "🔥 MAPA", "🔍 AUDITORÍA 360°"])

with tab3:
    tk = st.text_input("Introduce Ticker:", "ORCL").upper()
    data = auditar_v10(tk)
    
    # Fila 1: Precios y Márgenes
    col1, col2, col3 = st.columns(3)
    col1.metric("Precio Actual", f"${data['precio']:.2f}")
    col2.metric("Precio Justo", f"${data['justo']:.2f}")
    col3.metric("Margen Seg.", f"{data['margen']:.2f}%", delta=f"{data['margen']:.2f}%")

    # Fila 2: Indicadores Técnicos
    c1, c2, c3 = st.columns(3)
    c1.info(f"**RSI:** {data['rsi']:.2f} ({data['condicion']})")
    c2.warning(f"**SMA 200:** ${data['sma']:.2f}")
    c3.success(f"**EBITDA:** {data['ebitda']}")

    # Fila 3: La Estrategia
    st.subheader(f"⚡ Estrategia Sugerida: {data['estrategia']}")
    
    # Gráfico con SMA 200
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data['historia'].index, open=data['historia']['Open'], 
                  high=data['historia']['High'], low=data['historia']['Low'], close=data['historia']['Close'], name="Precio"))
    fig.add_trace(go.Scatter(x=data['historia'].index, y=data['historia']['SMA_200'], line=dict(color='orange', width=2), name="SMA 200"))
    st.plotly_chart(fig, use_container_width=True)
