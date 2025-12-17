import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import config, data_engine

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# Fetch fresh data
df_full, news_list = data_engine.fetch_market_data()

# Anchor to the VERY LAST ROW (Live Price)
if 'step' not in st.session_state:
    st.session_state.step = len(df_full) - 1
    st.session_state.trades = []

current_row = df_full.iloc[st.session_state.step]
price, w_perc, vol_val = data_engine.get_metrics(st.session_state.step, df_full)

# UI HEADER
st.title(f"🏆 {config.ASSET_NAME} LIVE TERMINAL")
st.write(f"**Current Trading Date:** {current_row.name.strftime('%B %d, %Y')}")

c1, c2, c3 = st.columns(3)
c1.metric("Current Price", f"${price:,.2f}")
c2.metric("Weekly Change", f"{w_perc:+.2f}%")
c3.metric("Volatility", f"{vol_val:.2f}%")

# --- GRAPHS ---
# Main Price & Trades
st.markdown("### 📈 PRICE ACTION & MOVING AVERAGES")
fig_p = go.Figure()
fig_p.add_trace(go.Candlestick(x=df_full.index, open=df_full['Open'], high=df_full['High'],
                               low=df_full['Low'], close=df_full['Close'], name="Price"))
fig_p.add_trace(go.Scatter(x=df_full.index, y=df_full['MA20'], name="MA20", line=dict(color='yellow')))
fig_p.add_trace(go.Scatter(x=df_full.index, y=df_full['MA50'], name="MA50", line=dict(color='red')))
fig_p.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
st.plotly_chart(fig_p, use_container_width=True)

# MACD Window
st.markdown("### 🚀 MACD MOMENTUM (With Signal Line)")
fig_m = go.Figure()
fig_m.add_trace(go.Bar(x=df_full.index, y=df_full['MACD_Hist'], name="Hist", marker_color='white'))
fig_m.add_trace(go.Scatter(x=df_full.index, y=df_full['MACD'], name="MACD", line=dict(color='cyan')))
fig_m.add_trace(go.Scatter(x=df_full.index, y=df_full['MACD_Signal'], name="Signal", line=dict(color='orange', dash='dot')))
fig_m.update_layout(template="plotly_dark", height=200)
st.plotly_chart(fig_m, use_container_width=True)

# RSI Window
st.markdown("### 📉 RSI OSCILLATOR")
fig_r = go.Figure(go.Scatter(x=df_full.index, y=df_full['RSI'], line=dict(color='purple')))
fig_r.add_hline(y=70, line_dash="dash", line_color="red")
fig_r.add_hline(y=30, line_dash="dash", line_color="green")
fig_r.update_layout(template="plotly_dark", height=150, yaxis=dict(range=[0, 100]))
st.plotly_chart(fig_r, use_container_width=True)

# NEWS SECTION
st.markdown("### 📰 LATEST HEADLINES")
for n in news_list:
    st.markdown(f"**[{n['title']}]({n['link']})**")

time.sleep(config.REFRESH_RATE)
st.rerun()