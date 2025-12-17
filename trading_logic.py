import config


def generate_trading_signal(latest_data_row):
    """
    Core algorithmic logic.
    Returns: 'BUY', 'SELL', or 'HOLD'
    """
    price = latest_data_row['Close']
    rsi = latest_data_row['RSI']
    macd = latest_data_row['MACD']
    macd_signal = latest_data_row['MACD_SIGNAL']
    ma20 = latest_data_row['MA20']

    # Multi-factor logic: Momentum + Mean Reversion
    is_oversold = rsi < config.RSI_OVERSOLD
    is_overbought = rsi > config.RSI_OVERBOUGHT
    macd_cross_up = macd > macd_signal
    price_above_ma = price > ma20

    if is_oversold and macd_cross_up:
        return "BUY"
    elif is_overbought or (not price_above_ma and macd < macd_signal):
        return "SELL"

    return "HOLD"