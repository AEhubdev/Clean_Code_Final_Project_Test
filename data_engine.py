import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import config
from datetime import datetime


@st.cache_data(ttl=600)
def get_gold_terminal_data(timeframe_name=None):  # Set default to None
    """
    Orchestrates data retrieval.
    Now uses DEFAULT_INTERVAL from config if no name is provided.
    """
    # If no timeframe is passed (like in the sidebar/metrics call), use the config default
    if timeframe_name is None:
        timeframe_name = config.DEFAULT_INTERVAL_LABEL

    interval_code = config.TIMEFRAME_OPTIONS.get(timeframe_name, "1d")
    historical_df = fetch_market_data(interval_code)

    # ... rest of your function remains the same ...

    # Now this check will succeed because historical_df is guaranteed to be a DataFrame
    if historical_df.empty:
        return pd.DataFrame(), 0.0, [], 0.0

    processed_df = apply_technical_indicators(historical_df)
    current_price = float(processed_df['Close'].iloc[-1])

    ytd_start_price = fetch_ytd_start_price(current_price)
    market_news = fetch_market_news()

    return processed_df, current_price, market_news, ytd_start_price


def fetch_market_data(interval_code):
    """
    Downloads raw ticker data with appropriate history depth.
    Ensures a DataFrame is always returned to prevent AttributeErrors.
    """
    if interval_code in ["1m", "2m", "5m"]:
        period = "7d"
    elif interval_code in ["15m", "30m", "60m", "1h"]:
        period = "60d"
    else:
        period = "max"

    try:
        df = yf.download(config.TICKER, period=period, interval=interval_code, auto_adjust=False, progress=False)

        if df is None or df.empty:
            return pd.DataFrame()

        # Handle yfinance MultiIndex columns (Rule S2.40)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.ffill().dropna()
    except Exception:
        return pd.DataFrame()


def apply_technical_indicators(df):
    """
    Calculates statistical indicators.
    Follows Rule C1.3: Uses full names instead of abbreviations.
    """
    # Create a copy to avoid SettingWithCopy warnings
    df = df.copy()

    # Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # Bollinger Bands
    standard_deviation = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (standard_deviation * 2)
    df['BB_Lower'] = df['MA20'] - (standard_deviation * 2)

    # RSI (Relative Strength Index)
    #
    price_delta = df['Close'].diff()
    positive_gain = (price_delta.where(price_delta > 0, 0)).rolling(window=14).mean()
    negative_loss = (-price_delta.where(price_delta < 0, 0)).rolling(window=14).mean()
    relative_strength = positive_gain / (negative_loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + relative_strength))

    # MACD (Moving Average Convergence Divergence)
    #
    ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Stochastic Oscillator
    rolling_low = df['Low'].rolling(window=config.STOCH_K_PERIOD).min()
    rolling_high = df['High'].rolling(window=config.STOCH_K_PERIOD).max()
    df['Stoch_K'] = 100 * ((df['Close'] - rolling_low) / (rolling_high - rolling_low + 1e-10))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=config.STOCH_D_PERIOD).mean()

    # Buy/Sell Signals based on Config Thresholds
    is_oversold = df['RSI'] < config.RSI_OVERSOLD
    is_overbought = df['RSI'] > config.RSI_OVERBOUGHT
    macd_is_bullish = df['MACD_Hist'] > 0
    macd_is_bearish = df['MACD_Hist'] < 0

    df['Buy_Signal'] = is_oversold & macd_is_bullish
    df['Sell_Signal'] = is_overbought & macd_is_bearish

    return df


def fetch_ytd_start_price(fallback_price):
    """Retrieves the price from the first day of the current year."""
    year_start = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
    try:
        ytd_data = yf.download(config.TICKER, start=year_start, progress=False)
        if isinstance(ytd_data.columns, pd.MultiIndex):
            ytd_data.columns = ytd_data.columns.get_level_values(0)

        return float(ytd_data['Close'].iloc[0]) if not ytd_data.empty else fallback_price
    except Exception:
        return fallback_price


def fetch_market_news():
    """Fetches news titles and links."""
    try:
        search = yf.Search("Gold Price", news_count=8)
        return search.news
    except Exception:
        return []


def calculate_market_metrics(current_price, df_full, ytd_start_price):
    """
    Calculates percentage changes and volatility.
    Rule C2.19: Single return point via dictionary.
    """
    performance = {"weekly": 0.0, "monthly": 0.0, "ytd": 0.0, "volatility": 0.0}

    try:
        # Standard financial calculations for performance metrics
        performance["weekly"] = ((current_price - df_full['Close'].iloc[-5]) / df_full['Close'].iloc[-5]) * 100
        performance["monthly"] = ((current_price - df_full['Close'].iloc[-21]) / df_full['Close'].iloc[-21]) * 100
        performance["ytd"] = ((current_price - ytd_start_price) / ytd_start_price) * 100

        daily_returns = df_full['Close'].pct_change()
        # Annualized Volatility formula: std_dev * sqrt(trading_days)
        performance["volatility"] = daily_returns.std() * np.sqrt(252) * 100
    except (IndexError, KeyError, ZeroDivisionError):
        pass

    return performance