import streamlit as st
import plotly.graph_objects as go
import data_engine, time

st.set_page_config(page_title="Gold Elite Terminal", layout="wide")

# Custom UI Styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: gold; }
    .signal-card { padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

df = data_engine.fetch_market_data()
latest = df.iloc[-1]
price = latest['Close']
prev_price = df['Close'].iloc[-2]
status, status_color = data_engine.get_signal(latest)

# --- 1. OVERVIEW TOP BAR ---
st.title("🏆 GOLD STRATEGIC TERMINAL")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live Gold Price", f"${price:,.2f}", f"{price - prev_price:+.2f}")
c2.metric("RSI (14D)", f"{latest['RSI']:.2f}")
c3.metric("MACD Hist", f"{latest['MACD_Hist']:.2f}")
c4.metric("Volatility", f"{(df['Close'].pct_change().std() * 100):.2f}%")

st.divider()

# --- 2. MAIN DASHBOARD SPLIT ---
col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    st.subheader("Market Price Action")
    # Price Chart Fix: Explicitly use df.index
    fig_p = go.Figure()
    fig_p.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
    fig_p.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='cyan', width=1.5), name="MA20"))
    fig_p.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_p, use_container_width=True)

    # Momentum Panel
    fig_m = go.Figure()
    colors = ['#00FF41' if x >= 0 else '#FF3131' for x in df['MACD_Hist']]
    fig_m.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors, name="MACD Hist"))
    fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='white'), name="MACD Line"))
    fig_m.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_m, use_container_width=True)

with col_signals:
    st.subheader("System Signals")
    # Current Signal Box
    st.markdown(f"""
        <div class="signal-card" style="background-color: {status_color}22; border-left: 5px solid {status_color};">
            <h4 style="margin:0; color:{status_color};">CURRENT ACTION</h4>
            <h2 style="margin:0;">{status}</h2>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Signal History")
    # Filter for signals
    history = df.tail(10).copy()
    history['Signal'] = history.apply(lambda x: data_engine.get_signal(x)[0], axis=1)
    st.dataframe(history[['Close', 'Signal']].sort_index(ascending=False), use_container_width=True)

    st.info(f"Last Scan: {df.index[-1].strftime('%H:%M:%S')}")

time.sleep(30)
st.rerun()