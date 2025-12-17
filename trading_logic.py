import config


def generate_signal(row):
    rsi = row['RSI']
    macd = row['MACD']
    sig_line = row['MACD_Signal']

    if rsi < config.RSI_OVERSOLD and macd > sig_line:
        return "STRONG BUY", "#00FF41"
    elif rsi > config.RSI_OVERBOUGHT:
        return "STRONG SELL", "#FF3131"
    return "NEUTRAL", "#808495"