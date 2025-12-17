import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = 100 # Back to the offset you had
    st.session_state.trades = []

df_full, news_list = data_engine.fetch_market_data()

# Simulation loop
if st.session_state.step >= len(df_full):
    st.session_state.step = 100

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# --- HEADER ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    # 1. PRICE ACTION WINDOW
    st.markdown('<div class="window-header">📈 PRICE ACTION & BOLLINGER BANDS</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=df_full.index[:st.session_state.step],
                                 open=df_full['Open'], high=df_full['High'],
                                 low=df_full['Low'], close=df_full['Close'], name="Price"))
    fig_p.add_trace(go.Scatter(x=df_full.index[:st.session_state.step], y=df_full['MA50'], name="MA50", line=dict(color='#E91E63')))
    fig_p.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_p, use_container_width=True)

    # 2. VOLUME WINDOW
    st.markdown('<div class="window-header">📊 TRADING VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(df_full['Close'], df_full['Open'])]
    fig_v = go.Figure(go.Bar(x=df_full.index[:st.session_state.step], y=df_full['Volume'], marker_color=v_colors))
    fig_v.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig_v, use_container_width=True)

    # 3. RSI WINDOW
    st.markdown('<div class="window-header">📉 RELATIVE STRENGTH (RSI) HISTORY</div>', unsafe_allow_html=True)
    fig_r = go.Figure(go.Scatter(x=df_full.index[:st.session_state.step], y=df_full['RSI'], line=dict(color='#BB86FC')))
    fig_r.add_hline(y=70, line_dash="dash", line_color="red")
    fig_r.add_hline(y=30, line_dash="dash", line_color="green")
    fig_r.update_layout(template="plotly_dark", height=200, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_r, use_container_width=True)

    # 4. MACD WINDOW
    st.markdown('<div class="window-header">🚀 MACD MOMENTUM & HISTOGRAM</div>', unsafe_allow_html=True)
    fig_m = go.Figure()
    h_colors = ['#00FF41' if val >= 0 else '#FF3131' for val in df_full['MACD_Hist']]
    fig_m.add_trace(go.Bar(x=df_full.index[:st.session_state.step], y=df_full['MACD_Hist'], marker_color=h_colors))
    fig_m.add_trace(go.Scatter(x=df_full.index[:st.session_state.step], y=df_full['MACD'], line=dict(color='#00E5FF')))
    fig_m.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig_m, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_signal(current_row)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    st.info(f"Simulation Step: {st.session_state.step} | Date: {current_row.name.date()}")

time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()