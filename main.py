import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = config.MA_LONG + 5  # Start only when indicators are ready
    st.session_state.trades = []

# Fetch All Data
df_full, news_list = data_engine.get_market_data()

# Logic to loop simulation
if st.session_state.step >= len(df_full):
    st.session_state.step = config.MA_LONG + 5

# Create the specific 'moment in time' for the simulation
df_sim = df_full.iloc[:st.session_state.step]
latest_row = df_sim.iloc[-1]
current_p, w_perc, m_perc, vol_val = data_engine.calculate_top_metrics(df_sim)

# Header Metrics
st.title(f"🏆 {config.ASSET_NAME} Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${current_p:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

# Visualization
col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    st.markdown('<div class="window-header">DYNAMIC MARKET CHART</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_sim.index, open=df_sim['Open'], high=df_sim['High'], low=df_sim['Low'],
                                 close=df_sim['Close'], name="Price"))
    fig.add_trace(go.Scatter(x=df_sim.index, y=df_sim['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1.5)))

    # Markers for buys/sells
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                 marker=dict(symbol='diamond', size=10, color='white'), name="Signals"))

    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="window-header">📰 MARKET HEADLINES</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)  # CRITICAL: This matches styles.py

with col_signals:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.generate_signal(latest_row)

    if status != "NEUTRAL":
        if not st.session_state.trades or st.session_state.trades[-1]['Time'] != latest_row.name:
            st.session_state.trades.append({"Time": latest_row.name, "Price": current_p, "Action": status})

    styles.display_signal("ALGO ADVICE", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{latest_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{latest_row['MACD']:.2f}", "STABLE", "#00E5FF")

# Advance simulation
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()