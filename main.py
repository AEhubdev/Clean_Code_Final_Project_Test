import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles

st.set_page_config(page_title="Gold Elite Terminal", layout="wide")
styles.apply_custom_styles()

# DATA & LOGIC
data, price, df_full = data_engine.get_gold_data()
data = trading_logic.get_signals(data)
latest = data.iloc[-1]

# HEADER METRICS
st.title("🏆 Gold Market Strategic Terminal")
c1, c2, c3, c4 = st.columns(4)
styles.colored_metric(c1, "Current Price", f"${price:,.2f}", 1)
styles.colored_metric(c2, "RSI (14)", f"{latest['RSI']:.1f}", 0)
styles.colored_metric(c3, "MACD Hist", f"{latest['MACD_Hist']:.2f}", latest['MACD_Hist'])
styles.colored_metric(c4, "Stoch %K", f"{latest['STOCH_K']:.1f}%", 0, is_vol=True)

st.divider()

col_charts, col_signals = st.columns([0.75, 0.25])

with col_charts:
    st.markdown('<div class="window-header">LIVE PRICE ACTION & SIGNALS</div>', unsafe_allow_html=True)
    fig = go.Figure()
    # Candlestick
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Gold"))

    # Technical Overlays
    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA20", line=dict(color='gold', width=1)))
    fig.add_trace(
        go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper", line=dict(color='rgba(173,216,230,0.3)', dash='dot')))
    fig.add_trace(
        go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower", line=dict(color='rgba(173,216,230,0.3)', dash='dot'),
                   fill='tonexty', fillcolor='rgba(173,216,230,0.02)'))

    # CHART SIGNALS (The requested feature)
    buys = data[data['Buy_Signal']]
    sells = data[data['Sell_Signal']]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.995, mode='markers',
                             marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name='BUY SIGNAL'))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.005, mode='markers',
                             marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name='SELL SIGNAL'))

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest)
    styles.display_signal("PRIMARY ACTION", status, "NOW", color)
    styles.display_signal("RSI MOMENTUM", f"{latest['RSI']:.1f}", "ACTIVE", color)
    styles.display_signal("MACD TREND", "BULLISH" if latest['MACD_Hist'] > 0 else "BEARISH", "LIVE", "#00E5FF")

    st.markdown("---")
    st.subheader("Recent Triggers")
    st.dataframe(data[data['Buy_Signal'] | data['Sell_Signal']][['Close', 'RSI']].tail(5), use_container_width=True)