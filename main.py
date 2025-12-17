import streamlit as st
import plotly.graph_objects as go
import numpy as np
from scipy.stats import linregress
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

df_base, price_now, news_list = data_engine.get_gold_data("1 Day")
metrics = data_engine.calculate_metrics(price_now, df_base)

# --- HEADER ---
st.title("🏆 Gold Multi-Timeframe Terminal")
cols = st.columns(5)
cols[0].metric("Live Gold", f"${price_now:,.2f}")
styles.colored_metric(cols[1], "Weekly", f"{metrics[0]:+.2f}%", metrics[0])
styles.colored_metric(cols[2], "Monthly", f"{metrics[1]:+.2f}%", metrics[1])
styles.colored_metric(cols[3], "YTD", f"{metrics[2]:+.2f}%", metrics[2])
styles.colored_metric(cols[4], "Volatility", f"{metrics[3]:.2f}%", metrics[3], is_vol=True)
st.divider()

col_charts, col_sidebar = st.columns([0.72, 0.28])


@st.fragment(run_every="15m")
def render_window(title, chart_type, key_id):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        h_col.markdown(f"**{title}**")
        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key=key_id,
                             label_visibility="collapsed")

        data, _, _ = data_engine.get_gold_data(tf)
        if data.empty: return st.warning("Data load error.")

        fig = go.Figure()

        if chart_type == "price":
            # 1. BB AND CANDLESTICKS
            fig.add_trace(go.Scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(173, 216, 230, 0.3)', width=1),
                                     name="Upper BB"))
            fig.add_trace(go.Scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(173, 216, 230, 0.3)', width=1),
                                     fill='tonexty', fillcolor='rgba(173, 216, 230, 0.05)', name="Lower BB"))
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))

            # 2. TREND LINE (Linear Regression)
            y_vals = data['Close'].values
            x_vals = np.arange(len(y_vals))
            slope, intercept, r, p, se = linregress(x_vals, y_vals)
            trendline = slope * x_vals + intercept
            fig.add_trace(go.Scatter(x=data.index, y=trendline, name="Trend Line",
                                     line=dict(color='orange', width=2, dash='dot')))

            # 3. FILTERED SIGNALS
            buys = data[data['Buy_Signal']];
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FF41'), name="Buy"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF3131'), name="Sell"))
            fig.update_layout(height=450, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors))
            fig.update_layout(height=180)

        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))
            fig.add_hline(y=70, line_color="red", line_dash="dash");
            fig.add_hline(y=30, line_color="green", line_dash="dash")

        elif chart_type == "macd":
            m_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=m_colors))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


with col_charts:
    render_window("WINDOW 1: PRICE ACTION & BB", "price", "tf_p")
    render_window("WINDOW 2: VOLUME", "volume", "tf_v")
    render_window("WINDOW 3: RSI", "rsi", "tf_r")
    render_window("WINDOW 4: MACD", "macd", "tf_m")

with col_sidebar:
    st.markdown('<div class="sidebar-header">📡 SIGNALS</div>', unsafe_allow_html=True)
    status, color = trading_logic.evaluate_status(df_base.iloc[-1])
    styles.display_signal("ACTION", status, "LIVE", color)
    st.markdown('<div class="window-header">📰 NEWS</div>', unsafe_allow_html=True)
    for n in news_list[:6]:
        st.markdown(f'<a href="{n["link"]}" target="_blank" class="news-link">● {n["title"]}</a>',
                    unsafe_allow_html=True)