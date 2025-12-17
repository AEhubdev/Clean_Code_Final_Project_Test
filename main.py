import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = 100
    st.session_state.trades = []

# Data Acquisition
df_full, news_list = data_engine.get_market_data()

# Logic to prevent index errors
if st.session_state.step >= len(df_full):
    st.session_state.step = 100  # Reset if reaches end

df_sim = df_full.iloc[:st.session_state.step]
latest = df_sim.iloc[-1]
price = float(latest['Close'])

# Pass the current step index to get accurate "live" metrics
w_c, m_c, y_c, vol = data_engine.calculate_top_metrics(st.session_state.step - 1, df_full)

# UI Header
st.title(f"🏆 {config.ASSET_NAME} Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly %", f"{w_c:+.2f}%", w_c)
styles.colored_metric(c3, "Monthly %", f"{m_c:+.2f}%", m_c)
styles.colored_metric(c4, "YTD %", f"{y_c:+.2f}%", y_c)
styles.colored_metric(c5, "Volatility", f"{vol:.2f}%", vol, is_vol=True)
st.divider()

# Charts & Sidebar
col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    st.markdown('<div class="window-header">LIVE TREND & INDICATORS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=df_sim.index, open=df_sim['Open'], high=df_sim['High'], low=df_sim['Low'],
                                  close=df_sim['Close'], name="Price"))
    fig1.add_trace(go.Scatter(x=df_sim.index, y=df_sim['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1)))

    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig1.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                  marker=dict(symbol='diamond', size=10, color='white'), name="Signals"))

    fig1.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown('<div class="window-header">📰 LATEST HEADLINES</div>', unsafe_allow_html=True)
    if news_list:
        for n in news_list[:5]:
            styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 TRADING SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.generate_signal(latest)

    if status != "NEUTRAL":
        if not st.session_state.trades or st.session_state.trades[-1]['Time'] != latest.name:
            st.session_state.trades.append({"Time": latest.name, "Price": price, "Action": status})

    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{latest['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{latest['MACD']:.2f}", "TRENDING", "#00E5FF")

# Simulation Loop
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()