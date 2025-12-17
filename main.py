import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, time

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# Custom CSS for that "Bloomberg" dark feel
st.markdown("""
    <style>
    .metric-container { background: #1e1e1e; padding: 15px; border-radius: 10px; border-left: 5px solid gold; }
    .signal-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

df = data_engine.fetch_market_data()
latest = df.iloc[-1]
status, color = trading_logic.evaluate_signal(latest)

# --- OVERVIEW SECTION ---
st.title("🏆 GOLD STRATEGIC TERMINAL")
st.caption(f"Market Status: OPEN | Last Update: {df.index[-1].strftime('%Y-%m-%d %H:%M')}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Live Price", f"${latest['Close']:,.2f}")
with m2: st.metric("Daily Change", f"{((latest['Close'] - latest['Open']) / latest['Open'] * 100):+.2f}%")
with m3: st.metric("RSI (14D)", f"{latest['RSI']:.1f}")
with m4:
    st.markdown(f'<div class="signal-box" style="background:{color}; color:white">{status}</div>',
                unsafe_allow_html=True)

st.markdown("---")

# --- MARKET CHART SECTION ---
col_charts, col_info = st.columns([0.7, 0.3])

with col_charts:
    # Main Chart with Signals
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))

    # Add SMA Lines
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='cyan', width=1), name="MA20"))

    # Add Signal Diamonds (The logic that was missing)
    buys = df[df.apply(lambda x: trading_logic.evaluate_signal(x)[0] == "BUY", axis=1)]
    sells = df[df.apply(lambda x: trading_logic.evaluate_signal(x)[0] == "SELL", axis=1)]

    fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.99, mode='markers',
                             marker=dict(symbol='diamond', color='#00FF41', size=10), name="BUY SIGNAL"))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.01, mode='markers',
                             marker=dict(symbol='diamond', color='#FF3131', size=10), name="SELL SIGNAL"))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False,
                      margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_info:
    st.markdown("### 📊 Market Context")
    st.write(f"**52W High:** ${df['High'].max():,.2f}")
    st.write(f"**52W Low:** ${df['Low'].min():,.2f}")
    st.write(f"**Current Trend:** {'Bullish' if latest['MA20'] > latest['MA50'] else 'Bearish'}")

    st.markdown("### 🔔 Signal Log")
    log_df = df.apply(lambda x: trading_logic.evaluate_signal(x)[0], axis=1).to_frame(name="Action")
    st.dataframe(log_df[log_df['Action'] != "NEUTRAL"].tail(5), use_container_width=True)

time.sleep(30)
st.rerun()