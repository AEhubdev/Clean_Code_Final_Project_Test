import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

# 1. Page Configuration
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_terminal_theme()

# 2. State Management for Simulation
if 'current_step' not in st.session_state:
    st.session_state.current_step = config.INITIAL_START_STEP
    st.session_state.trades = []

# 3. Data Processing
with st.spinner('Loading Live Feed...'):
    data = data_engine.apply_indicators(data_engine.fetch_historical_data())

if st.session_state.current_step >= len(data):
    st.success("Simulation Cycle Complete.")
    st.stop()

# Slicing the 'Live' view
sim_df = data.iloc[:st.session_state.current_step]
latest = sim_df.iloc[-1]

# 4. Algo Execution
current_action = trading_logic.get_signal(latest)
if current_action in ["BUY", "SELL"]:
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != latest.name:
        st.session_state.trades.append({"Time": latest.name, "Action": current_action, "Price": latest['Close']})

# 5. UI Layout
st.title(f"🏆 {config.ASSET_NAME} Algorithmic Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Price", f"${latest['Close']:,.2f}")
c2.metric("RSI (14)", f"{latest['RSI']:.2f}")
c3.metric("Step", st.session_state.current_step)
c4.metric("Total Trades", len(st.session_state.trades))

chart_col, news_col = st.columns([0.75, 0.25])

with chart_col:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_df.index, y=sim_df['Close'], name="Price", line=dict(color='white')))
    fig.add_trace(go.Scatter(x=sim_df.index, y=sim_df['MA20'], name="MA 20", line=dict(color='#FFD700', width=1)))

    # Plotting Trade Markers
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        for act, color, sym in [("BUY", "#00FF41", "triangle-up"), ("SELL", "#FF3131", "triangle-down")]:
            sub = tdf[tdf['Action'] == act]
            fig.add_trace(
                go.Scatter(x=sub['Time'], y=sub['Price'], mode='markers', marker=dict(symbol=sym, size=12, color=color),
                           name=act))

    fig.update_layout(template="plotly_dark", height=500, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with news_col:
    st.markdown("### Algorithm Status")
    color_class = f"status-{current_action.lower()}"
    st.markdown(f"<div class='signal-card'>Signal: <span class='{color_class}'>{current_action}</span></div>",
                unsafe_allow_html=True)

    st.markdown("### Market News")
    for article in data_engine.get_market_news():
        styles.render_news_item(article)

# 6. Simulation Loop
time.sleep(config.REFRESH_RATE_SECONDS)
st.session_state.current_step += 1
st.rerun()