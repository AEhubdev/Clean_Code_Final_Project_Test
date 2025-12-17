import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = 100
    st.session_state.trades = []

df_full, news_list = data_engine.fetch_market_data()

# Simulation point
if st.session_state.step >= len(df_full):
    st.session_state.step = 100

latest_idx = st.session_state.step
current_row = df_full.iloc[latest_idx]
price, w_perc, m_perc, vol = data_engine.get_metrics_at_point(latest_idx, df_full)

# Dashboard
st.title(f"🏆 {config.ASSET_NAME} Market Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol:.2f}%", vol, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    st.markdown('<div class="window-header">MARKET TREND (Simulation Mode)</div>', unsafe_allow_html=True)
    fig = go.Figure()

    # SHOW ALL DATA
    fig.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'], low=df_full['Low'],
                                 close=df_full['Close'], name="Full History"))

    # Vertical line indicating "NOW" in the simulation
    fig.add_vline(x=current_row.name, line_width=2, line_dash="dash", line_color="white")

    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # News section
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_signal(current_row)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{current_row['MACD']:.2f}", "STABLE", "#00E5FF")

# Timer display so you know when the next 2-min update is coming
st.caption(f"Next update in {config.REFRESH_RATE}s... Current Index: {latest_idx}")

time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()