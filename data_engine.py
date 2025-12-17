import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def fetch_market_data():
    df = yf.download(config.TICKER_SYMBOL, start=config.DATA_START_DATE)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # Calculations
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

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
    safe_idx = min(idx, len(df_full) - 1)
    row = df_full.iloc[safe_idx]
    price = float(row['Close'])

    # Relative changes
    prev_w = float(df_full['Close'].iloc[max(0, safe_idx - 5)])
    w_c = ((price - prev_w) / prev_w) * 100 if prev_w != 0 else 0

    prev_m = float(df_full['Close'].iloc[max(0, safe_idx - 21)])
    m_c = ((price - prev_m) / prev_m) * 100 if prev_m != 0 else 0

    vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
    return price, w_c, m_c, vol