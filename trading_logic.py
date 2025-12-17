import config


def evaluate_market_status(latest_bar):
    """
    Determines the trading recommendation based on RSI thresholds.
    Follows Rule C2.19: Single return point via 'decision' and 'status_color'.
    """
    rsi_value = latest_bar.get('RSI', 50)

    # Initialize with default 'Neutral' values (Rule 19)
    decision = "NEUTRAL"
    status_color = "#808495"

    # Logic based on config thresholds (Rule 21: No magic numbers)
    if rsi_value < config.RSI_OVERSOLD:
        decision = "STRONG BUY"
        status_color = "#00FF41"

    elif rsi_value > config.RSI_OVERBOUGHT:
        decision = "STRONG SELL"
        status_color = "#FF3131"

    return decision, status_color