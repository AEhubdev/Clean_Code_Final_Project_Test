import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


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
    if interval_code in ["15m", "1h"]:
        return "60d"
    if interval_code == "1wk":
        return "10y"
    return "max"


def _add_technical_indicators(dataframe):
    # Bollinger Bands
    dataframe['MA20'] = dataframe['Close'].rolling(window=config.BB_PERIOD).mean()
    dataframe['MA50'] = dataframe['Close'].rolling(window=50).mean()
    standard_deviation = dataframe['Close'].rolling(window=config.BB_PERIOD).std()
    dataframe['BB_U'] = dataframe['MA20'] + (standard_deviation * config.BB_STD_DEV)
    dataframe['BB_L'] = dataframe['MA20'] - (standard_deviation * config.BB_STD_DEV)

    # RSI
    price_delta = dataframe['Close'].diff()
    average_gain = (price_delta.where(price_delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    average_loss = (-price_delta.where(price_delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    dataframe['RSI'] = 100 - (100 / (1 + (average_gain / (average_loss + 1e-10))))

    # MACD
    ema_fast = dataframe['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = dataframe['Close'].ewm(span=26, adjust=False).mean()
    dataframe['MACD'] = ema_fast - ema_slow
    dataframe['MACD_Signal'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()
    dataframe['MACD_Hist'] = dataframe['MACD'] - dataframe['MACD_Signal']

    # Stochastic
    low_min = dataframe['Low'].rolling(14).min()
    high_max = dataframe['High'].rolling(14).max()
    dataframe['Stoch_K'] = 100 * ((dataframe['Close'] - low_min) / (high_max - low_min + 1e-10))
    dataframe['Stoch_D'] = dataframe['Stoch_K'].rolling(window=3).mean()
    return dataframe


def generate_ai_prediction(dataframe, forecast_days=30):
    """Predicts future prices using RSI, MACD, and Bollinger Bands as training features."""
    # 1. Clean data for training
    df_clean = dataframe.dropna(subset=['RSI', 'MACD_Hist', 'BB_U', 'BB_L', 'Close']).copy()

    # 2. Define Features (X) and Target (y)
    # We use these indicators to explain the price behavior
    features = ['RSI', 'MACD_Hist', 'BB_U', 'BB_L']
    X = df_clean[features].values
    y = df_clean['Close'].values

    # 3. Fit Multi-Variable Model
    model = LinearRegression()
    model.fit(X, y)

    # 4. Extrapolate Future Inputs
    # For prediction, we use the most recent indicator states to project forward
    # This assumes the 'momentum' of the indicators continues into the projection
    recent_features = df_clean[features].tail(forecast_days).values
    if len(recent_features) < forecast_days:
        recent_features = np.tile(df_clean[features].iloc[-1].values, (forecast_days, 1))

    future_preds = model.predict(recent_features)

    # 5. Build Future Index
    last_date = df_clean.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)

    return pd.DataFrame({'Predicted': future_preds}, index=future_dates)

def _generate_trading_signals(dataframe):
    buy_condition = (dataframe['RSI'] < config.RSI_BUY_THRESHOLD) & (dataframe['MACD_Hist'] > 0)
    sell_condition = (dataframe['RSI'] > config.RSI_SELL_THRESHOLD) & (dataframe['MACD_Hist'] < 0)

    # Boolean triggers to markers
    dataframe['Buy_Signal'] = (buy_condition & ~buy_condition.shift(1).fillna(False))
    dataframe['Sell_Signal'] = (sell_condition & ~sell_condition.shift(1).fillna(False))
    return dataframe


def _fetch_ytd_start_price(dataframe):
    try:
        current_year = datetime.now().year
        ytd_data = yf.download(config.TICKER, start=f"{current_year}-01-01", progress=False)
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
        weekly_return = ((current_price - dataframe['Close'].iloc[-5]) / dataframe['Close'].iloc[-5]) * 100
        monthly_return = ((current_price - dataframe['Close'].iloc[-21]) / dataframe['Close'].iloc[-21]) * 100
        ytd_return = ((current_price - ytd_start) / ytd_start) * 100
        volatility = dataframe['Close'].pct_change().tail(30).std() * np.sqrt(252) * 100
        return weekly_return, monthly_return, ytd_return, volatility
    except:
        return 0.0, 0.0, 0.0, 0.0