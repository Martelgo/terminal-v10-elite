import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal Elite V10", layout="wide")

# --- FUNCIONES DE CÁLCULO V10 ---
def calcular_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def auditoria_v10(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    
    if hist.empty: return None

    # 1. Datos Actuales
    precio_act = hist['Close'].iloc[-1]
    
    # 2. Fundamentales (Precio Justo)
    eps = info.get('forwardEps', 1)
    pe_ratio = info.get('forwardPE', 15)
    precio_justo = eps * pe_ratio
    margen_seguridad = ((precio_justo - precio_act) / precio_justo) * 100
    ebitda = info.get('ebitda', 'N/A')

    # 3. Indicadores Técnicos
    sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
    sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
    rsi = calcular_rsi(hist['Close']).iloc[-1]

    # 4. Estado de Valuación
    estado = "CARO 🔴" if precio_act > precio_justo else "BARATO 🟢"
    sobreventa = "SÍ ⚠️" if rsi < 30 else "NO"

    # 5. Estrategia V10
    if precio_act > sma_50 and sma_50 > sma_200:
        estrategia = "CONTINUACIÓN ALCISTA 📈"
    elif precio_act < sma_50 and rsi < 35:
        estrategia = "REBOTE TÉCNICO 📉"
    else:
        estrategia = "NEUTRAL / ESPERA ⚖️"

    return {
        "Precio": precio_act, "Precio Justo": precio_justo, "Margen": margen_seguridad,
        "EBITDA": ebitda, "RSI": rsi, "SMA50": sma_50, "SMA200": sma_200,
        "Estado": estado, "Sobreventa": sobreventa, "Estrategia": estrategia, "Hist": hist
    }

# --- INTERFAZ APP ---
st.title("🛰️ Terminal V10: Auditoría Completa")

ticker_input = st.text_input("Introduce Ticker (Ej: NVO, ORCL, MSFT):", "ORCL").upper()

if ticker_input:
    res = auditoria_v10(ticker_input)
    
    if res:
        # Fila 1: Métricas Críticas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("PRECIO ACTUAL", f"${res['Precio']:.2
