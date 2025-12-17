import config


def evaluate_signal(row):
    rsi = row['RSI']
    macd = row['MACD']
    signal_line = row['MACD_Signal']

    if rsi < config.RSI_OVERSOLD and macd > signal_line:
        return "STRONG BUY", "#00FF41"
    elif rsi > config.RSI_OVERBOUGHT:
        return "STRONG SELL", "#FF3131"
    return "NEUTRAL", "#808495"