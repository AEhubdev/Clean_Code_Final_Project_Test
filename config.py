# --- CORE ASSET SETTINGS ---
TICKER = "GC=F"              # Gold Futures (Standard)
DEFAULT_INTERVAL = "1d"      # Daily is the standard 'Anchor' timeframe

# --- RSI (Relative Strength Index) ---
# Standards: 14 periods is the universal benchmark.
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70          # Statistical extreme
RSI_OVERSOLD = 30           # Statistical extreme

# Professional Signal Logic:
# In gold, a cross above 50/60 confirms momentum.
# 40/60 are 'Regime' levels used by pro desk traders.
RSI_BUY_THRESHOLD = 55       # Confirming bullish momentum (Standard: 50-60)
RSI_SELL_THRESHOLD = 45      # Confirming bearish momentum (Standard: 40-50)

# --- BOLLINGER BANDS (BB) ---
# Standard: 20-period SMA with 2 Standard Deviations (95% of price action)
BB_PERIOD = 20
BB_STD_DEV = 2

# --- CHART STYLES ---
CHART_HEIGHT_MAIN = 500      # Slightly taller for better candle visibility
CHART_HEIGHT_INDICATOR = 150 # Compact for multi-indicator stacking

# --- TIMEFRAME OPTIONS ---
# Standard intervals used by institutional terminals (Bloomberg/Reuters)
TIMEFRAME_OPTIONS = {
    "15 Minutes": "15m",     # Scalping/Day Trade
    "1 Hour": "1h",          # Intraday Trend
    "1 Day": "1d",           # Macro Trend
    "1 Week": "1wk",         # Long-term Structure
    "1 Month": "1mo",        # Scalping/Day Trade
}