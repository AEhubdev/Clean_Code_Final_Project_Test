import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# 1. BASE DATA FOR HEADER
df_base, price_now, news_list = data_engine.get_gold_data("1 Day")
w_c, m_c, y_c, vol = data_engine.calculate_metrics(price_now, df_base)
latest_base = df_base.iloc[-1]

# --- HEADER ---
st.title("🏆 Gold Multi-Timeframe Terminal")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Live Gold", f"${price_now:,.2f}", f"{w_c:+.2f}%")
styles.colored_metric(c2, "Weekly", f"{w_c:+.2f}%", w_c)
styles.colored_metric(c3, "Monthly", f"{m_c:+.2f}%", m_c)
styles.colored_metric(c4, "YTD", f"{y_c:+.2f}%", y_c)
styles.colored_metric(c5, "Volatility", f"{vol:.2f}%", vol, is_vol=True)
st.divider()

col_charts, col_sidebar = st.columns([0.72, 0.28])


# --- CHART FRAGMENTS ---

@st.fragment(run_every="15m")
def render_window(title, chart_type, key_id):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        h_col.markdown(f"**{title}**")
        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key=key_id,
                             label_visibility="collapsed")

        data, current_p, _ = data_engine.get_gold_data(tf)
        if data.empty: return st.warning("Data load error.")

        fig = go.Figure()
        if chart_type == "price":
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))
            buys = data[data['Buy_Signal']];
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FF41'), name="Buy"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF3131'), name="Sell"))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors))
            fig.update_layout(height=180)

        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.add_hline(y=70, line_dash="dash", line_color="red");
            fig.add_hline(y=30, line_dash="dash", line_color="green")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))

        elif chart_type == "macd":
            m_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=m_colors))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)


with col_charts:
    render_window("WINDOW 1: LIVE PRICE ACTION", "price", "tf_1")
    render_window("WINDOW 2: TRADING VOLUME", "volume", "tf_2")
    render_window("WINDOW 3: RSI MOMENTUM", "rsi", "tf_3")
    render_window("WINDOW 4: MACD TREND", "macd", "tf_4")

with col_sidebar:
    st.markdown('<div class="sidebar-header">📡 SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(latest_base)
    styles.display_signal("PRIMARY ACTION", status, "LIVE", color)
    styles.display_signal("RSI (1D)", f"{latest_base['RSI']:.1f}", "ACTIVE", "#BB86FC")

    st.markdown('<div class="window-header">📰 NEWS</div>', unsafe_allow_html=True)
    for n in news_list[:6]:
        st.markdown(f'<a href="{n["link"]}" target="_blank" class="news-link">● {n["title"]}</a>',
                    unsafe_allow_html=True)