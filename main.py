import streamlit as st
import plotly.graph_objects as go
import data_engine, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# 1. SIDEBAR & DATA FETCH
choice = st.sidebar.selectbox("Timeframe", list(config.TIMEFRAME_OPTIONS.keys()), index=2)
interval_code = config.TIMEFRAME_OPTIONS[choice]
df, price = data_engine.get_gold_data(interval_code)


# 2. FRAGMENT (Safety Protected)
@st.fragment(run_every="15m")
def show_live_price_chart(data):
    st.markdown('<div class="window-header">LIVE PRICE ACTION</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close'], name="Gold"))

    # SAFETY: Only plot signals if columns actually exist
    if 'Buy_Signal' in data.columns and 'Sell_Signal' in data.columns:
        buys = data[data['Buy_Signal']]
        sells = data[data['Sell_Signal']]

        fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                 marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name='Buy'))
        fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                 marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name='Sell'))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)


# 3. DISPLAY
st.title("🏆 Gold Strategic Terminal")
col_main, col_news = st.columns([0.7, 0.3])

with col_main:
    show_live_price_chart(df)

    # Static Charts (These don't flicker or rerun every 15m)
    st.markdown("### Momentum History")
    fig_rsi = go.Figure(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#BB86FC')))
    fig_rsi.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(fig_rsi, use_container_width=True)

with col_news:
    st.markdown("### Signal Feed")
    st.dataframe(df[df['Buy_Signal'] | df['Sell_Signal']].tail(5)[['Close', 'RSI']])