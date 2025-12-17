import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

# 1. Fetch Data
df_full, news_list = data_engine.fetch_market_data()

# 2. Hardened Initialization (Always starts at the LATEST row)
if 'step' not in st.session_state or st.session_state.step >= len(df_full):
    st.session_state.step = len(df_full) - 1
    st.session_state.trades = []

# Safety Check
current_idx = st.session_state.step
current_row = df_full.iloc[current_idx]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(current_idx, df_full)

# Trading Signal
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# --- UI DISPLAY ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    # 1. Price Window
    st.markdown('<div class="window-header">📈 PRICE ACTION & VOLATILITY</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'], low=df_full['Low'], close=df_full['Close'], name="Candles"))
    fig_p.add_trace(go.Scatter(x=df_full.index, y=df_full['MA50'], name="MA50", line=dict(color='#E91E63')))
    fig_p.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_U'], name="BB Upper", line=dict(color='rgba(173,216,230,0.2)')))
    fig_p.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_L'], name="BB Lower", line=dict(color='rgba(173,216,230,0.2)'), fill='tonexty'))
    fig_p.add_vline(x=current_row.name, line_width=2, line_dash="dash", line_color="#FFD700")
    fig_p.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_p, use_container_width=True)

    # 2. Volume Window
    st.markdown('<div class="window-header">📊 VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(df_full['Close'], df_full['Open'])]
    fig_v = go.Figure(go.Bar(x=df_full.index, y=df_full['Volume'], marker_color=v_colors))
    fig_v.update_layout(template="plotly_dark", height=180)
    st.plotly_chart(fig_v, use_container_width=True)

    # 3. Momentum (RSI + MACD Hist)
    st.markdown('<div class="window-header">🚀 MOMENTUM (RSI & MACD HISTOGRAM)</div>', unsafe_allow_html=True)
    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(x=df_full.index, y=df_full['RSI'], name="RSI", line=dict(color='#BB86FC')))
    h_colors = ['#00FF41' if val >= 0 else '#FF3131' for val in df_full['MACD_Hist']]
    fig_m.add_trace(go.Bar(x=df_full.index, y=df_full['MACD_Hist'], name="MACD Hist", marker_color=h_colors))
    fig_m.update_layout(template="plotly_dark", height=250)
    st.plotly_chart(fig_m, use_container_width=True)

    st.markdown('<div class="window-header">📰 MARKET NEWS</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{current_row['MACD']:.2f}", "STABLE", "#00E5FF")
    st.write(f"**Last Sync:** {current_row.name}")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)

# Loop
time.sleep(config.REFRESH_RATE)
st.rerun()