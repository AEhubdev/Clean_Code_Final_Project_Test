import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime
from sklearn.linear_model import LinearRegression


@st.cache_data(ttl=60)
def get_gold_market_data(timeframe_name="1 Day"):
    interval_code = config.TIMEFRAME_OPTIONS.get(timeframe_name, "1d")
    data_period = _determine_fetch_period(interval_code)

    gold_data = yf.download(config.TICKER, period=data_period, interval=interval_code, auto_adjust=False)

    if gold_data.empty:
        return pd.DataFrame(), 0.0, [], 0.0

    # Handle MultiIndex and cleaning
    if isinstance(gold_data.columns, pd.MultiIndex):
        gold_data.columns = gold_data.columns.get_level_values(0)

    gold_data = gold_data.ffill().dropna()
    gold_data = _add_technical_indicators(gold_data)
    gold_data = _generate_trading_signals(gold_data)

    latest_price = float(gold_data['Close'].iloc[-1])
    year_to_date_start = _fetch_ytd_start_price(gold_data)
    market_news = _fetch_market_news()

    return gold_data, latest_price, market_news, year_to_date_start


def _determine_fetch_period(interval_code):
    if interval_code in ["15m", "1h"]: return "60d"
    if interval_code == "1wk": return "10y"
    return "max"


def _add_technical_indicators(dataframe):
    dataframe['MA20'] = dataframe['Close'].rolling(window=config.BB_PERIOD).mean()
    dataframe['MA50'] = dataframe['Close'].rolling(window=50).mean()
    standard_deviation = dataframe['Close'].rolling(window=config.BB_PERIOD).std()
    dataframe['BB_U'] = dataframe['MA20'] + (standard_deviation * config.BB_STD_DEV)
    dataframe['BB_L'] = dataframe['MA20'] - (standard_deviation * config.BB_STD_DEV)

    price_delta = dataframe['Close'].diff()
    average_gain = (price_delta.where(price_delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    average_loss = (-price_delta.where(price_delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    dataframe['RSI'] = 100 - (100 / (1 + (average_gain / (average_loss + 1e-10))))

    ema_fast = dataframe['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = dataframe['Close'].ewm(span=26, adjust=False).mean()
    dataframe['MACD'] = ema_fast - ema_slow
    dataframe['MACD_Signal'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()
    dataframe['MACD_Hist'] = dataframe['MACD'] - dataframe['MACD_Signal']

    low_min = dataframe['Low'].rolling(14).min()
    high_max = dataframe['High'].rolling(14).max()
    dataframe['Stoch_K'] = 100 * ((dataframe['Close'] - low_min) / (high_max - low_min + 1e-10))
    dataframe['Stoch_D'] = dataframe['Stoch_K'].rolling(window=3).mean()
    return dataframe


def generate_ai_prediction(dataframe, forecast_periods=30):
    """Predicts future prices with Damping and Seamless Stitching to prevent 'weird' behavior."""
    # 1. Scope and Clean Data
    df_window = dataframe.tail(150).copy()
    df_clean = df_window.dropna(subset=['RSI', 'MACD_Hist', 'BB_U', 'BB_L', 'Close']).copy()

    if df_clean.empty:
        return pd.DataFrame()

    features = ['RSI', 'MACD_Hist', 'BB_U', 'BB_L']
    X = df_clean[features].values
    y = df_clean['Close'].values

    # 2. Train Model
    model = LinearRegression()
    model.fit(X, y)

    # 3. Generate Raw Predictions
    recent_features = df_clean[features].tail(forecast_periods).values
    if len(recent_features) < forecast_periods:
        recent_features = np.tile(df_clean[features].iloc[-1].values, (forecast_periods, 1))

    raw_preds = model.predict(recent_features)

    # 4. FIX WEIRD JUMPS (Seamless Stitching)
    last_live_price = float(df_clean['Close'].iloc[-1])
    price_offset = last_live_price - raw_preds[0]
    aligned_preds = raw_preds + price_offset

    # 5. FIX DRAMATIC MOVES (Damping Factor)
    # This blends the AI prediction with the current 10-period momentum
    damped_preds = []
    # Calculate the current slope (Price change per bar)
    current_trend_slope = (df_clean['Close'].iloc[-1] - df_clean['Close'].iloc[-10]) / 10

    for i, ai_val in enumerate(aligned_preds):
        # simple_proj follows the current direction of the price
        simple_proj = last_live_price + (current_trend_slope * i)

        # 70% Weight on AI Logic, 30% Weight on Current Momentum
        # This prevents the 'crashing then recovering' U-shape
        final_val = (ai_val * 0.7) + (simple_proj * 0.3)
        damped_preds.append(final_val)

    # 6. DYNAMIC TIME DELTA (Skips timeframe visual bugs)
    last_date = df_clean.index[-1]
    if len(df_clean) > 1:
        time_delta = df_clean.index[-1] - df_clean.index[-2]
    else:
        time_delta = pd.Timedelta(days=1)

    future_dates = [last_date + (i * time_delta) for i in range(1, forecast_periods + 1)]

    # 7. Final DataFrame and Bridge
    pred_df = pd.DataFrame({'Predicted': damped_preds}, index=future_dates)
    bridge = pd.DataFrame({'Predicted': [last_live_price]}, index=[last_date])

    return pd.concat([bridge, pred_df])

def _generate_trading_signals(dataframe):
    buy_cond = (dataframe['RSI'] < config.RSI_BUY_THRESHOLD) & (dataframe['MACD_Hist'] > 0)
    sell_cond = (dataframe['RSI'] > config.RSI_SELL_THRESHOLD) & (dataframe['MACD_Hist'] < 0)
    dataframe['Buy_Signal'] = (buy_cond & ~buy_cond.shift(1).fillna(False))
    dataframe['Sell_Signal'] = (sell_cond & ~sell_cond.shift(1).fillna(False))
    return dataframe


def _fetch_ytd_start_price(dataframe):
    try:
        ytd_data = yf.download(config.TICKER, start=f"{datetime.now().year}-01-01", progress=False)
        if isinstance(ytd_data.columns, pd.MultiIndex): ytd_data.columns = ytd_data.columns.get_level_values(0)
        return float(ytd_data['Close'].iloc[0])
    except:
        return float(dataframe['Close'].iloc[0])


def _fetch_market_news():
    try:
        return yf.Search("Gold Price", news_count=5).news
    except:
        return []


def calculate_performance_metrics(current_price, dataframe, ytd_start):
    try:
        weekly_ret = ((current_price - dataframe['Close'].iloc[-5]) / dataframe['Close'].iloc[-5]) * 100
        monthly_ret = ((current_price - dataframe['Close'].iloc[-21]) / dataframe['Close'].iloc[-21]) * 100
        ytd_ret = ((current_price - ytd_start) / ytd_start) * 100
        vol = dataframe['Close'].pct_change().tail(30).std() * np.sqrt(252) * 100
        return weekly_ret, monthly_ret, ytd_ret, vol
    except:
        return 0.0, 0.0, 0.0, 0.0