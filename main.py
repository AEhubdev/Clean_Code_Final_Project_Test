import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = config.INITIAL_STEP
    st.session_state.trades = []

df_full, news_list = data_engine.fetch_market_data()

if st.session_state.step >= len(df_full):
    st.session_state.step = config.INITIAL_STEP

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# Trading Signal Record
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# --- UI HEADER ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    # 1. PRICE WINDOW
    st.markdown('<div class="window-header">📈 PRICE ACTION & BOLLINGER BANDS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    # history limited by simulation step
    hist_df = df_full.iloc[:st.session_state.step + 1]
    fig1.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'], close=hist_df['Close'], name="Price"))
    fig1.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MA50'], name="MA50", line=dict(color='#E91E63')))
    fig1.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, use_container_width=True)

    # 2. VOLUME WINDOW
    st.markdown('<div class="window-header">📊 VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(hist_df['Close'], hist_df['Open'])]
    fig2 = go.Figure(go.Bar(x=hist_df.index, y=hist_df['Volume'], marker_color=v_colors))
    fig2.update_layout(template="plotly_dark", height=180)
    st.plotly_chart(fig2, use_container_width=True)

    # 3. RSI WINDOW
    st.markdown('<div class="window-header">📉 RSI OSCILLATOR</div>', unsafe_allow_html=True)
    fig3 = go.Figure(go.Scatter(x=hist_df.index, y=hist_df['RSI'], line=dict(color='#BB86FC')))
    fig3.add_hline(y=70, line_dash="dash", line_color="red")
    fig3.add_hline(y=30, line_dash="dash", line_color="green")
    fig3.update_layout(template="plotly_dark", height=180, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig3, use_container_width=True)

    # 4. MACD WINDOW
    st.markdown('<div class="window-header">🚀 MACD MOMENTUM</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    m_colors = ['#00FF41' if val >= 0 else '#FF3131' for val in hist_df['MACD_Hist']]
    fig4.add_trace(go.Bar(x=hist_df.index, y=hist_df['MACD_Hist'], marker_color=m_colors))
    fig4.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD'], line=dict(color='#00E5FF')))
    fig4.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig4, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    st.write(f"**Step:** {st.session_state.step}")
    st.write(f"**Date:** {current_row.name.date()}")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)

# Loop refresh
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()