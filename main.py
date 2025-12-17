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

# Simulation step
if st.session_state.step >= len(df_full):
    st.session_state.step = 100

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# Record Signals automatically
status, color = trading_logic.evaluate_signal(current_row)
if status != "NEUTRAL":
    if not st.session_state.trades or st.session_state.trades[-1]['Time'] != current_row.name:
        st.session_state.trades.append({"Time": current_row.name, "Price": price, "Action": status})

# --- UI LAYOUT ---
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    # 1. PRICE & BOLLINGER BANDS & MAs
    st.markdown('<div class="window-header">MARKET TREND & VOLATILITY BANDS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'], low=df_full['Low'],
                                  close=df_full['Close'], name="Candlestick"))

    # MA Lines
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1)))
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['MA50'], name="MA50", line=dict(color='#E91E63', width=1)))

    # Bollinger Bands
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_U'], name="BB Upper",
                              line=dict(color='rgba(173, 216, 230, 0.3)', dash='dash')))
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['BB_L'], name="BB Lower",
                              line=dict(color='rgba(173, 216, 230, 0.3)', dash='dash'), fill='tonexty'))

    # Trading Signal Markers
    if st.session_state.trades:
        tdf = pd.DataFrame(st.session_state.trades)
        fig1.add_trace(go.Scatter(x=tdf['Time'], y=tdf['Price'], mode='markers',
                                  marker=dict(symbol='diamond', size=10, color='white'), name="Algo Signal"))

    fig1.add_vline(x=current_row.name, line_width=2, line_dash="dash", line_color="#FFD700")
    fig1.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    # 2. RSI & MACD Combined Window
    st.markdown('<div class="window-header">MOMENTUM & STRENGTH INDICATORS</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_full.index, y=df_full['RSI'], name="RSI", line=dict(color='#BB86FC')))
    fig2.add_trace(go.Scatter(x=df_full.index, y=df_full['MACD'], name="MACD", line=dict(color='#00E5FF')))
    fig2.add_hline(y=70, line_dash="dash", line_color="red")
    fig2.add_hline(y=30, line_dash="dash", line_color="green")
    fig2.update_layout(template="plotly_dark", height=300, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    # Headlines
    st.markdown('<div class="window-header">📰 NEWS FEED</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{current_row['MACD']:.2f}", "STABLE", "#00E5FF")

    # Trade Log Sidebar
    st.markdown("**Executed Signals Log**")
    if st.session_state.trades:
        st.dataframe(pd.DataFrame(st.session_state.trades).tail(5), use_container_width=True)

# Loop
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()