import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def fetch_market_data():
    # Force auto_adjust=False to get the real $4300+ price
    df = yf.download(config.TICKER_SYMBOL, start=config.DATA_START_DATE, auto_adjust=False)

    # --- CRITICAL FIX: FLATTEN MULTI-INDEX ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # Calculate Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # MACD Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    try:
        news = yf.Search(config.ASSET_NAME, news_count=5).news
    except:
        news = []

    return df.dropna(), news


def get_metrics(idx, df):
    row = df.iloc[idx]
    price = float(row['Close'])
    prev_w = float(df['Close'].iloc[max(0, idx - 5)])
    w_c = ((price - prev_w) / prev_w) * 100
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100
    return price, w_c, vol