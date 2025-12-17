import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import data_engine, time

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CSS for Bloomberg-style Overview
st.markdown("""
    <style>
    [data-testid="stMetric"] { background: #111; border: 1px solid #333; padding: 15px; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: gold !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

df = data_engine.fetch_market_data()
latest = df.iloc[-1]
status, s_color = data_engine.get_signal_logic(latest)

# --- SECTION 1: OVERVIEW BAR ---
st.title("🏆 GOLD STRATEGIC TERMINAL")
m1, m2, m3, m4 = st.columns(4)
m1.metric("LIVE PRICE", f"${latest['Close']:,.2f}", f"{latest['Close'] - df['Close'].iloc[-2]:+.2f}")
m2.metric("RSI (14D)", f"{latest['RSI']:.1f}")
m3.metric("MACD HIST", f"{latest['MACD_Hist']:.2f}")
m4.metric("VOLATILITY", f"{(df['Close'].pct_change().std() * 100):.2f}%")

st.divider()

# --- SECTION 2: MAIN DASHBOARD (70/30 SPLIT) ---
col_left, col_right = st.columns([0.72, 0.28])

with col_left:
    # --- CHART: PRICE + BB + VOLUME ---
    # We use subplots to separate Volume from Price
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, subplot_titles=('Price & BBs', 'Volume'),
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(
        go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Gold"),
        row=1, col=1)

    # Bollinger Bands & MAs
    fig.add_trace(
        go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(173, 216, 230, 0.4)'), name="BB Upper"), row=1,
        col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(173, 216, 230, 0.4)'), name="BB Lower",
                             fill='tonexty'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='gold', width=1.5), name="MA20"), row=1, col=1)

    # Volume (Separated at bottom)
    colors = ['green' if df['Close'].iloc[i] > df['Open'].iloc[i] else 'red' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False,
                      margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    # --- MOMENTUM CHARTS (MACD / RSI) ---
    st.markdown("#### Momentum Oscillators")
    fig_mom = make_subplots(rows=1, cols=2)
    # MACD
    fig_mom.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name="MACD Hist"), row=1, col=1)
    # RSI
    fig_mom.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=1, col=2)
    fig_mom.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(fig_mom, use_container_width=True)

with col_right:
    st.markdown("### 🔔 SYSTEM SIGNALS")
    st.markdown(f"""
        <div style="background:{s_color}; padding:20px; border-radius:10px; text-align:center;">
            <h1 style="color:white; margin:0;">{status}</h1>
            <small style="color:white;">Based on RSI/BB Alignment</small>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Signal Log")
    log = df.tail(15).copy()
    log['Signal'] = log.apply(lambda x: data_engine.get_signal_logic(x)[0], axis=1)
    st.table(log[['Close', 'Signal']].sort_index(ascending=False))

time.sleep(30)
st.rerun()