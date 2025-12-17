import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=900)  # Cache the heavy indicators for 15 mins
def get_base_data(interval="1d"):
    period = "60d" if interval in ["15m", "1h"] else "max"
    df = yf.download(config.TICKER, period=period, interval=interval, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()
    # ... (Your existing MA, RSI, MACD calculations here) ...
    return df


def get_live_price():
    # Fast fetch for just the latest candle
    ticker = yf.Ticker(config.TICKER)
    return ticker.fast_info['last_price']