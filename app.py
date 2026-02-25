import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="V10 Elite", layout="wide")

universo = {
"Tecnologia": ["MSFT", "CRM", "ADBE", "ORCL", "SAP"],
"Chips": ["AMD", "TSM", "NVDA", "ASML", "AVGO"],
"Salud": ["NVO", "LLY", "UNH", "PFE"],
"Consumo": ["AMZN", "BABA", "MELI", "NKE"]
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
datos.append({"Ticker": t, "Sector": sector, "Precio": p, "Margen": m})
except: continue
return pd.DataFrame(datos)

st.title("V10 Terminal")
tab1, tab2, tab3 = st.tabs(["RADAR", "MAPA", "AUDITORIA"])

with tab1:
df = cargar_radar()
if not df.empty:
for s in universo.keys():
st.write(f"### {s}")
st.dataframe(df[df['Sector'] == s])

with tab2:
if not df.empty:
fig = px.treemap(df, path=['Sector', 'Ticker'], values='Precio', color='Margen', color_continuous_scale='RdYlGn')
st.plotly_chart(fig, use_container_width=True)

with tab3:
tk = st.text_input("Ticker:", "MSFT").upper()
if tk:
acc = yf.Ticker(tk)
h = acc.history(period="1y")
if not h.empty:
h['RSI'] = ta.rsi(h['Close'], length=14)
h['SMA200'] = ta.sma(h['Close'], length=200)
p_now = h['Close'].iloc[-1]
rsi_now = h['RSI'].iloc[-1]
