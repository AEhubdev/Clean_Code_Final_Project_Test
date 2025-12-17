import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, styles, data_engine, trading_logic

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_css()

if 'step' not in st.session_state:
    st.session_state.step = config.INITIAL_STEP

df_full, news_list = data_engine.fetch_market_data()

# Simulation point logic
if st.session_state.step >= len(df_full):
    st.session_state.step = config.INITIAL_STEP

current_row = df_full.iloc[st.session_state.step]
price, w_perc, m_perc, vol_val = data_engine.get_metrics_at_point(st.session_state.step, df_full)

# --- 1. TOP METRICS (Updating every 2 mins) ---
st.title(f"🏆 {config.ASSET_NAME} Market Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Price", f"${price:,.2f}")
styles.colored_metric(c2, "Weekly Change", f"{w_perc:+.2f}%", w_perc)
styles.colored_metric(c3, "Monthly Change", f"{m_perc:+.2f}%", m_perc)
styles.colored_metric(c4, "Volatility", f"{vol_val:.2f}%", vol_val, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    # --- PRICE CHART ---
    st.markdown('<div class="window-header">MARKET TREND & INDICATORS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'], low=df_full['Low'],
                                  close=df_full['Close'], name="Price"))
    fig1.add_trace(go.Scatter(x=df_full.index, y=df_full['MA20'], name="MA20", line=dict(color='#FFEB3B', width=1)))
    fig1.add_vline(x=current_row.name, line_width=2, line_dash="dash", line_color="#FFD700")  # THE "LIVE" MARKER
    fig1.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    # --- VOLUME CHART ---
    st.markdown('<div class="window-header">TRADING VOLUME</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(df_full['Close'], df_full['Open'])]
    fig2 = go.Figure(go.Bar(x=df_full.index, y=df_full['Volume'], marker_color=v_colors))
    fig2.update_layout(template="plotly_dark", height=150, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    # --- RSI CHART ---
    st.markdown('<div class="window-header">RELATIVE STRENGTH (RSI)</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df_full.index, y=df_full['RSI'], line=dict(color='#BB86FC')))
    fig3.add_hline(y=70, line_dash="dash", line_color="red")
    fig3.add_hline(y=30, line_dash="dash", line_color="green")
    fig3.update_layout(template="plotly_dark", height=150, margin=dict(t=0, b=0), yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig3, use_container_width=True)

    # --- MACD CHART ---
    st.markdown('<div class="window-header">MACD MOMENTUM</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df_full.index, y=df_full['MACD'], name="MACD", line=dict(color='#00E5FF')))
    fig4.add_trace(go.Scatter(x=df_full.index, y=df_full['MACD_Signal'], name="Signal", line=dict(color='#FFCA28')))
    fig4.update_layout(template="plotly_dark", height=150, margin=dict(t=0, b=0))
    st.plotly_chart(fig4, use_container_width=True)

    # Headlines
    st.markdown('<div class="window-header">📰 LATEST HEADLINES</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        styles.render_news_item(n)

with col_signals:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_signal(current_row)

    # These cards update based on the "Live Marker"
    styles.display_signal("ALGO RECOMMENDATION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{current_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("MACD", f"{current_row['MACD']:.2f}", "TRENDING", "#00E5FF")

    # Extra Data for the sidebar
    st.write(f"**Simulation Date:** {current_row.name.date()}")
    st.write(f"**Next Update:** {config.REFRESH_RATE} seconds")

# Logic loop
time.sleep(config.REFRESH_RATE)
st.session_state.step += 1
st.rerun()