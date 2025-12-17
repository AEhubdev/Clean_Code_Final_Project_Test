import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)  # Updates every 60 seconds
def fetch_market_data():
    # We download everything from your start date until today
    df = yf.download(config.TICKER_SYMBOL, start=config.DATA_START_DATE, interval="1d")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # --- Calculations remain the same for consistency ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
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