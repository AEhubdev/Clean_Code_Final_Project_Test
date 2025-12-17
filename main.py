import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_trend(y):
    x = np.arange(len(y))
    n = len(x)
    m = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x ** 2) - (np.sum(x) ** 2))
    b = (np.sum(y) - m * np.sum(x)) / n
    return m * x + b


df_base, price_now, news_list = data_engine.get_gold_data("1 Day")
metrics = data_engine.calculate_metrics(price_now, df_base)

st.title("🏆 Gold Multi-Timeframe Terminal")
cols = st.columns(5)
cols[0].metric("Live Gold", f"${price_now:,.2f}")
styles.colored_metric(cols[1], "Weekly", f"{metrics[0]:+.2f}%", metrics[0])
styles.colored_metric(cols[2], "Monthly", f"{metrics[1]:+.2f}%", metrics[1])
styles.colored_metric(cols[4], "Volatility", f"{metrics[3]:.2f}%", metrics[3], is_vol=True)
st.divider()

col_charts, col_sidebar = st.columns([0.72, 0.28])


@st.fragment(run_every="15m")
def render_window(title, chart_type, key_id):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])

        # Identification Logic in Header
        if chart_type == "price":
            h_col.markdown(f"**{title}** <br> <span style='font-size:11px; color:gray;'>"
                           "<span style='color:#00d4ff'>● MA20</span> | "
                           "<span style='color:#ffea00'>● MA50</span> | "
                           "<span style='color:orange'>-- Trend</span></span>", unsafe_allow_html=True)
        else:
            h_col.markdown(f"**{title}**")

        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key=key_id,
                             label_visibility="collapsed")

        data, _, _ = data_engine.get_gold_data(tf)
        if data.empty: return st.warning("Data load error.")
        fig = go.Figure()

        if chart_type == "price":
            # Bollinger Bands
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           name="BB Upper"))
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           fill='tonexty', fillcolor='rgba(173, 216, 230, 0.05)', name="BB Lower"))

            # MA20 and MA50
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.5), name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], line=dict(color='#ffea00', width=1.5), name="MA50"))

            # Candlesticks
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))

            # Trend Line
            trend_vals = calculate_trend(data['Close'].values)
            fig.add_trace(
                go.Scatter(x=data.index, y=trend_vals, name="Trend Line",
                           line=dict(color='orange', width=2, dash='dot')))

            # Signals
            buys = data[data['Buy_Signal']];
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="Buy Signal"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="Sell Signal"))

            # SHOW LEGEND only for Price Chart
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10)
                ),
                height=400,
                xaxis_rangeslider_visible=False
            )

        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors, name="Volume"))
            fig.update_layout(height=180, showlegend=False)
        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC'), name="RSI"))
            fig.add_hline(y=70, line_color="red", line_dash="dash");
            fig.add_hline(y=30, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]), showlegend=False)
        elif chart_type == "macd":
            m_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=m_colors, name="MACD Hist"))
            fig.update_layout(height=180, showlegend=False)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)


with col_charts:
    render_window("WINDOW 1: PRICE ACTION", "price", "p1")
    render_window("WINDOW 2: VOLUME", "volume", "v1")
    render_window("WINDOW 3: RSI", "rsi", "r1")
    render_window("WINDOW 4: MACD", "macd", "m1")

with col_sidebar:
    st.markdown("### 🚦 Signal Center")
    latest = df_base.iloc[-1]

    # 1. Main Action (Your existing logic)
    status, color = trading_logic.evaluate_status(latest)
    styles.display_signal("PRIMARY ACTION", status, "LIVE", color)

    st.divider()

    # 2. RSI & MACD Metrics
    r_val = latest['RSI']
    rsi_state = "Overbought" if r_val > 70 else "Oversold" if r_val < 30 else "Neutral"
    st.markdown(f"**RSI (14):** `{r_val:.1f}` ({rsi_state})")

    m_dir = "UP" if latest['MACD_Hist'] > 0 else "DOWN"
    m_col = "green" if m_dir == "UP" else "red"
    st.markdown(f"**MACD Direction:** :{m_col}[{m_dir}]")

    # 3. Stochastic Oscillator (Ctochastik)
    sk, sd = latest['Stoch_K'], latest['Stoch_D']
    s_cross = "Bullish" if sk > sd else "Bearish"
    s_col = "green" if sk > sd else "red"
    st.markdown(f"**Stochastic (K/D):** `{sk:.0f}` / `{sd:.0f}` (:{s_col}[{s_cross}])")

    st.divider()

    # 4. Trend Strength (ADX)
    adx_val = latest['ADX']
    if adx_val > 50:
        t_str, t_col = "EXTREME", "orange"
    elif adx_val > 25:
        t_str, t_col = "STRONG", "green"
    elif adx_val > 20:
        t_str, t_col = "DEVELOPING", "yellow"
    else:
        t_str, t_col = "WEAK/RANGING", "gray"

    st.markdown(f"**Trend Strength:** :{t_col}[{t_str}]")
    st.progress(min(adx_val / 100, 1.0))
    st.caption(f"ADX Value: {adx_val:.1f} (25+ = Trending)")

    st.divider()
    st.markdown("### Market News")
    for n in news_list[:5]:
        st.markdown(f"● [{n['title']}]({n['link']})")