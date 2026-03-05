import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


# ==============================
# UNIVERSO DE ACTIVOS
# ==============================

sp500_sample = [
"AAPL","NVDA","MSFT","AMZN","META","AMD","AVGO","TSLA"
]

etfs = [
"SPY","QQQ","SMH","SOXL","TQQQ","SPXL"
]

mexico = [
"AMXL.MX","WALMEX.MX","GMEXICOB.MX"
]

universe = sp500_sample + etfs + mexico


# ==============================
# INDICADORES
# ==============================

def add_indicators(df):

    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    df["vol_avg"] = df["Volume"].rolling(20).mean()

    df["range"] = df["High"] - df["Low"]
    df["atr"] = df["range"].rolling(14).mean()

    df["mean"] = df["Close"].rolling(30).mean()
    df["std"] = df["Close"].rolling(30).std()

    df["zscore"] = (df["Close"] - df["mean"]) / df["std"]

    return df


# ==============================
# FILTRO DE LIQUIDEZ
# ==============================

def liquidity_filter(df):

    df["dollar_volume"] = df["Close"] * df["Volume"]

    dv = df["dollar_volume"].rolling(20).mean().iloc[-1]

    return dv >= 20_000_000


# ==============================
# CAPITULACION
# ==============================

def detect_capitulation(df):

    last = df.iloc[-1]

    rvol = last["Volume"] / last["vol_avg"]

    atr_expansion = last["atr"] > df["atr"].rolling(30).mean().iloc[-1] * 1.5

    z_cond = last["zscore"] < -2

    if rvol > 2 and atr_expansion and z_cond:
        return True

    return False


# ==============================
# ABSORCION
# ==============================

def detect_absorption(df):

    recent = df.tail(10)

    low_dump = df["Low"].iloc[-11]

    no_new_lows = recent["Low"].min() > low_dump

    range_size = (recent["High"].max() - recent["Low"].min()) / recent["Close"].iloc[-1]

    tight_range = range_size < 0.03

    volume_decline = recent["Volume"].mean() < df["Volume"].iloc[-11]

    if no_new_lows and tight_range and volume_decline:
        return True

    return False


# ==============================
# RECLAIM EMA
# ==============================

def reclaim_ema9(df):

    last = df.iloc[-1]
    prev = df.iloc[-2]

    return last["Close"] > last["EMA9"] and prev["Close"] < prev["EMA9"]


# ==============================
# RUPTURA ESTRUCTURA
# ==============================

def break_structure(df):

    recent_high = df["High"].tail(6).max()

    return df["Close"].iloc[-1] > recent_high


# ==============================
# SCORE
# ==============================

def compute_score(features):

    score = 0

    if features["trend"]:
        score += 2

    if features["correction"]:
        score += 1.5

    if features["capitulation"]:
        score += 3

    if features["absorption"]:
        score += 2

    if features["reclaim"]:
        score += 1

    if features["structure"]:
        score += 0.5

    return round(score,2)


# ==============================
# ANALISIS DE ACTIVO
# ==============================

def analyze_ticker(ticker):

    try:

        df15 = yf.download(ticker, interval="15m", period="5d", progress=False)
        df1d = yf.download(ticker, interval="1d", period="6mo", progress=False)

        df15 = add_indicators(df15)
        df1d = add_indicators(df1d)

        if not liquidity_filter(df1d):
            return None

        trend = df1d["Close"].iloc[-1] > df1d["EMA200"].iloc[-1]

        correction = (df15["Close"].max() - df15["Close"].iloc[-1]) / df15["Close"].max() > 0.08

        capitulation = detect_capitulation(df15)

        absorption = detect_absorption(df15)

        reclaim = reclaim_ema9(df15)

        structure = break_structure(df15)

        features = {
            "trend":trend,
            "correction":correction,
            "capitulation":capitulation,
            "absorption":absorption,
            "reclaim":reclaim,
            "structure":structure
        }

        score = compute_score(features)

        if score < 7:
            return None

        if score >= 9:
            state = "COMPRA CLARA"

        elif score >= 8:
            state = "PREPARAR COMPRA"

        else:
            state = "OBSERVAR"

        return {
            "ticker":ticker,
            "score":score,
            "estado":state
        }

    except:

        return None


# ==============================
# SCANNER
# ==============================

def run_scanner():

    results = []

    print("Escaneando mercado...")

    for ticker in universe:

        res = analyze_ticker(ticker)

        if res:
            results.append(res)

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.sort_values(by="score", ascending=False)

    return df


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    results = run_scanner()

    print("\nRESULTADOS\n")

    if results.empty:

        print("No hay setups detectados")

    else:

        print(results)
