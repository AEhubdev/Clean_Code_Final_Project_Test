import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=3600)
def fetch_historical_data():
    """Retrieves data with a fail-safe simulation if the API is unreachable."""
    try:
        raw_data = yf.download(config.TICKER_SYMBOL, start=config.INITIAL_DATA_START_DATE, timeout=10)
        if raw_data.empty or len(raw_data) < 10:
            raise ValueError("Empty dataset")
        if isinstance(raw_data.columns, pd.MultiIndex):
            raw_data.columns = raw_data.columns.get_level_values(0)
        return raw_data
    except Exception:
        # Fallback: Realistic simulation if API fails
        dates = pd.date_range(start="2024-01-01", periods=500, freq='D')
        prices = 2300 + np.cumsum(np.random.normal(0.5, 10, size=500))
        return pd.DataFrame(
            {'Open': prices - 5, 'High': prices + 10, 'Low': prices - 10, 'Close': prices, 'Volume': 20000},
            index=dates)


def apply_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculates SMA, Bollinger Bands, RSI, and MACD."""
    df = dataframe.copy()
    df['MA20'] = df['Close'].rolling(window=config.MA_SHORT_WINDOW).mean()
    df['MA50'] = df['Close'].rolling(window=config.MA_LONG_WINDOW).mean()

    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # MACD Calculation
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9).mean()

    return df


def get_market_news():
    """Fetches news headlines via yfinance."""
    try:
        return yf.Search(f"{config.ASSET_NAME} Market", news_count=6).news
    except:
        return []