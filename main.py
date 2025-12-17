import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import data_engine, config, time

st.set_page_config(page_title="Gold Terminal 2025", layout="wide")

# Fetch corrected data
df = data_engine.fetch_market_data()
price, change, vol = data_engine.get_live_metrics(df)

# --- DASHBOARD HEADER ---
st.title("🏆 Gold Market Intelligence")
st.subheader(f"Live Terminal: {df.index[-1].strftime('%B %d, %Y')}")

c1, c2, c3 = st.columns(3)
c1.metric("Live Market Price", f"${price:,.2f}")
c2.metric("Change since Dec 2024", f"{change:+.2f}%")
c3.metric("Annualized Volatility", f"{vol:.2f}%")

# --- CHART 1: PRICE & MA ---
st.markdown("### 📈 Price Action ($4,300+ Range)")
fig1 = go.Figure()
fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Gold"))
fig1.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='orange', width=2), name="MA50"))
fig1.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
st.plotly_chart(fig1, use_container_width=True)

# --- CHART 2: MACD MOMENTUM ---
st.markdown("### 🚀 MACD Signal & Histogram")
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="Hist", marker_color='gray'))
fig2.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='cyan')))
fig2.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal", line=dict(color='gold', dash='dot')))
fig2.update_layout(template="plotly_dark", height=200)
st.plotly_chart(fig2, use_container_width=True)

# --- CHART 3: RSI OSCILLATOR ---
st.markdown("### 📉 RSI Oscillator")
fig3 = go.Figure(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta')))
fig3.add_hline(y=70, line_color="red", line_dash="dash")
fig3.add_hline(y=30, line_color="green", line_dash="dash")
fig3.update_layout(template="plotly_dark", height=150, yaxis=dict(range=[0, 100]))
st.plotly_chart(fig3, use_container_width=True)

time.sleep(30)
st.rerun()