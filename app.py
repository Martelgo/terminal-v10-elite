CÓDIGO LIMPIO PARA app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import plotly.express as px

Configuración de página para móvil
st.set_page_config(page_title="V10 Elite Terminal", layout="wide")

--- UNIVERSO DE ACTIVOS ---
universo = {
"Tecnologia": ["MSFT", "CRM", "ADBE", "ORCL", "SAP"],
"Chips": ["AMD", "TSM", "NVDA", "ASML", "AVGO"],
"Salud": ["NVO", "LLY", "UNH", "PFE"],
"Consumo": ["AMZN", "BABA", "MELI", "NKE"],
"Finanzas": ["PYPL", "V", "MA", "BAC"]
}

@st.cache_data(ttl=600)
def cargar_datos_radar():
datos = []
for sector, tickers in universo.items():
for t in tickers:
try:
stock = yf.Ticker(t)
px_val = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice', 0)
target = stock.info.get('targetMeanPrice') or (stock.info.get('forwardPE', 15) * stock.info.get('forwardEps', 1))
margen = ((target - px_val) / target) * 100 if target else 0
datos.append({"Ticker": t, "Sector": sector, "Precio": px_val, "Margen %": margen})
except: continue
return pd.DataFrame(datos)

--- INTERFAZ PRINCIPAL ---
st.title("🛰️ Terminal V10: Elite")
tab1, tab2, tab3 = st.tabs(["🎯 RADAR", "🔥 MAPA", "🔍 AUDITORIA"])

--- TAB 1: RADAR ---
with tab1:
df_radar = cargar_datos_radar()
if not df_radar.empty:
for sector in universo.keys():
st.subheader(f"Sector: {sector}")
sector_df = df_radar[df_radar['Sector'] == sector].sort_values(by="Margen %", ascending=False)
st.table(sector_df[['Ticker', 'Precio', 'Margen %']].style.format({"Precio": "{:.2f}", "Margen %": "{:.2f}%"}))

--- TAB 2: MAPA ---
with tab2:
if not df_radar.empty:
fig_mapa = px.treemap(df_radar, path=['Sector', 'Ticker'], values='Precio',
color='Margen %', color_continuous_scale='RdYlGn',
title="Mapa de Calor: Oportunidades")
st.plotly_chart(fig_mapa, use_container_width=True)

--- TAB 3: AUDITORIA ---
with tab3:
tk = st.text_input("Introduce Ticker para Auditoria:", "MSFT").upper()
if tk:
with st.spinner('Analizando...'):
acc = yf.Ticker(tk)
h = acc.history(period="1y")
info = acc.info

========================================================== METRICA            VALOR            ESTADO
Precio Actual            ${p_act:.2f}        Cotizando Precio Justo             ${p_justo:.2f}        Referencia Margen Seg.              {margen:.1f}%        {est_margen} RSI (14d)                {rsi_v:.1f}         {est_rsi} SMA 200                  ${sma_v:.2f}        {est_tend} EBITDA                   {ebitda:,}        Solido
ESTRATEGIA V10: {estrategia} NIVELES DE COMPRA:  1: ${p_act0.96:.2f} | 2: ${p_act0.92:.2f} | 3: ${p_act*0.88:.2f}
