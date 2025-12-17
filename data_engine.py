import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def get_market_data():
    df = yf.download(config.TICKER_SYMBOL, start=config.INITIAL_DATA_START_DATE)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicators
    df['MA20'] = df['Close'].rolling(window=config.MA_SHORT).mean()
    df['MA50'] = df['Close'].rolling(window=config.MA_LONG).mean()
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
    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
                df['High'].rolling(14).max() - df['Low'].rolling(14).min())

    try:
        news = yf.Search(config.ASSET_NAME, news_count=8).news
    except:
        news = []

    return df, news


def calculate_top_metrics(price, df_full):
    w_c = ((price - float(df_full['Close'].iloc[-5])) / float(df_full['Close'].iloc[-5])) * 100
    m_c = ((price - float(df_full['Close'].iloc[-21])) / float(df_full['Close'].iloc[-21])) * 100
    y_s = df_full[df_full.index >= "2025-01-01"]['Close'].iloc[0]
    y_c = ((price - y_s) / y_s) * 100
    vol = np.log(df_full['Close'] / df_full['Close'].shift(1)).std() * np.sqrt(252) * 100
    return w_c, m_c, y_c, vol