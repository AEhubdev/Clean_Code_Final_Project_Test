import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def fetch_market_data():
    ticker = yf.Ticker(config.TICKER_SYMBOL)
    # auto_adjust=False ensures we get the actual $4,300 price, not adjusted $2,600
    df = ticker.history(start=config.DATA_START_DATE, interval="1d", auto_adjust=False)

    if df.empty:
        st.error("No data found. Check your internet or Ticker Symbol.")
        return pd.DataFrame(), []

    # FIX FOR JAN 2025 BREAK: Remove Multi-Index if Yahoo added it
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Standardize column names
    df.columns = [str(c).capitalize() for c in df.columns]
    df = df.ffill().dropna()

    # --- INDICATORS (Now safe from column errors) ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    try:
        news = ticker.news
    except:
        news = []

    return df.dropna(), news


def get_metrics_at_point(idx, df_full):
    row = df_full.iloc[idx]
    price = float(row['Close'])
    # Weekly/Monthly Change logic
    prev_w = float(df_full['Close'].iloc[max(0, idx - 5)])
    w_c = ((price - prev_w) / prev_w) * 100
    prev_m = float(df_full['Close'].iloc[max(0, idx - 21)])
    m_c = ((price - prev_m) / prev_m) * 100
    vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
    return price, w_c, m_c, vol