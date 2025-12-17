import streamlit as st
import plotly.graph_objects as go
import data_engine, config, time

st.set_page_config(page_title="Gold Terminal 2025", layout="wide")

# Get clean data
df = data_engine.fetch_market_data()
latest_price = float(df['Close'].iloc[-1])

# Header Metrics
st.title(f"🏆 {config.ASSET_NAME} Advanced Terminal")
st.subheader(f"Current Date: {df.index[-1].strftime('%Y-%m-%d')}")

col_m1, col_m2 = st.columns(2)
col_m1.metric("Live Market Price", f"${latest_price:,.2f}")
col_m2.metric("RSI (14D)", f"{df['RSI'].iloc[-1]:.2f}")

# --- PANEL 1: PRICE & CANDLESTICKS ---
st.markdown("#### 📈 Price Action & Moving Averages")
fig_p = go.Figure()
fig_p.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Gold"))
fig_p.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20", line=dict(color='rgba(255, 255, 0, 0.7)')))
fig_p.add_trace(go.Scatter(x=df.index, y=df['MA50'], name="MA50", line=dict(color='rgba(255, 0, 0, 0.7)')))
fig_p.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=30, b=0))
st.plotly_chart(fig_p, use_container_width=True)

# --- PANEL 2: MACD WINDOW ---
st.markdown("#### 🚀 MACD Momentum")
fig_m = go.Figure()
# Histogram
colors = ['green' if x >= 0 else 'red' for x in df['MACD_Hist']]
fig_m.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="Histogram", marker_color=colors))
# MACD & Signal Lines
fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='cyan', width=2)))
fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal", line=dict(color='orange', dash='dot')))
fig_m.update_layout(template="plotly_dark", height=250, margin=dict(t=0, b=0))
st.plotly_chart(fig_m, use_container_width=True)

# --- PANEL 3: RSI WINDOW ---
st.markdown("#### 📉 RSI Oscillator")
fig_r = go.Figure()
fig_r.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta', width=2)))
fig_r.add_hline(y=70, line_dash="dash", line_color="red")
fig_r.add_hline(y=30, line_dash="dash", line_color="green")
fig_r.update_layout(template="plotly_dark", height=180, yaxis=dict(range=[0, 100]), margin=dict(t=0, b=0))
st.plotly_chart(fig_r, use_container_width=True)

time.sleep(config.REFRESH_RATE)
st.rerun()