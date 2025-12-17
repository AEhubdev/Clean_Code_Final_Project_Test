import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def get_gold_data(interval="1d"):
    # Determine lookback period based on interval
    # 15m/1h need shorter periods due to API limits
    period = "60d" if interval in ["15m", "1h"] else "max"

    df = yf.download(config.TICKER, period=period, interval=interval, auto_adjust=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # Technicals (Dynamic based on data frequency)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_U'] = df['MA20'] + (std * 2)
    df['BB_L'] = df['MA20'] - (std * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Smarter Logic: Trigger when momentum shifts at extremes
    df['Buy_Signal'] = (df['RSI'] < 35) & (df['MACD_Hist'] > df['MACD_Hist'].shift(1))
    df['Sell_Signal'] = (df['RSI'] > 65) & (df['MACD_Hist'] < df['MACD_Hist'].shift(1))

    return df, float(df['Close'].iloc[-1])