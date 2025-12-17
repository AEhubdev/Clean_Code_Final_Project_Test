import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# 1. LOAD DATA & SETTINGS
choice = st.sidebar.selectbox("Timeframe", list(config.TIMEFRAME_OPTIONS.keys()), index=2)
df, price, news_list = data_engine.get_gold_data(config.TIMEFRAME_OPTIONS[choice])
w_c, m_c, y_c, vol = data_engine.calculate_metrics(price, df)
latest = df.iloc[-1]

# 2. HEADER METRICS
st.title(f"🏆 Gold Market Terminal ({choice})")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Live Price", f"${price:,.2f}", f"{w_c:+.2f}%")
styles.colored_metric(c2, "Weekly", f"{w_c:+.2f}%", w_c)
styles.colored_metric(c3, "Monthly", f"{m_c:+.2f}%", m_c)
styles.colored_metric(c4, "YTD", f"{y_c:+.2f}%", y_c)
styles.colored_metric(c5, "Volatility", f"{vol:.2f}%", vol, is_vol=True)
st.divider()


# 3. FRAGMENTED LIVE CHART
@st.fragment(run_every="15m")
def live_trend_chart(data):
    st.markdown('<div class="window-header">WINDOW 1: LIVE TREND & SIGNALS</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_U'], name="Upper BB", line=dict(color='gray', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['BB_L'], name="Lower BB", line=dict(color='gray', dash='dash')))

    buys = data[data['Buy_Signal']];
    sells = data[data['Sell_Signal']]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.99, mode='markers',
                             marker=dict(symbol='triangle-up', size=15, color='#00FF41')))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.01, mode='markers',
                             marker=dict(symbol='triangle-down', size=15, color='#FF3131')))

    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


# 4. MAIN LAYOUT
col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    live_trend_chart(df)  # The only live part

    # WINDOW 2: VOLUME
    st.markdown('<div class="window-header">WINDOW 2: TRADING VOLUME</div>', unsafe_allow_html=True)
    fig_v = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color='#26a69a'))
    fig_v.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(fig_v, use_container_width=True)

    # WINDOW 3: RSI
    st.markdown('<div class="window-header">WINDOW 3: RSI MOMENTUM</div>', unsafe_allow_html=True)
    fig_rsi = go.Figure(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#BB86FC')))
    fig_rsi.add_hline(y=70, line_color="red");
    fig_rsi.add_hline(y=30, line_color="green")
    fig_rsi.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(fig_rsi, use_container_width=True)

    # WINDOW 4: MACD
    st.markdown('<div class="window-header">WINDOW 4: MACD HISTOGRAM</div>', unsafe_allow_html=True)
    h_colors = ['#00FF41' if v > 0 else '#FF3131' for v in df['MACD_Hist']]
    fig_macd = go.Figure(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=h_colors))
    fig_macd.update_layout(template="plotly_dark", height=200, margin=dict(t=0, b=0))
    st.plotly_chart(fig_macd, use_container_width=True)

with col_right:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest)
    styles.display_signal("ALGO ACTION", status, "LIVE", color)
    styles.display_signal("RSI STRENGTH", f"{latest['RSI']:.1f}", "ACTIVE", "#BB86FC")

    st.markdown('<div class="window-header">MARKET NEWS</div>', unsafe_allow_html=True)
    for n in news_list[:6]:
        st.markdown(f'<a href="{n["link"]}" class="news-link">● {n["title"]}</a>', unsafe_allow_html=True)