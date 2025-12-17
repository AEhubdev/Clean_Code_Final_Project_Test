import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def fetch_market_data():
    # Force auto_adjust=False to get the RAW $4300+ price
    # Set start to Dec 2024 as requested
    df = yf.download(config.TICKER_SYMBOL, start="2024-12-01", auto_adjust=False)

    # --- 2025 CRITICAL FIX: FLATTEN MULTI-INDEX HEADERS ---
    # Yahoo now returns 2 layers of headers (e.g., ['Close', 'GC=F']).
    # This line collapses it so our code sees just 'Close'.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure all columns are standard capitalization
    df.columns = [str(c).capitalize() for c in df.columns]
    df = df.ffill().dropna()

    # --- INDICATORS ---
    # These will work now because the columns are flattened
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

    return df.dropna()


def get_live_metrics(df):
    latest = df.iloc[-1]
    price = float(latest['Close'])
    # Calculate % change from start of the dataframe (Dec 2024)
    total_change = ((price - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    vol = df['Close'].pct_change().std() * np.sqrt(252) * 100
    return price, total_change, vol