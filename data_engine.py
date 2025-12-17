import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=3600)
def fetch_historical_data():
    """Retrieves historical data to seed the simulation."""
    raw_data = yf.download(config.TICKER_SYMBOL, start=config.INITIAL_DATA_START_DATE)
    if isinstance(raw_data.columns, pd.MultiIndex):
        raw_data.columns = raw_data.columns.get_level_values(0)
    return raw_data


def apply_technical_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculates all statistical indicators required for the algorithm."""
    # Moving Averages
    dataframe['MA20'] = dataframe['Close'].rolling(window=config.MA_SHORT_WINDOW).mean()
    dataframe['MA50'] = dataframe['Close'].rolling(window=config.MA_LONG_WINDOW).mean()

    # Bollinger Bands
    rolling_std = dataframe['Close'].rolling(window=20).std()
    dataframe['BB_UPPER'] = dataframe['MA20'] + (rolling_std * 2)
    dataframe['BB_LOWER'] = dataframe['MA20'] - (rolling_std * 2)

    # RSI
    delta = dataframe['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    rs_value = gain / loss
    dataframe['RSI'] = 100 - (100 / (1 + rs_value))

    # MACD
    ema_12 = dataframe['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = dataframe['Close'].ewm(span=26, adjust=False).mean()
    dataframe['MACD'] = ema_12 - ema_26
    dataframe['MACD_SIGNAL'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()
    dataframe['MACD_HIST'] = dataframe['MACD'] - dataframe['MACD_SIGNAL']

    return dataframe


def fetch_market_news():
    """Queries latest headlines for the commodity."""
    try:
        search_result = yf.Search(f"{config.ASSET_NAME} Market", news_count=5)
        return search_result.news
    except Exception:
        return []