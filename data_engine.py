import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


@st.cache_data(ttl=600)
def get_gold_data(interval_name="1 Day"):
    interval_code = config.TIMEFRAME_OPTIONS.get(interval_name, "1d")

    # Intraday needs 60d, Daily/Weekly/Monthly needs 'max'
    period = "60d" if interval_code in ["15m", "1h"] else "max"

    df = yf.download(config.TICKER, period=period, interval=interval_code, auto_adjust=False)

    if df.empty: return pd.DataFrame(), 0.0, [], 0.0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # --- Indicators ---
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

    # --- FIXED SIGNAL LOGIC ---
    # We explicitly cast to bool to avoid the "bad operand type for unary ~" error
    buy_cond = (df['RSI'] < 35) & (df['MACD_Hist'] > 0)
    sell_cond = (df['RSI'] > 65) & (df['MACD_Hist'] < 0)

    # This prevents the shift(1) from breaking on the first NaN value
    df['Buy_Signal'] = (buy_cond & ~buy_cond.shift(1).fillna(False).astype(bool))
    df['Sell_Signal'] = (sell_cond & ~sell_cond.shift(1).fillna(False).astype(bool))

    # --- Metrics Logic ---
    try:
        y_start = f"{datetime.now().year}-01-01"
        ytd_data = yf.download(config.TICKER, start=y_start, progress=False)
        ytd_start_price = ytd_data['Close'].iloc[0] if not ytd_data.empty else df['Close'].iloc[0]
    except:
        ytd_start_price = df['Close'].iloc[0]

    news_list = []
    try:
        search = yf.Search("Gold Price", news_count=8)
        news_list = search.news
    except:
        pass

    return df, float(df['Close'].iloc[-1]), news_list, float(ytd_start_price)


def calculate_metrics(price, df_full, ytd_start):
    try:
        w_idx = -5 if len(df_full) >= 5 else 0
        m_idx = -21 if len(df_full) >= 21 else 0
        w_c = ((price - df_full['Close'].iloc[w_idx]) / df_full['Close'].iloc[w_idx]) * 100
        m_c = ((price - df_full['Close'].iloc[m_idx]) / df_full['Close'].iloc[m_idx]) * 100
        ytd_c = ((price - ytd_start) / ytd_start) * 100
        vol = df_full['Close'].pct_change().tail(30).std() * np.sqrt(252) * 100
        return w_c, m_c, ytd_c, vol
    except:
        return 0.0, 0.0, 0.0, 0.0