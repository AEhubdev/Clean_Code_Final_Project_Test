def evaluate_status(latest):
    if latest['RSI'] < 30: return "STRONG BUY", "#00FF41"
    if latest['RSI'] > 70: return "STRONG SELL", "#FF3131"
    if latest['MACD_Hist'] > 0: return "BULLISH", "#00E5FF"
    return "NEUTRAL", "#808495"