# config.py
TICKER_SYMBOL = "GC=F"
ASSET_NAME = "Gold"
DATA_START_DATE = "2025-01-01" # More recent start

# Technical Settings
MA_SHORT = 20
MA_LONG = 50
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Simulation Pace
REFRESH_RATE = 120.0
INITIAL_STEP = 50 # Start at least 50 days in to see MA50