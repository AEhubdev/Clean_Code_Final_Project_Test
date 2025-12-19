from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
import streamlit as st

import config


@st.cache_data(ttl=60)
def get_gold_market_data(timeframe_name: str = "1 Day") -> tuple:
    """Fetch and process gold market data for the given timeframe."""
    interval_code = config.TIMEFRAME_OPTIONS.get(timeframe_name, "1d")
    data_period = _determine_fetch_period(interval_code)

    gold_data = yf.download(
        tickers=config.TICKER,
        period=data_period,
        interval=interval_code,
        auto_adjust=False
    )

    if gold_data.empty:
        return pd.DataFrame(), 0.0, [], 0.0

    gold_data = _clean_dataframe(gold_data)
    gold_data = _add_technical_indicators(gold_data)
    gold_data = _generate_trading_signals(gold_data)

    latest_price = float(gold_data['Close'].iloc[-1])
    ytd_start_price = _fetch_ytd_start_price(gold_data)
    market_news = _fetch_market_news()

    return gold_data, latest_price, market_news, ytd_start_price


def _determine_fetch_period(interval_code: str) -> str:
    """Determine the data fetch period based on interval."""
    if interval_code in ["15m", "1h"]:
        return "60d"
    if interval_code == "1wk":
        return "10y"
    return "max"


def _clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare the raw dataframe."""
    if isinstance(dataframe.columns, pd.MultiIndex):
        dataframe.columns = dataframe.columns.get_level_values(0)
    return dataframe.ffill().dropna()


def _add_technical_indicators(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators and add them to the dataframe."""
    # Moving averages
    dataframe['MA20'] = dataframe['Close'].rolling(window=config.BB_PERIOD).mean()
    dataframe['MA50'] = dataframe['Close'].rolling(window=50).mean()

    # Bollinger Bands
    standard_deviation = dataframe['Close'].rolling(window=config.BB_PERIOD).std()
    dataframe['BB_U'] = dataframe['MA20'] + (standard_deviation * config.BB_STD_DEV)
    dataframe['BB_L'] = dataframe['MA20'] - (standard_deviation * config.BB_STD_DEV)

    # RSI
    dataframe['RSI'] = _calculate_rsi(dataframe['Close'])

    # MACD
    dataframe['MACD'], dataframe['MACD_Signal'], dataframe['MACD_Hist'] = _calculate_macd(dataframe['Close'])

    # Stochastic
    dataframe['Stoch_K'], dataframe['Stoch_D'] = _calculate_stochastic(
        dataframe['High'], dataframe['Low'], dataframe['Close']
    )

    return dataframe


def _calculate_rsi(price_series: pd.Series) -> pd.Series:
    """Calculate Relative Strength Index."""
    price_delta = price_series.diff()

    average_gain = price_delta.where(price_delta > 0, 0).rolling(window=config.RSI_PERIOD).mean()
    average_loss = (-price_delta.where(price_delta <, 0)).rolling(window=config.RSI_PERIOD).mean()

    relative_strength = average_gain / (average_loss + 1e-10)
    rsi = 100 - (100 / (1 + relative_strength))

    return rsi


def _calculate_macd(price_series: pd.Series) -> tuple:
    """Calculate MACD, Signal line, and Histogram."""
    ema_fast = price_series.ewm(span=12, adjust=False).mean()
    ema_slow = price_series.ewm(span=26, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    return macd, signal, histogram


def _calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series) -> tuple:
    """Calculate Stochastic Oscillator %K and %D."""
    low_min = low.rolling(window=14).min()
    high_max = high.rolling(window=14).max()

    stochastic_k = 100 * ((close - low_min) / (high_max - low_min + 1e-10))
    stochastic_d = stochastic_k.rolling(window=3).mean()

    return stochastic_k, stochastic_d


def generate_ai_prediction(dataframe: pd.DataFrame, forecast_periods: int = 30) -> pd.DataFrame:
    """Generate AI price predictions with damping to prevent extreme movements."""

    if dataframe.empty:
        return pd.DataFrame()

    # Prepare features
    features_data = _prepare_prediction_features(dataframe)
    if features_data.empty:
        return pd.DataFrame()

    # Train model and generate predictions
    predictions = _train_and_predict(features_data, forecast_periods)

    # Apply corrections to predictions
    corrected_predictions = _correct_predictions(predictions, features_data)

    # Create prediction dataframe with dates
    return _create_prediction_dataframe(corrected_predictions, features_data)


