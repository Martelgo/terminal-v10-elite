import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go

st.set_page_config(page_title="Terminal V10 Pro", layout="wide")

st.title("🛰 Terminal V10 Pro")

# ===============================
# FUNCION CAMBIO INDICES
# ===============================

def get_index_change(symbol):

    try:
        data = yf.Ticker(symbol).history(period="2d")

        if len(data) < 2:
            return 0

        change = ((data["Close"].iloc[-1] - data["Close"].iloc[-2]) /
                  data["Close"].iloc[-2]) * 100

        return round(change, 2)

    except:
        return 0


# ===============================
# UNIVERSO DE ACCIONES
# ===============================

@st.cache_data
def get_sp500():

    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        table = pd.read_html(url)
        df = table[0]
        return df["Symbol"].tolist()

    except:
        return []


@st.cache_data
def get_nasdaq100():

    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        table = pd.read_html(url)
        df = table[4]
        return df["Ticker"].tolist()

    except:
        return []


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


# ===============================
# SCORE
# ===============================

def interpretar_score(score):

    if score >= 9:
        return "🟢 COMPRA CONFIRMADA"

    elif score == 8:
        return "🟠 SECTOR PREPARADO"

    elif score == 7:
        return "🟡 VIGILAR"

    else:
        return "-"


# ===============================
# SCANNER
# ===============================

@st.cache_data(ttl=600)
def scan_market():

    tickers = universo_total()

    resultados = []

    for ticker in tickers:

        try:

            df = yf.download(
                ticker,
                period="5d",
                interval="15m",
                progress=False
            )

            if df.empty or len(df) < 60:
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

            if abs(price - ema50) / ema50 <= 0.01:
                score += 3
                setup = "Pullback EMA50"

            if volume > volavg:
                score += 1

            if price > df["Close"].iloc[-2]:
                score += 1

            atr_mean = df["ATR"].rolling(20).mean().iloc[-1]

            if df["ATR"].iloc[-1] > atr_mean * 1.5:
                score += 2

            if score >= 7:

                resultados.append({
                    "Ticker": ticker,
                    "Setup": setup,
                    "Score": score,
                    "Estado": interpretar_score(score),
                    "Precio": round(price, 2)
                })

        except:
            continue

    return pd.DataFrame(resultados)


# ===============================
# SIDEBAR
# ===============================

menu = st.sidebar.radio(
    "Navegación",
    [
        "Dashboard",
        "Scanner",
        "Oportunidades",
        "Análisis",
        "Sentimiento"
    ]
)

# ===============================
# DASHBOARD
# ===============================

if menu == "Dashboard":

    st.subheader("📊 Mercado Hoy")

    col1, col2, col3 = st.columns(3)

    sp500 = get_index_change("^GSPC")
    nasdaq = get_index_change("^IXIC")
    vix = get_index_change("^VIX")

    col1.metric("S&P500", f"{sp500}%")
    col2.metric("NASDAQ", f"{nasdaq}%")
    col3.metric("VIX", f"{vix}%")

    st.subheader("🔥 Oportunidades del mercado")

    if st.button("Escanear mercado"):

        with st.spinner("Escaneando mercado..."):

            df = scan_market()

        if not df.empty:
            st.dataframe(df.sort_values("Score", ascending=False),
                         use_container_width=True)
        else:
            st.warning("No se detectaron oportunidades")


# ===============================
# SCANNER
# ===============================

elif menu == "Scanner":

    st.subheader("⚡ Scanner institucional")

    if st.button("Ejecutar scanner"):

        with st.spinner("Analizando mercado..."):

            df = scan_market()

        if not df.empty:

            st.dataframe(
                df.sort_values("Score", ascending=False),
                use_container_width=True
            )

        else:

            st.warning("No hay setups activos")


# ===============================
# OPORTUNIDADES
# ===============================

elif menu == "Oportunidades":

    st.subheader("🔥 Top oportunidades")

    df = scan_market()

    if not df.empty:

        st.dataframe(
            df.sort_values("Score", ascending=False),
            use_container_width=True
        )

    else:

        st.info("No hay oportunidades activas")


# ===============================
# ANALISIS
# ===============================

elif menu == "Análisis":

    ticker = st.text_input("Ticker", "NVDA")

    data = yf.Ticker(ticker).history(period="1y")

    if not data.empty:

        data["EMA200"] = ta.ema(data["Close"], length=200)

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Precio"
        ))

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["EMA200"],
            name="EMA200"
        ))

        fig.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    else:

        st.warning("No se pudieron descargar datos")


# ===============================
# SENTIMIENTO
# ===============================

elif menu == "Sentimiento":

    spy = yf.Ticker("SPY").history(period="1y")

    spy["RSI"] = ta.rsi(spy["Close"], length=14)

    rsi = spy["RSI"].iloc[-1]

    if rsi < 30:
        estado = "🔴 PÁNICO"

    elif rsi < 45:
        estado = "🟠 MIEDO"

    elif rsi < 60:
        estado = "⚪ NEUTRAL"

    elif rsi < 75:
        estado = "🟢 CODICIA"

    else:
        estado = "🟢 EUFORIA"

    st.metric("Sentimiento mercado", estado)
