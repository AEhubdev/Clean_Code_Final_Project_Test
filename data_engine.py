import yfinance as yf

import pandas as pd

import numpy as np

import streamlit as st

import config

from datetime import datetime



@st.cache_data(ttl=600)

def get_gold_data(interval_name="1 Day"):

    interval_code = config.TIMEFRAME_OPTIONS.get(interval_name, "1d")

    period = "60d" if interval_code in ["15m", "1h"] else "max"



    df = yf.download(config.TICKER, period=period, interval=interval_code, auto_adjust=False)

    if df.empty: return pd.DataFrame(), 0.0, [], 0.0

    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)



    df = df.ffill().dropna()



    # --- MOVING AVERAGES & BOLLINGER BANDS ---

    df['MA20'] = df['Close'].rolling(window=20).mean()

    df['MA50'] = df['Close'].rolling(window=50).mean()

    df['StdDev'] = df['Close'].rolling(window=20).std()

    df['BB_U'] = df['MA20'] + (df['StdDev'] * 2)

    df['BB_L'] = df['MA20'] - (df['StdDev'] * 2)



    # --- RSI & MACD ---

    delta = df['Close'].diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()

    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))



    ema12 = df['Close'].ewm(span=12, adjust=False).mean()

    ema26 = df['Close'].ewm(span=26, adjust=False).mean()

    df['MACD'] = ema12 - ema26

    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']



    # --- STOCHASTIC ---

    k_period, d_period = 14, 3

    df['Low_Min'] = df['Low'].rolling(window=k_period).min()

    df['High_Max'] = df['High'].rolling(window=k_period).max()

    df['Stoch_K'] = 100 * ((df['Close'] - df['Low_Min']) / (df['High_Max'] - df['Low_Min'] + 1e-10))

    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()



    # --- SIGNALS ---

    buy_cond = (df['RSI'] < 30) & (df['MACD_Hist'] > 0)

    sell_cond = (df['RSI'] > 70) & (df['MACD_Hist'] < 0)

    df['Buy_Signal'] = buy_cond & ~buy_cond.shift(1).fillna(False)

    df['Sell_Signal'] = sell_cond & ~sell_cond.shift(1).fillna(False)



    # --- YTD START PRICE ---

    y_start = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')

    ytd_data = yf.download(config.TICKER, start=y_start, progress=False)

    ytd_start_price = ytd_data['Close'].iloc[0] if not ytd_data.empty else df['Close'].iloc[0]



    news_list = []

    try:

        search = yf.Search("Gold Price", news_count=8)

        news_list = search.news

    except: pass



    return df, float(df['Close'].iloc[-1]), news_list, float(ytd_start_price)



def calculate_metrics(price, df_full, ytd_start):

    try:

        w_c = ((price - df_full['Close'].iloc[-5]) / df_full['Close'].iloc[-5]) * 100

        m_c = ((price - df_full['Close'].iloc[-21]) / df_full['Close'].iloc[-21]) * 100

        ytd_c = ((price - ytd_start) / ytd_start) * 100

        vol = df_full['Close'].pct_change().std() * np.sqrt(252) * 100

        return w_c, m_c, ytd_c, vol

    except: return 0.0, 0.0, 0.0, 0.0