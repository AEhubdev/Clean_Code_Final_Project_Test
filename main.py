import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime

import data_engine
import trading_logic
import styles
import config

# --- PAGE SETUP ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_terminal_theme()

# Initialize Session State for simulation
if 'current_step' not in st.session_state:
    st.session_state.current_step = 100  # Start with some history
    st.session_state.trade_history = []

# --- DATA PREPARATION ---
raw_history = data_engine.fetch_historical_data()
df_with_indicators = data_engine.apply_technical_indicators(raw_history)

# Simulation Slice
simulated_df = df_with_indicators.iloc[:st.session_state.current_step]
latest_row = simulated_df.iloc[-1]
current_price = latest_row['Close']

# --- HEADER ---
st.title(f"🏆 {config.ASSET_NAME} Algo-Trading Terminal")
col1, col2, col3 = st.columns(3)
col1.metric("Live Price", f"${current_price:,.2f}")
col2.metric("RSI (14)", f"{latest_row['RSI']:.2f}")
col3.metric("Step", f"{st.session_state.current_step}")

# --- ALGO DECISION ---
current_decision = trading_logic.generate_trading_signal(latest_row)
if current_decision in ["BUY", "SELL"]:
    trade_entry = {
        "Time": latest_row.name,
        "Action": current_decision,
        "Price": current_price
    }
    # Avoid duplicate logs for the same timestamp
    if not st.session_state.trade_history or st.session_state.trade_history[-1]["Time"] != latest_row.name:
        st.session_state.trade_history.append(trade_entry)

# --- VISUALIZATION ---
chart_col, side_col = st.columns([0.7, 0.3])

with chart_col:
    fig = go.Figure()
    # Price & Indicators
    fig.add_trace(go.Scatter(x=simulated_df.index, y=simulated_df['Close'], name="Price", line=dict(color='white')))
    fig.add_trace(
        go.Scatter(x=simulated_df.index, y=simulated_df['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1)))

    # Plot Trade Decisions (Requirement: Precise time of buy/sell)
    if st.session_state.trade_history:
        trades_df = pd.DataFrame(st.session_state.trade_history)
        buys = trades_df[trades_df['Action'] == "BUY"]
        sells = trades_df[trades_df['Action'] == "SELL"]

        fig.add_trace(go.Scatter(x=buys['Time'], y=buys['Price'], mode='markers',
                                 marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="BUY"))
        fig.add_trace(go.Scatter(x=sells['Time'], y=sells['Price'], mode='markers',
                                 marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="SELL"))

    fig.update_layout(template="plotly_dark", height=500, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with side_col:
    st.subheader("📡 Live Signal")
    status_class = "status-buy" if current_decision == "BUY" else "status-sell" if current_decision == "SELL" else ""
    st.markdown(f"<div class='signal-card'>Action: <span class='{status_class}'>{current_decision}</span></div>",
                unsafe_allow_html=True)

    st.subheader("📰 Market News")
    news = data_engine.fetch_market_news()
    for item in news:
        styles.render_news_item(item)

# --- DYNAMIC UPDATE LOOP ---
# Requirement: Simulation of live data feed
if st.session_state.current_step < len(df_with_indicators) - 1:
    st.session_state.current_step += 1
    time.sleep(config.REFRESH_RATE_SECONDS)
    st.rerun()