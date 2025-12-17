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


# --- LIVE OVERVIEW FRAGMENT ---
# This updates the top metrics and sidebar signals every 1 minute
@st.fragment(run_every="1m")
def render_live_overview():
    # Fetch fresh 1-day data for the header metrics
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
        # We pass the index for "1 Month" (index 4 in your config) as default
        render_window("PRICE ACTION", "price", "p1", default_idx=4)
        render_window("VOLUME", "volume", "v1", default_idx=4)
        render_window("RSI", "rsi", "r1", default_idx=4)
        render_window("MACD", "macd", "m1", default_idx=4)

    with col_sidebar:
        st.markdown("### 🚦 Signal Center")

        # Use the 1-day data for the primary signal logic
        latest = df_base.iloc[-1]
        status, color = trading_logic.evaluate_status(latest)

        # This function handles the HTML rendering itself
        styles.display_signal("PRIMARY ACTION", status, "LIVE", color)

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


# --- CHART WINDOW FUNCTION ---
def render_window(title, chart_type, key_id, default_idx=2):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        if chart_type == "price":
            h_col.markdown(f"**{title}** <br> <span style='font-size:11px; color:gray;'>"
                           "<span style='color:#00d4ff'>● MA20</span> | "
                           "<span style='color:#ffea00'>● MA50</span> | "
                           "<span style='color:orange'>-- Trend</span></span>", unsafe_allow_html=True)
        else:
            h_col.markdown(f"**{title}**")

        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=default_idx, key=key_id,
                             label_visibility="collapsed")
        data, _, _, _ = data_engine.get_gold_data(tf)
        if data.empty: return st.warning("Data load error.")

        fig = go.Figure()
        if chart_type == "price":
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           name="BB Upper"))
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           fill='tonexty', fillcolor='rgba(173, 216, 230, 0.05)', name="BB Lower"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.5), name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], line=dict(color='#ffea00', width=1.5), name="MA50"))
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))
            trend_vals = calculate_trend(data['Close'].values)
            fig.add_trace(go.Scatter(x=data.index, y=trend_vals, name="Trend Line",
                                     line=dict(color='orange', width=2, dash='dot')))

            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="Buy Signal"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="Sell Signal"))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors))
            fig.update_layout(height=180)
        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.add_hline(y=70, line_color="red", line_dash="dash")
            fig.add_hline(y=30, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))
        elif chart_type == "macd":
            m_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=m_colors))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# Start the live overview
render_live_overview()