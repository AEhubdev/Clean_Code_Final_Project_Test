import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

# 1. SETUP & STYLES (Rule S2.43: Imports and config on top)
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_least_squares_trend(prices):
    """Calculates a linear trend line using the least squares method."""
    x_axis = np.arange(len(prices))
    n_points = len(x_axis)

    # Formula components for m (slope) and b (intercept)
    sum_x = np.sum(x_axis)
    sum_y = np.sum(prices)
    sum_xy = np.sum(x_axis * prices)
    sum_xx = np.sum(x_axis ** 2)

    slope = (n_points * sum_xy - sum_x * sum_y) / (n_points * sum_xx - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n_points

    return slope * x_axis + intercept


# 2. DATA ORCHESTRATION (Rule C4: Human-readable flow)
df_base, price_now, news_list, ytd_start_price = data_engine.get_gold_terminal_data("1 Day")
metrics = data_engine.calculate_market_metrics(price_now, df_base, ytd_start_price)

# 3. HEADER METRICS
st.title("🏆 Gold Multi-Timeframe Terminal")
cols = st.columns(5)
cols[0].metric("Live Gold", f"${price_now:,.2f}")

# Using Dictionary Keys (Rule C1: Precise Names) instead of index numbers
styles.colored_metric(cols[1], "Weekly", f"{metrics['weekly']:+.2f}%", metrics['weekly'])
styles.colored_metric(cols[2], "Monthly", f"{metrics['monthly']:+.2f}%", metrics['monthly'])
styles.colored_metric(cols[3], "YTD", f"{metrics['ytd']:+.2f}%", metrics['ytd'])
styles.colored_metric(cols[4], "Volatility", f"{metrics['volatility']:.2f}%", metrics['volatility'], is_volatility=True)

st.divider()

# 4. LAYOUT DIVISION
col_charts, col_sidebar = st.columns([0.72, 0.28])


@st.fragment(run_every="15m")
def render_chart_window(title, chart_type, unique_key):
    """Renders modular chart containers for different technical indicators."""
    with st.container(border=True):
        header_col, selector_col = st.columns([0.7, 0.3])

        # Header display logic
        if chart_type == "price":
            header_col.markdown(f"**{title}** <br> <span style='font-size:11px; color:gray;'>"
                                "<span style='color:#00d4ff'>● MA20</span> | "
                                "<span style='color:#ffea00'>● MA50</span> | "
                                "<span style='color:orange'>-- Trend</span></span>", unsafe_allow_html=True)
        else:
            header_col.markdown(f"**{title}**")

        timeframe = selector_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()),
                                           index=2, key=unique_key, label_visibility="collapsed")

        # Fetch data for specific timeframe
        data, _, _, _ = data_engine.get_gold_terminal_data(timeframe)
        if data.empty:
            return st.warning("Data load error.")

        fig = go.Figure()

        # Chart Logic Switch (Rule C2.17: Avoiding Convoluted Logic)
        if chart_type == "price":
            # Bollinger Bands & MAs
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_Upper'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           name="BB Up"))
            fig.add_trace(
                go.Scatter(x=data.index, y=data['BB_Lower'], line=dict(color='rgba(173, 216, 230, 0.15)', width=1),
                           fill='tonexty', name="BB Low"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.5), name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], line=dict(color='#ffea00', width=1.5), name="MA50"))

            # Main Candlesticks
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))

            # Trend Line
            trend_line = calculate_least_squares_trend(data['Close'].values)
            fig.add_trace(
                go.Scatter(x=data.index, y=trend_line, name="Trend", line=dict(color='orange', width=2, dash='dot')))

            # Signals (Using Refactored Names)
            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00FF41'), name="Buy"))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#FF3131'), name="Sell"))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)

        elif chart_type == "rsi":
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC')))
            fig.add_hline(y=config.RSI_OVERBOUGHT, line_color="red", line_dash="dash")
            fig.add_hline(y=config.RSI_OVERSOLD, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))

        elif chart_type == "macd":
            macd_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=macd_colors))
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig, use_container_width=True)


with col_charts:
    render_chart_window("PRICE ACTION", "price", "p1")
    render_chart_window("RSI", "rsi", "r1")
    render_chart_window("MACD", "macd", "m1")

# 5. SIDEBAR SIGNALS (Rule C2.22: Natural Conditions)
with col_sidebar:
    st.markdown("### 🚦 Signal Center")
    latest_bar = df_base.iloc[-1]

    # Evaluate Status (Clean Logic)
    status, status_color = trading_logic.evaluate_market_status(latest_bar)
    styles.display_signal("PRIMARY ACTION", status, "LIVE", status_color)

    st.markdown("---")

    # Technical Gauges
    c1, c2 = st.columns(2)
    current_rsi = latest_bar['RSI']
    rsi_display_color = "red" if current_rsi > config.RSI_OVERBOUGHT else "green" if current_rsi < config.RSI_OVERSOLD else "#00d4ff"

    c1.markdown(f"""
        <div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {rsi_display_color}">
            <small style="color:gray">RSI (14)</small><br>
            <strong style="font-size:18px">{current_rsi:.1f}</strong>
        </div>
    """, unsafe_allow_html=True)

    # Stochastic Display
    stoch_k, stoch_d = latest_bar['Stoch_K'], latest_bar['Stoch_D']
    is_bullish_stoch = stoch_k > stoch_d
    stoch_color = "green" if is_bullish_stoch else "red"

    st.markdown(f"""
        <div style="background:#1e2130; padding:12px; border-radius:5px; margin-top:10px;">
            <div style="display:flex; justify-content:space-between">
                <span style="color:gray">Stoch (K/D)</span>
                <span style="color:{stoch_color}; font-weight:bold">
                    {"Bullish" if is_bullish_stoch else "Bearish"}
                </span>
            </div>
            <div style="font-size:20px; font-weight:bold">{stoch_k:.0f} / {stoch_d:.0f}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Market News")
    for news_item in news_list[:5]:
        st.markdown(f"● [{news_item['title']}]({news_item['link']})")