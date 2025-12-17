import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

data, price, df_full = data_engine.get_gold_data()
latest = data.iloc[-1]

# --- HEADER ---
st.title("🏆 Gold Market Strategic Terminal")
c1, c2, c3, c4 = st.columns(4)
styles.colored_metric(c1, "Current Price", f"${price:,.2f}", 1)
styles.colored_metric(c2, "RSI (14)", f"{latest['RSI']:.1f}", 0)
styles.colored_metric(c3, "MACD Trend", "Bullish" if latest['MACD_Hist'] > 0 else "Bearish",
                      1 if latest['MACD_Hist'] > 0 else -1)
styles.colored_metric(c4, "Stoch %K", f"{latest['STOCH_K']:.1f}%", 0, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    # WINDOW 1: TREND & SIGNALS
    st.markdown('<div class="window-header">MARKET TREND & CHART SIGNALS</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"))
    fig1.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper",
                              line=dict(color='rgba(173, 216, 230, 0.4)', dash='dash')))
    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower",
                              line=dict(color='rgba(173, 216, 230, 0.4)', dash='dash'), fill='tonexty'))

    # CHARTS ARROWS
    buys = data[data['Buy_Signal']]
    sells = data[data['Sell_Signal']]
    fig1.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.99, mode='markers',
                              marker=dict(symbol='triangle-up', size=15, color='#00FF41'), name='Buy Trigger'))
    fig1.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.01, mode='markers',
                              marker=dict(symbol='triangle-down', size=15, color='#FF3131'), name='Sell Trigger'))
    fig1.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig1, use_container_width=True)

    # WINDOW 2: VOLUME
    st.markdown('<div class="window-header">TRADING VOLUME</div>', unsafe_allow_html=True)
    v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
    fig2 = go.Figure(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors))
    fig2.update_layout(template="plotly_dark", height=180)
    st.plotly_chart(fig2, use_container_width=True)

    # WINDOW 3: RSI
    st.markdown('<div class="window-header">RELATIVE STRENGTH (RSI)</div>', unsafe_allow_html=True)
    fig3 = go.Figure(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC', width=2)))
    fig3.add_hline(y=70, line_dash="dash", line_color="#FF3131")
    fig3.add_hline(y=30, line_dash="dash", line_color="#00FF41")
    fig3.update_layout(template="plotly_dark", height=180, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig3, use_container_width=True)

    # WINDOW 4: MACD
    st.markdown('<div class="window-header">MACD MOMENTUM</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD", line=dict(color='#00E5FF')))
    fig4.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name="Signal", line=dict(color='#FFCA28')))
    h_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
    fig4.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=h_colors))
    fig4.update_layout(template="plotly_dark", height=220)
    st.plotly_chart(fig4, use_container_width=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest)
    styles.display_signal("ALGO ACTION", status, "LIVE", color)
    styles.display_signal("TREND STRENGTH", "BULLISH" if latest['Close'] > latest['MA20'] else "BEARISH", "CHECK",
                          "#BB86FC")
    st.divider()
    st.subheader("Last 5 Triggers")
    st.dataframe(data[data['Buy_Signal'] | data['Sell_Signal']][['Close', 'RSI']].tail(5))