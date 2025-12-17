import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


@st.cache_data(ttl=600)
def get_gold_terminal_data(timeframe_name="1 Day"):
    # Safe access to config with a hardcoded fallback
    interval_code = config.TIMEFRAME_OPTIONS.get(timeframe_name, "1d")
    historical_df = fetch_market_data(interval_code)

    if historical_df.empty:
        return pd.DataFrame(), 0.0, [], 0.0

    processed_df = apply_technical_indicators(historical_df)

    # Safety check for the final row
    if processed_df.empty:
        return pd.DataFrame(), 0.0, [], 0.0

    current_price = float(processed_df['Close'].iloc[-1])
    ytd_start_price = fetch_ytd_start_price(current_price)
    market_news = fetch_market_news()

    return processed_df, current_price, market_news, ytd_start_price


def fetch_market_data(interval_code):
    """Downloads data and strictly flattens MultiIndex headers."""
    if interval_code in ["1m", "2m", "5m"]:
        period = "7d"
    elif interval_code in ["15m", "30m", "60m", "1h"]:
        period = "60d"
    else:
        period = "max"

    try:
        df = yf.download(
            config.TICKER,
            period=period,
            interval=interval_code,
            auto_adjust=False,
            progress=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # CRITICAL FIX: Flatten MultiIndex (Ticker Level)
        # Recent yfinance returns: [Price, Ticker] columns.
        # We need to strip the Ticker level so df['Close'] is a Series.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Standardize column names to remove any 'Price' index name
        df.columns = [str(col).strip() for col in df.columns]

        return df.ffill().dropna()

    except Exception as e:
        st.error(f"yfinance Connection Error: {e}")
        return pd.DataFrame()


def apply_technical_indicators(df):
    """Calculates indicators with safety checks for data length."""
    df = df.copy()

    # Requirement: Rolling math needs at least N rows
    min_rows = max(50, config.STOCH_K_PERIOD)
    if len(df) < min_rows:
        return df

    # Standard Indicators
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # Bollinger Bands
    std_dev = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (std_dev * 2)
    df['BB_Lower'] = df['MA20'] - (std_dev * 2)

    # RSI Logic
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD Logic
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Stochastic Oscillator
    low_min = df['Low'].rolling(window=config.STOCH_K_PERIOD).min()
    high_max = df['High'].rolling(window=config.STOCH_K_PERIOD).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min + 1e-10))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=config.STOCH_D_PERIOD).mean()

    # Signals
    df['Buy_Signal'] = (df['RSI'] < config.RSI_OVERSOLD) & (df['MACD_Hist'] > 0)
    df['Sell_Signal'] = (df['RSI'] > config.RSI_OVERBOUGHT) & (df['MACD_Hist'] < 0)

    return df


def fetch_ytd_start_price(fallback):
    year_start = f"{datetime.now().year}-01-01"
    try:
        data = yf.download(config.TICKER, start=year_start, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return float(data['Close'].iloc[0]) if not data.empty else fallback
    except:
        return fallback


def fetch_market_news():
    try:
        return yf.Search("Gold Price", news_count=8).news
    except:
        return []