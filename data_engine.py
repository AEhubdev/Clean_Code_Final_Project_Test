import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config


@st.cache_data(ttl=60)
def get_gold_data():
    df = yf.download(config.TICKER, start=config.START_DATE, auto_adjust=False)
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

    # --- SIGNAL LOGIC FOR CHART ---
    df['Buy_Signal'] = (df['RSI'] < 35)
    df['Sell_Signal'] = (df['RSI'] > 65)

    try:
        search = yf.Search("Gold Market", news_count=8)
        news_data = search.news
    except:
        news_data = []

    return df[df.index >= config.CHART_START], float(df['Close'].iloc[-1]), df, news_data


def calculate_metrics(price, df_full):
    w_c = ((price - float(df_full['Close'].iloc[-5])) / float(df_full['Close'].iloc[-5])) * 100
    m_c = ((price - float(df_full['Close'].iloc[-21])) / float(df_full['Close'].iloc[-21])) * 100
    y_df = df_full[df_full.index >= "2025-01-01"]
    y_s = y_df['Close'].iloc[0] if not y_df.empty else price
    y_c = ((price - y_s) / y_s) * 100
    vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100
    return w_c, m_c, y_c, vol