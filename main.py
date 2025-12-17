import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

# 1. PAGE SETUP
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_least_squares_trend(prices):
    """Calculates a linear trend line using the least squares method."""
    x_axis = np.arange(len(prices))
    n_points = len(x_axis)
    sum_x, sum_y = np.sum(x_axis), np.sum(prices)
    sum_xy, sum_xx = np.sum(x_axis * prices), np.sum(x_axis ** 2)
    denominator = (n_points * sum_xx - sum_x ** 2)
    if denominator == 0: return prices
    slope = (n_points * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n_points
    return slope * x_axis + intercept


# 2. CHART FRAGMENT (Handles individual window updates)
@st.fragment
def render_chart_window(title, chart_type, unique_key):
    """Renders modular chart containers with independent timeframe control."""
    with st.container(border=True):
        header_col, selector_col = st.columns([0.7, 0.3])

        # 1. Implementation of Default Interval Logic
        timeframe_options = list(config.TIMEFRAME_OPTIONS.keys())
        try:
            # Dynamically find where "1 Month" is in the list
            default_idx = timeframe_options.index(config.DEFAULT_INTERVAL_LABEL)
        except ValueError:
            default_idx = 0

        timeframe = selector_col.selectbox(
            "TF",
            timeframe_options,
            index=default_idx,  # Starts at "1 Month" automatically
            key=unique_key,
            label_visibility="collapsed"
        )
        # 2. Fetch the data LOCALLY within the fragment
        # This ensures 'data' is defined every time the fragment reruns
        try:
            data, _, _, _ = data_engine.get_gold_terminal_data(timeframe)
        except Exception as e:
            st.error(f"Connection Error: {e}")
            return

        # 3. Now check if data is empty
        if data is None or data.empty:
            st.warning("No data available for this timeframe.")
            return


        fig = go.Figure()
        if chart_type == "price":
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_Upper'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           name="BB Up"))
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_Lower'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           fill='tonexty', name="BB Low"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.5), name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], line=dict(color='#ffea00', width=1.5), name="MA50"))
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))
            trend_line = calculate_least_squares_trend(data['Close'].values)
            fig.add_trace(
                go.Scatter(x=data.index, y=trend_line, name="Trend", line=dict(color='orange', width=2, dash='dot')))
            buys, sells = data[data['Buy_Signal']], data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="Buy"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="Sell"))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)
        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=v_colors))
            fig.update_layout(height=180)
        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.add_hline(y=config.RSI_OVERBOUGHT, line_color="red", line_dash="dash")
            fig.add_hline(y=config.RSI_OVERSOLD, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))
        elif chart_type == "macd":
            m_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=m_colors))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)


# 3. MAIN LIVE FRAGMENT (The "Heartbeat" of the app)
@st.fragment(run_every="1m")  # Updates everything every 60 seconds
def main_terminal_hub():
    """The central hub that refreshes prices, signals, and news automatically."""

    # Refresh data from engine
    df_base, price_now, news_list, ytd_start_price = data_engine.get_gold_terminal_data("1 Day")
    metrics = data_engine.calculate_market_metrics(price_now, df_base, ytd_start_price)

    # Header Metrics (Now Live!)
    st.title("🏆 Gold Multi-Timeframe Terminal")
    cols = st.columns(5)
    cols[0].metric("Live Gold", f"${price_now:,.2f}")
    styles.colored_metric(cols[1], "Weekly", f"{metrics['weekly']:+.2f}%", metrics['weekly'])
    styles.colored_metric(cols[2], "Monthly", f"{metrics['monthly']:+.2f}%", metrics['monthly'])
    styles.colored_metric(cols[3], "YTD", f"{metrics['ytd']:+.2f}%", metrics['ytd'])
    styles.colored_metric(cols[4], "Volatility", f"{metrics['volatility']:.2f}%", metrics['volatility'],
                          is_volatility=True)

    st.divider()

    col_charts, col_sidebar = st.columns([0.72, 0.28])

    with col_charts:
        render_chart_window("PRICE ACTION", "price", "p1")
        render_chart_window("VOLUME", "volume", "v1")
        render_chart_window("RSI", "rsi", "r1")
        render_chart_window("MACD", "macd", "m1")

    with col_sidebar:
        st.markdown("### 🚦 Signal Center")
        latest_bar = df_base.iloc[-1]
        status, status_color = trading_logic.evaluate_market_status(latest_bar)
        styles.display_signal("PRIMARY ACTION", status, "LIVE", status_color)

        st.markdown("---")
        c1, c2 = st.columns(2)
        r_val = latest_bar['RSI']
        r_color = "red" if r_val > config.RSI_OVERBOUGHT else "green" if r_val < config.RSI_OVERSOLD else "#00d4ff"
        c1.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {r_color}"><small style="color:gray">RSI (14)</small><br><strong style="font-size:18px">{r_val:.1f}</strong></div>',
            unsafe_allow_html=True)

        m_hist = latest_bar['MACD_Hist']
        m_dir = "UP" if m_hist > 0 else "DOWN"
        m_color = "#00FF41" if m_dir == "UP" else "#FF3131"
        c2.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {m_color}"><small style="color:gray">MACD</small><br><strong style="font-size:18px; color:{m_color}">{m_dir}</strong></div>',
            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sk, sd = latest_bar['Stoch_K'], latest_bar['Stoch_D']
        s_col = "#00FF41" if sk > sd else "#FF3131"
        st.markdown(
            f'<div style="background:#1e2130; padding:12px; border-radius:5px;"><div style="display:flex; justify-content:space-between"><span style="color:gray">Stoch (K/D)</span><span style="color:{s_col}; font-weight:bold">{"Bullish" if sk > sd else "Bearish"}</span></div><div style="font-size:20px; font-weight:bold">{sk:.0f} / {sd:.0f}</div></div>',
            unsafe_allow_html=True)

        st.divider()
        st.markdown("### Market News")
        for news in news_list[:5]:
            st.markdown(f"● [{news['title']}]({news['link']})")


# 4. START THE TERMINAL
if __name__ == "__main__":
    main_terminal_hub()