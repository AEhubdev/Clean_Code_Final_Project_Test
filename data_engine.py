import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=600)
def get_gold_data(interval_name="1 Day"):
    interval_code = config.TIMEFRAME_OPTIONS.get(interval_name, "1d")
    period = "60d" if interval_code in ["15m", "1h"] else "max"

    df = yf.download(config.TICKER, period=period, interval=interval_code, auto_adjust=False)
    if df.empty: return pd.DataFrame(), 0.0, []
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # --- BOLLINGER BANDS ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['StdDev'] = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (df['StdDev'] * 2)
    df['BB_L'] = df['MA20'] - (df['StdDev'] * 2)

    # --- RSI & MACD ---
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # --- SIGNALS ---
    buy_cond = (df['RSI'] < 30) & (df['MACD_Hist'] > 0)
    sell_cond = (df['RSI'] > 70) & (df['MACD_Hist'] < 0)
    df['Buy_Signal'] = buy_cond & ~buy_cond.shift(1).fillna(False)
    df['Sell_Signal'] = sell_cond & ~sell_cond.shift(1).fillna(False)

    news_list = []
    try:
        search = yf.Search("Gold Price", news_count=8)
        news_list = search.news
    except:
        pass

    return df, float(df['Close'].iloc[-1]), news_list


def calculate_metrics(price, df_full):
    try:
        w_c = ((price - df_full['Close'].iloc[-5]) / df_full['Close'].iloc[-5]) * 100
        m_c = ((price - df_full['Close'].iloc[-21]) / df_full['Close'].iloc[-21]) * 100
        vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
        return w_c, m_c, 0.0, vol
    except:
        return 0.0, 0.0, 0.0, 0.0