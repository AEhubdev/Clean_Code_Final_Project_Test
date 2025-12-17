import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

df_full, news_list = data_engine.fetch_market_data()

# Ensure we are at the LIVE end of the data
if 'step' not in st.session_state:
    st.session_state.step = len(df_full) - 1
    st.session_state.trades = []

# Update price and indicators for the current "Live" moment
current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# Logic for Signal generation
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    # Prevent duplicate logs for the same timestamp
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# --- UI DISPLAY ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
st.caption(f"Last Sync: {current_row.name.strftime('%Y-%m-%d %H:%M:%S')}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)

col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    hist_df = df_full.iloc[:st.session_state.step + 1]

    # CHART 1: PRICE & SIGNALS
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'],
                                   close=hist_df['Close'], name="Gold"))

    # Add Signal Markers (The Diamonds)
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig_p.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                   marker=dict(symbol='diamond', size=15, color='white',
                                               line=dict(width=2, color='gold')),
                                   name="ALGO SIGNAL"))

    fig_p.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False,
                        title="Price Action & Trade Execution")
    st.plotly_chart(fig_p, use_container_width=True)

    # CHART 2: MACD + SIGNAL LINE
    fig_m = go.Figure()
    # Histogram
    h_cols = ['#00FF41' if x >= 0 else '#FF3131' for x in hist_df['MACD_Hist']]
    fig_m.add_trace(go.Bar(x=hist_df.index, y=hist_df['MACD_Hist'], name="Hist", marker_color=h_cols))
    # MACD Line
    fig_m.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD'], name="MACD", line=dict(color='#00E5FF', width=2)))
    # Signal Line
    fig_m.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD_Signal'], name="Signal",
                               line=dict(color='#FFD700', width=2, dash='dot')))

    fig_m.update_layout(template="plotly_dark", height=250, title="MACD Momentum")
    st.plotly_chart(fig_m, use_container_width=True)

with col_signals:
    st.markdown("### 📡 SYSTEM STATUS")
    styles.display_signal("ALGO RECOMMENDATION", status, "ACTIVE", color)
    st.markdown("---")
    st.write("**Recent Signal Log**")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(10), use_container_width=True)
    else:
        st.info("Searching for market entry signals...")

time.sleep(config.REFRESH_RATE)
st.rerun()