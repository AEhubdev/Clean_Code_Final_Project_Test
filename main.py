import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles

st.set_page_config(page_title="Gold Terminal", layout="wide")
styles.apply_custom_styles()

data, price, df_full, news_list = data_engine.get_gold_data()
w_c, m_c, vol = data_engine.calculate_metrics(price, df_full)
latest = data.iloc[-1]

# HEADER
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
styles.metric_row(c1, c2, c3, price, w_c, m_c)
c4.subheader(f"Volatility Index: {vol:.2f}%")

st.divider()

col_left, col_right = st.columns([0.7, 0.3])

with col_left:
    # --- CHART 1: PRICE & SIGNALS ---
    st.markdown('<div class="window-header">Trend Analysis & Buy/Sell Signals</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(
        go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                       name="Gold"))

    # ADDING BUY/SELL INDICATORS
    buys = data[data['Buy_Signal']]
    sells = data[data['Sell_Signal']]
    fig1.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.997, mode='markers',
                              marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name='Buy Trigger'))
    fig1.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.003, mode='markers',
                              marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name='Sell Trigger'))

    fig1.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(t=0, b=0))
    st.plotly_chart(fig1, use_container_width=True)

    # --- CHART 2: RSI ---
    st.markdown('<div class="window-header">RSI Momentum</div>', unsafe_allow_html=True)
    fig2 = go.Figure(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
    fig2.add_hline(y=70, line_dash="dash", line_color="red")
    fig2.add_hline(y=30, line_dash="dash", line_color="green")
    fig2.update_layout(template="plotly_dark", height=150, margin=dict(t=0, b=0))
    st.plotly_chart(fig2, use_container_width=True)

    # --- NEWS ---
    st.markdown('<div class="window-header">Market News Feed</div>', unsafe_allow_html=True)
    for n in news_list[:5]:
        st.markdown(f"**[{n['title']}]({n['link']})**")

with col_right:
    st.markdown('<div class="sidebar-header">SIGNAL CENTER</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest)
    st.markdown(f"""<div class="signal-card">
        <small>ALGO STATUS</small><br>
        <b style="color:{color}; font-size:20px;">{status}</b>
    </div>""", unsafe_allow_html=True)

    st.write("Recent Activity")
    st.dataframe(data[data['Buy_Signal'] | data['Sell_Signal']].tail(8)[['Close', 'RSI']])