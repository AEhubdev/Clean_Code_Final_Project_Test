import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

# --- DATA ---
df_full, news_list = data_engine.fetch_market_data()

# --- CORE LOGIC: STAY ON LIVE DATA ---
# This ensures we are always looking at the very last row (Current Price)
if 'step' not in st.session_state or st.session_state.step >= len(df_full):
    st.session_state.step = len(df_full) - 1
    st.session_state.trades = []

# Fetch row based on fixed step
current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# --- SIGNALS ---
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# --- UI HEADER ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
st.subheader(f"Trading Date: {current_row.name.strftime('%B %d, %Y')}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    # Use full history up to now for charts
    hist_df = df_full.iloc[:st.session_state.step + 1]

    # 1. MAIN PRICE CHART
    st.markdown('<div class="window-header">📈 PRICE ACTION</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'],
                                   close=hist_df['Close'], name="Price"))
    fig_p.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MA50'], name="MA50", line=dict(color='#E91E63', width=1.5)))

    # Plot trade signals
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig_p.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                   marker=dict(symbol='diamond', size=12, color='gold'), name="Signals"))

    fig_p.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig_p, use_container_width=True)

    # 2. MACD (Now with visible Signal Line)
    st.markdown('<div class="window-header">🚀 MACD MOMENTUM</div>', unsafe_allow_html=True)
    fig_m = go.Figure()
    fig_m.add_trace(go.Bar(x=hist_df.index, y=hist_df['MACD_Hist'], name="Histogram", marker_color='gray'))
    fig_m.add_trace(go.Scatter(x=hist_df.index, y=hist_df['MACD'], name="MACD", line=dict(color='#00E5FF')))
    fig_m.add_trace(
        go.Scatter(x=hist_df.index, y=hist_df['MACD_Signal'], name="Signal", line=dict(color='#FFD700', dash='dot')))
    fig_m.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(fig_m, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")

    st.markdown("**Recent Trade Log**")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)

# Pause before refresh
time.sleep(config.REFRESH_RATE)
st.rerun()