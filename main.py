import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = config.INITIAL_STEP
    st.session_state.trades = []

df_full, news_list = data_engine.fetch_market_data()

# Simulation step control
if st.session_state.step >= len(df_full):
    st.session_state.step = config.INITIAL_STEP

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# Record Trading Signals
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
    # 1. MAIN PRICE & VOLUME SUBPLOT
    st.markdown('<div class="window-header">MARKET TREND, VOLATILITY & VOLUME</div>', unsafe_allow_html=True)
    fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         vertical_spacing=0.03, subplot_titles=('', ''),
                         row_width=[0.3, 0.7])

    # Candlestick
    fig1.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'],
                                  low=df_full['Low'], close=df_full['Close'], name="Price"), row=1, col=1)

    # Indicators on Price Chart
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1)),
                   row=1, col=1)
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['MA50'], name="MA50", line=dict(color='#E91E63', width=1)),
                   row=1, col=1)
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_U'], name="BB Upper",
                              line=dict(color='rgba(173, 216, 230, 0.2)', dash='dash')), row=1, col=1)
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_L'], name="BB Lower",
                              line=dict(color='rgba(173, 216, 230, 0.2)', dash='dash'), fill='tonexty'), row=1, col=1)

    # Volume Bar Chart
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(df_full['Close'], df_full['Open'])]
    fig1.add_trace(go.Bar(x=df_full.index, y=df_full['Volume'], name="Volume", marker_color=v_colors), row=2, col=1)

    # Signal Markers
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig1.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                  marker=dict(symbol='diamond', size=10, color='white'), name="Algo Signal"), row=1,
                       col=1)

    fig1.add_vline(x=current_row.name, line_width=2, line_dash="dash", line_color="#FFD700", row='all', col=1)
    fig1.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    # 2. MOMENTUM SUBPLOT (RSI & MACD HISTOGRAM)
    st.markdown('<div class="window-header">MOMENTUM & MACD HISTOGRAM</div>', unsafe_allow_html=True)
    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.5, 0.5])

    # RSI
    fig2.add_trace(go.Scatter(x=df_full.index, y=df_full['RSI'], name="RSI", line=dict(color='#BB86FC')), row=1, col=1)
    fig2.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
    fig2.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)

    # MACD Histogram & Lines
    h_colors = ['#00FF41' if val >= 0 else '#FF3131' for val in df_full['MACD_Hist']]
    fig2.add_trace(go.Bar(x=df_full.index, y=df_full['MACD_Hist'], name="MACD Hist", marker_color=h_colors), row=2,
                   col=1)
    fig2.add_trace(
        go.Scatter(x=df_full.index, y=df_full['MACD'], name="MACD Line", line=dict(color='#00E5FF', width=1)), row=2,
        col=1)
    fig2.add_trace(
        go.Scatter(x=df_full.index, y=df_full['MACD_Signal'], name="Signal Line", line=dict(color='#FFCA28', width=1)),
        row=2, col=1)

    fig2.update_layout(template="plotly_dark", height=400, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    # News Feed
    st.markdown('<div class="window-header">📰 NEWS FEED</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{current_row['MACD']:.2f}", "STABLE", "#00E5FF")

    st.markdown("**Executed Signals Log**")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(10), use_container_width=True)

# Loop with 2-minute refresh
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()