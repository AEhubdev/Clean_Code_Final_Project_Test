import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

df_full, news_list = data_engine.fetch_market_data()

# INITIALIZATION
if 'step' not in st.session_state:
    # Anchor to the end for Live Price ($4300+)
    st.session_state.step = len(df_full) - 1
    st.session_state.trades = []

if st.session_state.step >= len(df_full):
    st.session_state.step = len(df_full) - 1

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# SIGNAL TRACKER
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# UI HEADER
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    hist_df = df_full.iloc[:st.session_state.step + 1]

    # 1. PRICE CHART
    st.markdown('<div class="window-header">📈 PRICE ACTION & BB BANDS</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'],
                                   close=hist_df['Close'], name="Price"))
    fig_p.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MA50'], name="MA50", line=dict(color='#E91E63')))
    fig_p.add_trace(go.Scatter(x=hist_df.index, y=hist_df['BB_U'], name="BB Upper",
                               line=dict(color='rgba(173,216,230,0.3)', dash='dash')))
    fig_p.add_trace(go.Scatter(x=hist_df.index, y=hist_df['BB_L'], name="BB Lower",
                               line=dict(color='rgba(173,216,230,0.3)', dash='dash'), fill='tonexty'))

    # SHOW HISTORICAL SIGNALS ON CHART
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig_p.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                   marker=dict(symbol='diamond', size=12, color='white',
                                               line=dict(width=2, color='gold')), name="Algo Signal"))

    fig_p.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig_p, use_container_width=True)

    # 2. VOLUME
    st.markdown('<div class="window-header">📊 VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(hist_df['Close'], hist_df['Open'])]
    fig_v = go.Figure(go.Bar(x=hist_df.index, y=hist_df['Volume'], marker_color=v_colors))
    fig_v.update_layout(template="plotly_dark", height=150)
    st.plotly_chart(fig_v, use_container_width=True)

    # 3. MACD WINDOW (Fixed Signal Line)
    st.markdown('<div class="window-header">🚀 MACD MOMENTUM & SIGNAL LINE</div>', unsafe_allow_html=True)
    fig_m = go.Figure()
    h_colors = ['#00FF41' if val >= 0 else '#FF3131' for val in hist_df['MACD_Hist']]
    fig_m.add_trace(go.Bar(x=hist_df.index, y=hist_df['MACD_Hist'], name="Histogram", marker_color=h_colors))
    fig_m.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD'], name="MACD", line=dict(color='#00E5FF', width=2)))
    fig_m.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD_Signal'], name="Signal Line",
                               line=dict(color='#FFD700', width=2, dash='dot')))
    fig_m.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig_m, use_container_width=True)

    # 4. RSI WINDOW
    st.markdown('<div class="window-header">📉 RSI OSCILLATOR</div>', unsafe_allow_html=True)
    fig_r = go.Figure(go.Scatter(x=hist_df.index, y=hist_df['RSI'], line=dict(color='#BB86FC')))
    fig_r.add_hline(y=70, line_dash="dash", line_color="red")
    fig_r.add_hline(y=30, line_dash="dash", line_color="green")
    fig_r.update_layout(template="plotly_dark", height=150, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_r, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    st.write(f"**Current Date:** {current_row.name.date()}")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(10), use_container_width=True)

time.sleep(config.REFRESH_RATE)
st.rerun()