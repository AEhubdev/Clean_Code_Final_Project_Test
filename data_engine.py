import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st


@st.cache_data(ttl=60)
def fetch_market_data():
    # 1. Download Raw Gold Futures ($4300+ price)
    df = yf.download("GC=F", start="2024-12-01", auto_adjust=False)

    # 2. Fix 2025 Header Bug (Flatten MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # 3. Moving Averages & Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std * 2)
    df['BB_Lower'] = df['MA20'] - (std * 2)

    # 4. MACD & RSI
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    return df.dropna()


def get_signal_logic(row):
    if row['RSI'] < 32: return "STRONG BUY", "#00FF41"
    if row['RSI'] > 68: return "STRONG SELL", "#FF3131"
    return "NEUTRAL", "#888888"