import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

# 1. SETUP & STYLES
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_least_squares_trend(prices):
    """Calculates a linear trend line using the least squares method."""
    x_axis = np.arange(len(prices))
    n_points = len(x_axis)

    sum_x = np.sum(x_axis)
    sum_y = np.sum(prices)
    sum_xy = np.sum(x_axis * prices)
    sum_xx = np.sum(x_axis ** 2)

    slope = (n_points * sum_xy - sum_x * sum_y) / (n_points * sum_xx - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n_points

    return slope * x_axis + intercept


# 2. DATA ORCHESTRATION
df_base, price_now, news_list, ytd_start_price = data_engine.get_gold_terminal_data("1 Day")
metrics = data_engine.calculate_market_metrics(price_now, df_base, ytd_start_price)

# 3. HEADER METRICS
st.title("🏆 Gold Multi-Timeframe Terminal")
cols = st.columns(5)
cols[0].metric("Live Gold", f"${price_now:,.2f}")
styles.colored_metric(cols[1], "Weekly", f"{metrics['weekly']:+.2f}%", metrics['weekly'])
styles.colored_metric(cols[2], "Monthly", f"{metrics['monthly']:+.2f}%", metrics['monthly'])
styles.colored_metric(cols[3], "YTD", f"{metrics['ytd']:+.2f}%", metrics['ytd'])
styles.colored_metric(cols[4], "Volatility", f"{metrics['volatility']:.2f}%", metrics['volatility'], is_volatility=True)

st.divider()

col_charts, col_sidebar = st.columns([0.72, 0.28])


@st.fragment(run_every="15m")
def render_chart_window(title, chart_type, unique_key):
    """Renders modular chart containers including Price, Volume, RSI, and MACD."""
    with st.container(border=True):
        header_col, selector_col = st.columns([0.7, 0.3])

        if chart_type == "price":
            header_col.markdown(f"**{title}** <br> <span style='font-size:11px; color:gray;'>"
                                "<span style='color:#00d4ff'>● MA20</span> | "
                                "<span style='color:#ffea00'>● MA50</span> | "
                                "<span style='color:orange'>-- Trend</span></span>", unsafe_allow_html=True)
        else:
            header_col.markdown(f"**{title}**")

        # In main.py
        timeframe = selector_col.selectbox(
            "TF",
            list(config.TIMEFRAME_OPTIONS.keys()),  # This pulls the new list from config.py
            index=2,
            key=unique_key,
            label_visibility="collapsed"
        )

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

            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="Buy"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="Sell"))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            # Bar colors based on price movement
            vol_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], marker_color=vol_colors, name="Volume"))
            fig.update_layout(height=180)

        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.add_hline(y=config.RSI_OVERBOUGHT, line_color="red", line_dash="dash")
            fig.add_hline(y=config.RSI_OVERSOLD, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))

        elif chart_type == "macd":
            macd_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=macd_colors, name="MACD Hist"))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)


# 4. CHART RENDERING
with col_charts:
    render_chart_window("PRICE ACTION", "price", "p1")
    render_chart_window("VOLUME", "volume", "v1")
    render_chart_window("RSI", "rsi", "r1")
    render_chart_window("MACD", "macd", "m1")

# 5. SIDEBAR SIGNALS
with col_sidebar:
    st.markdown("### 🚦 Signal Center")
    latest_bar = df_base.iloc[-1]

    # Evaluate Status
    status, status_color = trading_logic.evaluate_market_status(latest_bar)
    styles.display_signal("PRIMARY ACTION", status, "LIVE", status_color)

    st.markdown("---")

    # Technical Gauges
    c1, c2 = st.columns(2)

    # RSI Gauge
    current_rsi = latest_bar['RSI']
    rsi_color = "red" if current_rsi > config.RSI_OVERBOUGHT else "green" if current_rsi < config.RSI_OVERSOLD else "#00d4ff"
    c1.markdown(f"""
        <div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {rsi_color}">
            <small style="color:gray">RSI (14)</small><br>
            <strong style="font-size:18px">{current_rsi:.1f}</strong>
        </div>
    """, unsafe_allow_html=True)

    # MACD Gauge
    macd_hist = latest_bar['MACD_Hist']
    macd_trend = "UP" if macd_hist > 0 else "DOWN"
    macd_color = "#00FF41" if macd_trend == "UP" else "#FF3131"
    c2.markdown(f"""
        <div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {macd_color}">
            <small style="color:gray">MACD</small><br>
            <strong style="font-size:18px; color:{macd_color}">{macd_trend}</strong>
        </div>
    """, unsafe_allow_html=True)

    # Stochastic Gauge
    stoch_k, stoch_d = latest_bar['Stoch_K'], latest_bar['Stoch_D']
    is_bullish = stoch_k > stoch_d
    stoch_color = "#00FF41" if is_bullish else "#FF3131"

    st.markdown(f"""
        <div style="background:#1e2130; padding:12px; border-radius:5px; margin-top:10px;">
            <div style="display:flex; justify-content:space-between">
                <span style="color:gray">Stoch (K/D)</span>
                <span style="color:{stoch_color}; font-weight:bold">
                    {"Bullish" if is_bullish else "Bearish"}
                </span>
            </div>
            <div style="font-size:20px; font-weight:bold">{stoch_k:.0f} / {stoch_d:.0f}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Market News")
    for news_item in news_list[:5]:
        st.markdown(f"● [{news_item['title']}]({news_item['link']})")