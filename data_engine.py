import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def get_market_data():
    # Fetching extra data to ensure indicators (MA50) have enough lead time
    df = yf.download(config.TICKER_SYMBOL, start=config.INITIAL_DATA_START_DATE)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Clean any NaN values that break calculations
    df = df.ffill().dropna()

    # Indicators
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

    try:
        news = yf.Search(config.ASSET_NAME, news_count=8).news
    except:
        news = []

    return df, news


def calculate_top_metrics(current_df):
    """Calculates metrics using only the available 'simulated' window."""
    if len(current_df) < 2:
        return 0, 0, 0, 0

    current_price = float(current_df['Close'].iloc[-1])

    # Weekly (5 steps back)
    prev_w = float(current_df['Close'].iloc[-5]) if len(current_df) > 5 else float(current_df['Close'].iloc[0])
    w_c = ((current_price - prev_w) / prev_w) * 100

    # Monthly (21 steps back)
    prev_m = float(current_df['Close'].iloc[-21]) if len(current_df) > 21 else float(current_df['Close'].iloc[0])
    m_c = ((current_price - prev_m) / prev_m) * 100

    # Annual Volatility
    vol = np.log(current_df['Close'] / current_df['Close'].shift(1)).std() * np.sqrt(252) * 100

    return current_price, w_c, m_m_c, vol  # Note: Using placeholder for YTD to keep it simple and stable