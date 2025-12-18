import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


@st.cache_data(ttl=600)
def get_gold_data(interval_name="1 Day"):
    interval_code = config.TIMEFRAME_OPTIONS.get(interval_name, "1d")
    period = "60d" if interval_code in ["15m", "1h"] else "max"

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
    df['MACD_Hist'] = ema12 - ema26 - (ema12 - ema26).ewm(span=9, adjust=False).mean()

    # --- THE LOGIC FIX ---
    # We define the state (is it overbought?) and then find the MOMENT it enters that state
    is_overbought = (df['RSI'] > 65) & (df['MACD_Hist'] < 0)
    is_oversold = (df['RSI'] < 35) & (df['MACD_Hist'] > 0)

    # Only True on the first candle the condition is met
    df['Buy_Signal'] = is_oversold & ~is_oversold.shift(1).fillna(False)
    df['Sell_Signal'] = is_overbought & ~is_overbought.shift(1).fillna(False)

    # --- NEWS & YTD ---
    try:
        y_start = f"{datetime.now().year}-01-01"
        ytd_data = yf.download(config.TICKER, start=y_start, progress=False)
        ytd_start_price = ytd_data['Close'].iloc[0] if not ytd_data.empty else df['Close'].iloc[0]
    except:
        ytd_start_price = df['Close'].iloc[0]

    news_list = []
    try:
        news_list = yf.Search("Gold Price", news_count=8).news
    except:
        pass

    return df, float(df['Close'].iloc[-1]), news_list, float(ytd_start_price)


def calculate_metrics(price, df_full, ytd_start):
    try:
        w_idx, m_idx = (-5 if len(df_full) >= 5 else 0), (-21 if len(df_full) >= 21 else 0)
        w_c = ((price - df_full['Close'].iloc[w_idx]) / df_full['Close'].iloc[w_idx]) * 100
        m_c = ((price - df_full['Close'].iloc[m_idx]) / df_full['Close'].iloc[m_idx]) * 100
        ytd_c = ((price - ytd_start) / ytd_start) * 100
        vol = df_full['Close'].pct_change().tail(30).std() * np.sqrt(252) * 100
        return w_c, m_c, ytd_c, vol
    except:
        return 0.0, 0.0, 0.0, 0.0