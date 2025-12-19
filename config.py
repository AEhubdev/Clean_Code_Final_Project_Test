# ================================
# GOLD TRADING SYSTEM CONFIGURATION
# ================================

# --- ASSET & TIMEFRAME ---
TICKER = "GC=F"                    # Gold Futures
DEFAULT_INTERVAL = "1d"           # Primary analysis timeframe

# --- RSI SETTINGS ---
RSI_PERIOD = 14                    # Standard benchmark period
RSI_OVERBOUGHT = 70                # Overbought threshold
RSI_OVERSOLD = 30                  # Oversold threshold
RSI_BUY_THRESHOLD = 55             # Bullish momentum confirmation
RSI_SELL_THRESHOLD = 45            # Bearish momentum confirmation

# --- BOLLINGER BANDS SETTINGS ---
BB_PERIOD = 20                     # Moving average period
BB_STD_DEV = 2                     # Standard deviation multiplier

# --- VISUALIZATION ---
CHART_HEIGHT_MAIN = 500            # Main chart height
CHART_HEIGHT_INDICATOR = 150       # Indicator panel height

# --- TIMEFRAME OPTIONS ---
TIMEFRAME_OPTIONS = {
    "15 Minutes": "15m",           # Short-term analysis
    "1 Hour": "1h",                # Intraday trends
    "1 Day": "1d",                 # Primary analysis
    "1 Week": "1wk",               # Longer-term structure
    "1 Month": "1mo",              # Macro trends
}