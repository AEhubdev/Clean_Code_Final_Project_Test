import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

data, price, df_full, news_list = data_engine.get_gold_data()
w_c, m_c, y_c, vol_calc = data_engine.calculate_metrics(price, df_full)
latest = data.iloc[-1]

# --- HEADER ---
st.title("🏆 Gold Market Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Price", f"${price:,.2f}", f"{w_c:+.2f}%")
styles.colored_metric(c2, "Weekly Change", f"{w_c:+.2f}%", w_c)
styles.colored_metric(c3, "Monthly Change", f"{m_c:+.2f}%", m_c)
styles.colored_metric(c4, "YTD Change", f"{y_c:+.2f}%", y_c)
styles.colored_metric(c5, "Volatility", f"{vol_calc:.2f}%", vol_calc, is_vol=True)
st.divider()

col_charts, col_signals = st.columns([0.72, 0.28])

with col_charts:
    # WINDOW 1: TREND & SIGNALS
    st.markdown('<div class="window-header">MARKET TREND & INDICATORS HISTORY</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"))
    fig1.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="MA 20", line=dict(color='#FFEB3B', width=1.5)))
    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_U'], name="BB Upper",
                              line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash')))
    fig1.add_trace(go.Scatter(x=data.index, y=data['BB_L'], name="BB Lower",
                              line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash'), fill='tonexty',
                              fillcolor='rgba(173, 216, 230, 0.05)'))

    # --- ADDED: CHART TRIANGLES ---
    buys = data[data['Buy_Signal']]
    sells = data[data['Sell_Signal']]
    fig1.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.99, mode='markers',
                              marker=dict(symbol='triangle-up', size=15, color='#00FF41'), name='BUY'))
    fig1.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.01, mode='markers',
                              marker=dict(symbol='triangle-down', size=15, color='#FF3131'), name='SELL'))

    fig1.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig1, use_container_width=True)

    # WINDOW 2: VOLUME
    st.markdown('<div class="window-header">TRADING VOLUME HISTORY</div>', unsafe_allow_html=True)
    v_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(data['Close'], data['Open'])]
    fig2 = go.Figure(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume"))
    fig2.update_layout(template="plotly_dark", height=250, margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    # WINDOW 3: RSI
    st.markdown('<div class="window-header">RELATIVE STRENGTH (RSI) HISTORY</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", line=dict(color='#BB86FC', width=2)))
    fig3.add_hline(y=70, line_dash="dash", line_color="#FF3131")
    fig3.add_hline(y=30, line_dash="dash", line_color="#00FF41")
    fig3.update_layout(template="plotly_dark", height=250, yaxis=dict(range=[0, 100]), margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

    # WINDOW 4: MACD
    st.markdown('<div class="window-header">MACD MOMENTUM HISTORY</div>', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=data.index, y=data['MACD'], name="MACD", line=dict(color='#00E5FF', width=2)))
    fig4.add_trace(
        go.Scatter(x=data.index, y=data['MACD_Signal'], name="Signal", line=dict(color='#FFCA28', width=1.5)))
    h_colors = ['#26a69a' if val >= 0 else '#ef5350' for val in data['MACD_Hist']]
    fig4.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], name="Histogram", marker_color=h_colors))
    fig4.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

    # NEWS
    st.markdown('<div class="window-header">📰 LATEST MARKET HEADLINES</div>', unsafe_allow_html=True)
    for article in news_list:
        st.markdown(f'<a href="{article["link"]}" target="_blank" class="news-link">● {article["title"]}</a>',
                    unsafe_allow_html=True)

with col_signals:
    st.markdown('<div class="sidebar-header">📡 TRADING SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest)
    styles.display_signal("PRIMARY ACTION", status, "LIVE", color)
    styles.display_signal("RSI (14)", f"{latest['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("STOCH (%K)", f"{latest['STOCH_K']:.1f}%", "ACTIVE", "#FFA500")
    styles.display_signal("TREND STRENGTH", "BULLISH" if latest['Close'] > latest['MA20'] else "BEARISH", "LIVE",
                          "#00FF41")