def evaluate_status(latest_price_data: dict) -> tuple[str, str]:
    """Evaluate trading status based on RSI value.

    Args:
        latest_price_data: Dictionary containing latest price indicators
                          (must contain 'RSI' key)

    Returns:
        Tuple of (status_label, status_color) where:
        - status_label: String describing the trading status
        - status_color: Hex color code for display
    """
    rsi_value = latest_price_data.get('RSI')

    if rsi_value is None:
        return "DATA UNAVAILABLE", "#808495"

    if rsi_value < 30:
        return "STRONG BUY", "#00FF41"

    if rsi_value > 70:
        return "STRONG SELL", "#FF3131"

    return "NEUTRAL", "#808495"