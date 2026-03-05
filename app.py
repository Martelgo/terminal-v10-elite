import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go

# -------------------------------
# CONFIGURACIÓN
# -------------------------------

st.set_page_config(
    page_title="Terminal V10 Pro",
    layout="wide"
)

st.markdown("# 🛰 Terminal V10 Pro")

# -------------------------------
# FUNCIONES UNIVERSO DE MERCADO
# -------------------------------

@st.cache_data
def get_sp500():

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    table = pd.read_html(url)

    df = table[0]

    return df["Symbol"].tolist()


@st.cache_data
def get_nasdaq100():

    url = "https://en.wikipedia.org/wiki/Nasdaq-100"

    table = pd.read_html(url)

    df = table[4]

    return df["Ticker"].tolist()


def get_bmv():

    return [
        "WALMEX.MX",
        "AMX.MX",
        "GMEXICOB.MX",
        "FEMSAUBD.MX",
        "GFNORTEO.MX",
        "BIMBOA.MX",
        "CEMEXCPO.MX"
    ]


def universo_total():

    sp500 = get_sp500()

    nasdaq = get_nasdaq100()

    bmv = get_bmv()

    return list(set(sp500 + nasdaq + bmv))


# -------------------------------
# SCORE INTERPRETACIÓN
# -------------------------------

def interpretar_score(score):

    if score >= 9:
        return "🟢 COMPRA CONFIRMADA"

    elif score == 8:
        return "🟠 SECTOR PREPARADO"

    elif score == 7:
        return "🟡 VIGILAR"

    else:
        return "-"


# -------------------------------
# MOTOR DEL SCANNER
# -------------------------------

@st.cache_data(ttl=600)
def scan_market():

    tickers = universo_total()

    data = yf.download(
        tickers,
        period="5d",
        interval="15m",
        group_by="ticker",
        threads=True
    )

    resultados = []

    for ticker in tickers:

        try:

            df = data[ticker].dropna()

            if len(df) < 60:
                continue

            df["EMA9"] = ta.ema(df["Close"], length=9)
            df["EMA50"] = ta.ema(df["Close"], length=50)
            df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"])

            df["VolAvg"] = df["Volume"].rolling(20).mean()

            price = df["Close"].iloc[-1]
            ema9 = df["EMA9"].iloc[-1]
            ema50 = df["EMA50"].iloc[-1]

            volume = df["Volume"].iloc[-1]
            volavg = df["VolAvg"].iloc[-1]

            score = 0
            setup = None

            if price > ema9 and ema9 > ema50:

                score += 3
                setup = "Reclaim EMA9"

            if abs(price - ema50)/ema50 <= 0.01:

                score += 3
                setup = "Pullback EMA50"

            if volume > volavg:

                score += 1

            if price > df["Close"].iloc[-2]:

                score += 1

            if df["ATR"].iloc[-1] > df["ATR"].rolling(20).mean().iloc[-1] * 1.5:

                score += 2

            if score >= 7:

                resultados.append({
                    "Ticker": ticker,
                    "Setup": setup,
                    "Score": score,
                    "Estado": interpretar_score(score),
                    "Precio": round(price,2)
                })

        except:
            continue

    return pd.DataFrame(resultados)


# -------------------------------
# SIDEBAR NAVEGACIÓN
# -------------------------------

menu = st.sidebar.radio(
    "Navegación",
    [
        "Dashboard",
        "Mercado",
        "Scanner",
        "Oportunidades",
        "Análisis",
        "Sentimiento"
    ]
)

# -------------------------------
# DASHBOARD
# -------------------------------

if menu == "Dashboard":

    st.subheader("📊 Mercado Hoy")

    col1, col2, col3 = st.columns(3)

    sp500 = yf.Ticker("^GSPC").history(period="1d")["Close"].pct_change().iloc[-1]*100
    nasdaq = yf.Ticker("^IXIC").history(period="1d")["Close"].pct_change().iloc[-1]*100
    vix = yf.Ticker("^VIX").history(period="1d")["Close"].pct_change().iloc[-1]*100

    col1.metric("S&P500",f"{sp500:.2f}%")
    col2.metric("NASDAQ",f"{nasdaq:.2f}%")
    col3.metric("VIX",f"{vix:.2f}%")

    st.subheader("🔥 Oportunidades del mercado")

    if st.button("Escanear mercado"):

        df = scan_market()

        st.dataframe(df.sort_values("Score",ascending=False))


# -------------------------------
# SCANNER
# -------------------------------

elif menu == "Scanner":

    st.subheader("⚡ Scanner institucional")

    if st.button("Ejecutar scanner"):

        df = scan_market()

        st.dataframe(df.sort_values("Score",ascending=False), use_container_width=True)


# -------------------------------
# OPORTUNIDADES
# -------------------------------

elif menu == "Oportunidades":

    st.subheader("🔥 Top oportunidades")

    df = scan_market()

    if not df.empty:

        st.dataframe(df.sort_values("Score",ascending=False), use_container_width=True)


# -------------------------------
# ANALISIS
# -------------------------------

elif menu == "Análisis":

    ticker = st.text_input("Ticker","NVDA")

    data = yf.Ticker(ticker).history(period="1y")

    data["EMA200"] = ta.ema(data["Close"], length=200)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"]
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["EMA200"],
        name="EMA200"
    ))

    st.plotly_chart(fig, use_container_width=True)


# -------------------------------
# SENTIMIENTO
# -------------------------------

elif menu == "Sentimiento":

    spy = yf.Ticker("SPY").history(period="1y")

    spy["RSI"] = ta.rsi(spy["Close"], length=14)

    rsi = spy["RSI"].iloc[-1]

    if rsi < 30:

        estado = "PÁNICO"

    elif rsi < 45:

        estado = "MIEDO"

    elif rsi < 60:

        estado = "NEUTRAL"

    elif rsi < 75:

        estado = "CODICIA"

    else:

        estado = "EUFORIA"

    st.metric("Sentimiento mercado", estado)