def _prepare_prediction_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Prepare cleaned feature data for prediction."""
    required_columns = ['RSI', 'MACD_Hist', 'BB_U', 'BB_L', 'Close']

    window_data = dataframe.tail(150).copy()
    clean_data = window_data.dropna(subset=required_columns).copy()

    return clean_data


def _train_and_predict(features_data: pd.DataFrame, forecast_periods: int) -> np.ndarray:
    """Train linear regression model and generate raw predictions."""
    feature_columns = ['RSI', 'MACD_Hist', 'BB_U', 'BB_L']

    X = features_data[feature_columns].values
    y = features_data['Close'].values

    model = LinearRegression()
    model.fit(X, y)

    # Use recent features for prediction
    recent_features = features_data[feature_columns].tail(forecast_periods).values
    if len(recent_features) < forecast_periods:
        recent_features = np.tile(features_data[feature_columns].iloc[-1].values, (forecast_periods, 1))

    return model.predict(recent_features)


def _correct_predictions(raw_predictions: np.ndarray, features_data: pd.DataFrame) -> np.ndarray:
    """Apply seamless stitching and damping to raw predictions."""
    last_live_price = float(features_data['Close'].iloc[-1])

    # Seamless stitching: align first prediction with current price
    price_offset = last_live_price - raw_predictions[0]
    aligned_predictions = raw_predictions + price_offset

    # Damping: blend with current momentum
    current_trend_slope = _calculate_current_trend_slope(features_data['Close'])
    return _apply_damping(aligned_predictions, last_live_price, current_trend_slope)


def _calculate_current_trend_slope(price_series: pd.Series) -> float:
    """Calculate current price trend slope over last 10 periods."""
    if len(price_series) < 10:
        return 0.0
    return (price_series.iloc[-1] - price_series.iloc[-10]) / 10


def _apply_damping(predictions: np.ndarray, last_price: float, trend_slope: float) -> np.ndarray:
    """Apply damping factor to blend AI predictions with current momentum."""
    damped_predictions = []

    for i, ai_prediction in enumerate(predictions):
        simple_projection = last_price + (trend_slope * i)
        # 70% weight on AI, 30% weight on current momentum
        final_value = (ai_prediction * 0.7) + (simple_projection * 0.3)
        damped_predictions.append(final_value)

    return np.array(damped_predictions)


def _create_prediction_dataframe(predictions: np.ndarray, features_data: pd.DataFrame) -> pd.DataFrame:
    """Create final prediction dataframe with proper dates."""
    forecast_periods = len(predictions)
    last_date = features_data.index[-1]

    # Calculate time delta between periods
    if len(features_data) > 1:
        time_delta = features_data.index[-1] - features_data.index[-2]
    else:
        time_delta = pd.Timedelta(days=1)

    # Generate future dates
    future_dates = [last_date + (i * time_delta) for i in range(1, forecast_periods + 1)]

    # Create bridge point (current price)
    bridge_point = pd.DataFrame(
        {'Predicted': [float(features_data['Close'].iloc[-1])]},
        index=[last_date]
    )

    # Create predictions dataframe
    predictions_df = pd.DataFrame(
        {'Predicted': predictions},
        index=future_dates
    )

    return pd.concat([bridge_point, predictions_df])


def _generate_trading_signals(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Generate buy and sell signals based on RSI and MACD conditions."""
    buy_condition = (dataframe['RSI'] < config.RSI_BUY_THRESHOLD) & (dataframe['MACD_Hist'] > 0)
    sell_condition = (dataframe['RSI'] > config.RSI_SELL_THRESHOLD) & (dataframe['MACD_Hist'] < 0)

    dataframe['Buy_Signal'] = buy_condition & ~buy_condition.shift(1).fillna(False)
    dataframe['Sell_Signal'] = sell_condition & ~sell_condition.shift(1).fillna(False)

    return dataframe


def _fetch_ytd_start_price(dataframe: pd.DataFrame) -> float:
    """Fetch Year-to-Date starting price for gold."""
    try:
        current_year = datetime.now().year
        ytd_data = yf.download(
            tickers=config.TICKER,
            start=f"{current_year}-01-01",
            progress=False
        )

        if isinstance(ytd_data.columns, pd.MultiIndex):
            ytd_data.columns = ytd_data.columns.get_level_values(0)

        return float(ytd_data['Close'].iloc[0])
    except Exception:
        return float(dataframe['Close'].iloc[0])


def _fetch_market_news() -> list:
    """Fetch recent market news related to gold."""
    try:
        return yf.Search("Gold Price", news_count=5).news
    except Exception:
        return []


def calculate_performance_metrics(
        current_price: float,
        dataframe: pd.DataFrame,
        ytd_start: float
) -> tuple:
    """Calculate performance metrics: weekly, monthly, YTD returns, and volatility."""
    try:
        weekly_return = _calculate_return(current_price, dataframe, periods=5)
        monthly_return = _calculate_return(current_price, dataframe, periods=21)
        ytd_return = _calculate_ytd_return(current_price, ytd_start)
        volatility = _calculate_volatility(dataframe)

        return weekly_return, monthly_return, ytd_return, volatility
    except Exception:
        return 0.0, 0.0, 0.0, 0.0


def _calculate_return(current_price: float, dataframe: pd.DataFrame, periods: int) -> float:
    """Calculate return over specified number of periods."""
    if len(dataframe) <= periods:
        return 0.0
    return ((current_price - dataframe['Close'].iloc[-periods]) / dataframe['Close'].iloc[-periods]) * 100


def _calculate_ytd_return(current_price: float, ytd_start: float) -> float:
    """Calculate Year-to-Date return."""
    if ytd_start == 0:
        return 0.0
    return ((current_price - ytd_start) / ytd_start) * 100


def _calculate_volatility(dataframe: pd.DataFrame) -> float:
    """Calculate annualized volatility from daily returns."""
    if len(dataframe) < 2:
        return 0.0

    daily_returns = dataframe['Close'].pct_change().tail(30)
    if daily_returns.empty:
        return 0.0

    daily_volatility = daily_returns.std()
    annualized_volatility = daily_volatility * np.sqrt(252) * 100

    return annualized_volatility