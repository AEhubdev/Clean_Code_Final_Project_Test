def evaluate_signal(row):
    # RSI + MACD Strategy
    if row['RSI'] < 35 and row['MACD_Hist'] > 0:
        return "BUY", "#00FF41"
    elif row['RSI'] > 65 and row['MACD_Hist'] < 0:
        return "SELL", "#FF3131"
    else:
        return "NEUTRAL", "gray"