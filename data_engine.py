import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def get_gold_data():
    ticker = config.TICKER
    # Download more data than we need to ensure indicators have enough "buffer"
    df = yf.download(ticker, start="2024-09-01", auto_adjust=False)

    if df.empty:
        st.error("No data found for the ticker. Check connection.")
        return pd.DataFrame(), 0.0, pd.DataFrame(), []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.ffill().dropna()

    # Indicators
    df['MA20'] = df['Close'].rolling(window=config.MA_FAST).mean()
    df['MA50'] = df['Close'].rolling(window=config.MA_SLOW).mean()
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

    df['STOCH_K'] = (df['Close'] - df['Low'].rolling(14).min()) * 100 / (
                df['High'].rolling(14).max() - df['Low'].rolling(14).min() + 1e-10)

    # Signal Logic
    df['Buy_Signal'] = (df['RSI'] < 35) & (df['MACD_Hist'] > 0)
    df['Sell_Signal'] = (df['RSI'] > 65) & (df['MACD_Hist'] < 0)

    # HARDENED NEWS FETCH
    news_data = []
    try:
        search = yf.Search("Gold Market", news_count=5)
        if hasattr(search, 'news'):
            news_data = search.news
    except Exception:
        news_data = []  # Fallback to empty list if Yahoo fails

    # Return only from CHART_START onwards for display
    display_df = df[df.index >= config.CHART_START].copy()
    current_price = float(df['Close'].iloc[-1])

    return display_df, current_price, df, news_data


def calculate_metrics(price, df_full):
    try:
        # Check if we have enough data points for the calculations
        w_idx = -5 if len(df_full) >= 5 else 0
        m_idx = -21 if len(df_full) >= 21 else 0

        w_c = ((price - float(df_full['Close'].iloc[w_idx])) / float(df_full['Close'].iloc[w_idx])) * 100
        m_c = ((price - float(df_full['Close'].iloc[m_idx])) / float(df_full['Close'].iloc[m_idx])) * 100

        y_df = df_full[df_full.index >= "2025-01-01"]
        y_s = y_df['Close'].iloc[0] if not y_df.empty else price
        y_c = ((price - y_s) / y_s) * 100

        vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
        return w_c, m_c, y_c, vol
    except Exception:
        return 0.0, 0.0, 0.0, 0.0