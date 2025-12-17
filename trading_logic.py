import config

def get_signals(df):
    # Buy when RSI < 30 and price is near Lower Bollinger Band
    df['Buy_Signal'] = (df['RSI'] < config.RSI_OVERSOLD) & (df['Close'] <= df['BB_L'] * 1.01)
    # Sell when RSI > 70 and price is near Upper Bollinger Band
    df['Sell_Signal'] = (df['RSI'] > config.RSI_OVERBOUGHT) & (df['Close'] >= df['BB_U'] * 0.99)
    return df

def evaluate_status(latest):
    if latest['RSI'] < config.RSI_OVERSOLD: return "STRONG BUY", "#00FF41"
    if latest['RSI'] > config.RSI_OVERBOUGHT: return "STRONG SELL", "#FF3131"
    return "NEUTRAL", "#808495"