import streamlit as st
import plotly.graph_objects as go
import data_engine, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# 1. LOAD STATIC DATA (Reruns only on full page refresh or timeframe change)
selected_interval = st.sidebar.selectbox("Timeframe", list(config.TIMEFRAME_OPTIONS.keys()), index=2)
interval_code = config.TIMEFRAME_OPTIONS[selected_interval]
df = data_engine.get_base_data(interval_code)


# 2. THE LIVE PRICE FRAGMENT
@st.fragment(run_every="15m")
def show_live_price_chart(data):
    # This block updates every 15 mins without touching the rest of the page
    st.markdown('<div class="window-header">LIVE PRICE CHART (Updates every 15m)</div>', unsafe_allow_html=True)

    # Optionally: fetch just the absolute latest price to append/update
    # current_price = data_engine.get_live_price()

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close']))

    # Add your Buy/Sell Triangles here
    buys = data[data['Buy_Signal']]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.99, mode='markers',
                             marker=dict(symbol='triangle-up', color='#00FF41')))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)


# 3. DISPLAY THE DASHBOARD
st.title("🏆 Gold Strategic Terminal")

col_charts, col_signals = st.columns([0.7, 0.3])

with col_charts:
    # This part updates automatically
    show_live_price_chart(df)

    st.divider()

    # THESE PARTS ARE FIXED (Only update if you change timeframe)
    st.markdown("### Fixed Momentum & Volume Analysis")
    # ... (Render Volume, RSI, and MACD charts here) ...

with col_signals:
    # Sidebar remains static
    st.markdown("### Signal Center")
    # ... (Render News and Signal status) ...