import config


def get_signal(row):
    """
    Sophisticated logic: BUY if RSI is oversold and MACD is bullish.
    SELL if RSI is overbought or price drops below MA20.
    """
    price = row['Close']
    rsi = row['RSI']
    macd = row['MACD']
    signal = row['MACD_SIGNAL']
    ma20 = row['MA20']

    if rsi < config.RSI_OVERSOLD and macd > signal:
        return "BUY"
    elif rsi > config.RSI_OVERBOUGHT or (price < ma20 and macd < signal):
        return "SELL"
    return "HOLD"