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


@st.fragment(run_every="1m")
def render_live_overview():
    # Fresh data for live metrics
    df_base, price_now, news_list, ytd_start_price = data_engine.get_gold_data("1 Day")
    metrics = data_engine.calculate_metrics(price_now, df_base, ytd_start_price)

    st.title("🏆 Gold Multi-Timeframe Terminal")
    cols = st.columns(5)
    cols[0].metric("Live Gold", f"${price_now:,.2f}")
    styles.colored_metric(cols[1], "Weekly", f"{metrics[0]:+.2f}%", metrics[0])
    styles.colored_metric(cols[2], "Monthly", f"{metrics[1]:+.2f}%", metrics[1])
    styles.colored_metric(cols[3], "YTD", f"{metrics[2]:+.2f}%", metrics[2])
    styles.colored_metric(cols[4], "Volatility", f"{metrics[3]:.2f}%", metrics[3], is_vol=True)
    st.divider()

    col_charts, col_sidebar = st.columns([0.72, 0.28])

    with col_charts:
        # Default index 4 is "1 Month"
        render_window("PRICE ACTION", "price", "p1", default_idx=4)
        render_window("VOLUME", "volume", "v1", default_idx=4)
        render_window("RSI", "rsi", "r1", default_idx=4)
        render_window("MACD", "macd", "m1", default_idx=4)

    with col_sidebar:
        st.markdown("### 🚦 Signal Center")
        latest = df_base.iloc[-1]
        status, color = trading_logic.evaluate_status(latest)

        # Now renders as a box because of the fix in styles.py
        styles.display_signal("PRIMARY ACTION", status, "LIVE", color)

        st.markdown("---")
        # Sub-metrics RSI/MACD/Stoch
        c1, c2 = st.columns(2)
        r_val = latest['RSI']
        r_color = "red" if r_val > 70 else "green" if r_val < 30 else "#00d4ff"
        c1.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {r_color}"><small style="color:gray">RSI (14)</small><br><strong style="font-size:18px">{r_val:.1f}</strong></div>',
            unsafe_allow_html=True)

        m_dir = "UP" if latest['MACD_Hist'] > 0 else "DOWN"
        m_color = "green" if m_dir == "UP" else "red"
        c2.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {m_color}"><small style="color:gray">MACD</small><br><strong style="font-size:18px; color:{m_color}">{m_dir}</strong></div>',
            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sk, sd = latest['Stoch_K'], latest['Stoch_D']
        s_col = "green" if sk > sd else "red"
        st.markdown(
            f'<div style="background:#1e2130; padding:12px; border-radius:5px;"><div style="display:flex; justify-content:space-between"><span style="color:gray">Stoch (K/D)</span><span style="color:{s_col}; font-weight:bold">{"Bullish" if sk > sd else "Bearish"}</span></div><div style="font-size:20px; font-weight:bold">{sk:.0f} / {sd:.0f}</div></div>',
            unsafe_allow_html=True)

        st.divider()
        st.markdown("### Market News")
        for n in news_list[:5]:
            st.markdown(f"● [{n['title']}]({n['link']})")


def render_window(title, chart_type, key_id, default_idx=2):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        h_col.markdown(f"**{title}**")
        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=default_idx, key=key_id,
                             label_visibility="collapsed")

        data, _, _, _ = data_engine.get_gold_data(tf)
        if data.empty: return st.warning("Data load error.")

        fig = go.Figure()
        # ... [Plotly trace logic same as your provided code] ...
        # (Assuming your candlestick and indicator traces are here)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


render_live_overview()