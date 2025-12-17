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

    # Calculate indicators on the full dataset
    df['MA20'] = df['Close'].rolling(window=config.MA_SHORT).mean()
    df['MA50'] = df['Close'].rolling(window=config.MA_LONG).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
                df['High'].rolling(14).max() - df['Low'].rolling(14).min())

    try:
        news = yf.Search(config.ASSET_NAME, news_count=8).news
    except:
        news = []

    return df.ffill().dropna(), news


def get_simulation_metrics(current_idx, df_full):
    """Calculates metrics relative to the current step in time."""
    curr_price = float(df_full['Close'].iloc[current_idx])

    # Week change (5 trading days ago)
    prev_w = float(df_full['Close'].iloc[max(0, current_idx - 5)])
    w_c = ((curr_price - prev_w) / prev_w) * 100

    # Month change (21 trading days ago)
    prev_m = float(df_full['Close'].iloc[max(0, current_idx - 21)])
    m_c = ((curr_price - prev_m) / prev_m) * 100

    # Annualized Volatility
    vol = np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(252) * 100

    return curr_price, w_c, m_c, vol