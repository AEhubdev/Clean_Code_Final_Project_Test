import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=900)
def get_gold_data(interval="1d"):
    period = "60d" if interval in ["15m", "1h"] else "max"
    df = yf.download(config.TICKER, period=period, interval=interval, auto_adjust=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # Calculations (Must happen BEFORE the return)
    df['MA20'] = df['Close'].rolling(window=20).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # CRITICAL: Create the signal columns here
    df['Buy_Signal'] = (df['RSI'] < 35) & (df['MACD_Hist'] > df['MACD_Hist'].shift(1))
    df['Sell_Signal'] = (df['RSI'] > 65) & (df['MACD_Hist'] < df['MACD_Hist'].shift(1))

    return df, float(df['Close'].iloc[-1])