import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def fetch_market_data():
    df = yf.download(config.TICKER_SYMBOL, start=config.DATA_START_DATE)

    # Critical fix for yfinance multi-index format
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # --- INDICATORS ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # Bollinger Bands
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    try:
        news = yf.Search(config.ASSET_NAME, news_count=8).news
    except:
        news = []

    return df.dropna(), news


def get_metrics_at_point(idx, df_full):
    row = df_full.iloc[idx]
    price = float(row['Close'])
    prev_w = float(df_full['Close'].iloc[max(0, idx - 5)])
    w_c = ((price - prev_w) / prev_w) * 100
    prev_m = float(df_full['Close'].iloc[max(0, idx - 21)])
    m_c = ((price - prev_m) / prev_m) * 100
    vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
    return price, w_c, m_c, vol