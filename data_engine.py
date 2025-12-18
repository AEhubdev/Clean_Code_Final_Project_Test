import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


@st.cache_data(ttl=60)  # Refreshes every minute
def get_gold_data(interval_name="1 Day"):
    interval_code = config.TIMEFRAME_OPTIONS.get(interval_name, "1d")

    # CRITICAL FIX: Intraday (15m, 1h) MUST use 60d period or Yahoo returns empty data
    if interval_code in ["15m", "1h", "30m", "5m"]:
        period = "60d"
    else:
        period = "max"

    df = yf.download(config.TICKER, period=period, interval=interval_code, auto_adjust=False)

    if df.empty: return pd.DataFrame(), 0.0, [], 0.0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # --- INDICATORS ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['StdDev'] = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (df['StdDev'] * 2)
    df['BB_L'] = df['MA20'] - (df['StdDev'] * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    k_p, d_p = 14, 3
    df['Stoch_K'] = 100 * ((df['Close'] - df['Low'].rolling(k_p).min()) / (
                df['High'].rolling(k_p).max() - df['Low'].rolling(k_p).min() + 1e-10))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_p).mean()

    # --- SIGNAL LOGIC (Adjusted for better visibility) ---
    # Buy when RSI < 40 (Oversold territory) AND MACD Histogram turns positive
    is_buy_zone = (df['RSI'] < 40) & (df['MACD_Hist'] > 0)
    # Sell when RSI > 60 (Overbought territory) AND MACD Histogram turns negative
    is_sell_zone = (df['RSI'] > 60) & (df['MACD_Hist'] < 0)

    # Only show the arrow on the EXACT candle the trend starts
    df['Buy_Signal'] = (is_buy_zone & ~is_buy_zone.shift(1).fillna(False).astype(bool))
    df['Sell_Signal'] = (is_sell_zone & ~is_sell_zone.shift(1).fillna(False).astype(bool))

    # Live Price & News
    current_price = float(df['Close'].iloc[-1])
    news = []
    try:
        news = yf.Search("Gold Price", news_count=5).news
    except:
        pass

    # YTD Start
    try:
        y_df = yf.download(config.TICKER, start=f"{datetime.now().year}-01-01", progress=False)
        y_start = y_df['Close'].iloc[0]
    except:
        y_start = df['Close'].iloc[0]

    return df, current_price, news, float(y_start)


def calculate_metrics(price, df_full, ytd_start):
    try:
        w_c = ((price - df_full['Close'].iloc[-5]) / df_full['Close'].iloc[-5]) * 100
        m_c = ((price - df_full['Close'].iloc[-21]) / df_full['Close'].iloc[-21]) * 100
        ytd_c = ((price - ytd_start) / ytd_start) * 100
        vol = df_full['Close'].pct_change().tail(30).std() * np.sqrt(252) * 100
        return w_c, m_c, ytd_c, vol
    except:
        return 0.0, 0.0, 0.0, 0.0