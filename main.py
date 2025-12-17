import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

# Session State Initialization
if 'step' not in st.session_state:
    st.session_state.step = config.INITIAL_STEP
    st.session_state.trades = []

# Data Acquisition
df_full, news_list = data_engine.fetch_market_data()

# Logic to wrap the simulation loop
if st.session_state.step >= len(df_full):
    st.session_state.step = config.INITIAL_STEP

# Slice data for the 'current' moment in simulation
df_sim = df_full.iloc[:st.session_state.step]
latest_row = df_sim.iloc[-1]
price, w_perc, m_perc, vol = data_engine.get_simulation_metrics(st.session_state.step - 1, df_full)

# Dashboard Layout
st.title(f"🏆 {config.ASSET_NAME} Market Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Risk (Vol)", f"{vol:.2f}%", vol, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    st.markdown('<div class="window-header">DYNAMIC MARKET TREND</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_sim.index, open=df_sim['Open'], high=df_sim['High'], low=df_sim['Low'],
                                 close=df_sim['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1.2)))

    # Plot historical trades recorded in session_state
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                 marker=dict(symbol='diamond', size=10, color='white'), name="Executed"))

    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="window-header">📰 MARKET HEADLINES</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_signal(latest_row)

    # Record trade if signal triggers
    if status != "NEUTRAL":
        if not st.session_state.trades or st.session_state.trades[-1]['Time'] != latest_row.name:
            st.session_state.trades.append({"Time": latest_row.name, "Price": price, "Action": status})

    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{latest_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{latest_row['MACD']:.2f}", "TRENDING", "#00E5FF")

# Rerun for simulation effect
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()