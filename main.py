import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_trend_line(closing_prices):
    """Calculates a linear regression line for the provided price data."""
    indices = np.arange(len(closing_prices))
    slope, intercept = np.polyfit(indices, closing_prices, 1)
    return slope * indices + intercept


@st.fragment(run_every="1m")
def render_live_overview():
    # 1. Fetch Processed Data
    gold_df, price_now, news_list, ytd_price = data_engine.get_gold_market_data("1 Day")
    perf_metrics = data_engine.calculate_performance_metrics(price_now, gold_df, ytd_price)

    # 2. Daily Delta Calculation
    yesterday_close = gold_df['Close'].iloc[-2]
    day_percentage_change = ((price_now - yesterday_close) / yesterday_close) * 100

    st.title("🏆 Gold Multi-Timeframe Terminal")

    # 3. Horizontal Metrics Bar
    metric_cols = st.columns(5)
    metric_cols[0].metric(label="Live Gold", value=f"${price_now:,.2f}", delta=f"{day_percentage_change:+.2f}%")

    styles.colored_metric(metric_cols[1], "Weekly", f"{perf_metrics[0]:+.2f}%", perf_metrics[0])
    styles.colored_metric(metric_cols[2], "Monthly", f"{perf_metrics[1]:+.2f}%", perf_metrics[1])
    styles.colored_metric(metric_cols[3], "YTD", f"{perf_metrics[2]:+.2f}%", perf_metrics[2])
    styles.colored_metric(metric_cols[4], "Volatility", f"{perf_metrics[3]:.2f}%", perf_metrics[3], is_vol=True)

    st.divider()

    # 4. Main Grid Layout
    left_pane, right_pane = st.columns([0.72, 0.28])

    with left_pane:
        render_chart_window("PRICE ACTION & AI FORECAST", "price", "p1_daily", default_idx=2)
        render_chart_window("VOLUME", "volume", "v1_vol", default_idx=2)
        render_chart_window("RSI", "rsi", "r1_rsi", default_idx=2)
        render_chart_window("MACD", "macd", "m1_macd", default_idx=2)

    with right_pane:
        _render_sidebar_signals(gold_df)

    # 5. Full-Width News Section
    _render_news_section(news_list)


def _render_sidebar_signals(dataframe):
    st.markdown("### 🚦 Signal Center")
    latest_bar = dataframe.iloc[-1]

    signal_text, signal_color = trading_logic.evaluate_status(latest_bar)
    styles.display_signal("PRIMARY ACTION", signal_text, "LIVE", signal_color)

    st.markdown("---")
    # Quick-View Indicators
    rsi_val = latest_bar['RSI']
    rsi_indicator_color = "red" if rsi_val > config.RSI_OVERBOUGHT else "green" if rsi_val < 45 else "#00d4ff"

    c1, c2 = st.columns(2)
    c1.markdown(_get_indicator_html("RSI (14)", f"{rsi_val:.1f}", rsi_indicator_color), unsafe_allow_html=True)

    macd_val = latest_bar['MACD_Hist']
    macd_dir, macd_col = ("UP", "green") if macd_val > 0 else ("DOWN", "red")
    c2.markdown(_get_indicator_html("MACD Hist", macd_dir, macd_col), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    stoch_text = f"{latest_bar['Stoch_K']:.0f} / {latest_bar['Stoch_D']:.0f}"
    stoch_col = "green" if latest_bar['Stoch_K'] > latest_bar['Stoch_D'] else "red"
    st.markdown(_get_indicator_html("Stochastic (K/D)", stoch_text, stoch_col), unsafe_allow_html=True)


def _get_indicator_html(label, value, color):
    """Helper to maintain clean code and unique strings (S1)."""
    return f'''
        <div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {color}">
            <small>{label}</small><br><strong>{value}</strong>
        </div>'''


def render_chart_window(title, chart_type, key_id, default_idx=2):
    with st.container(border=True):
        header_col, select_col = st.columns([0.7, 0.3])
        header_col.markdown(f"**{title}**")
        selected_tf = select_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()),
                                           index=default_idx, key=f"select_{key_id}", label_visibility="collapsed")

        # Fetch data for this specific window's timeframe
        df_for_chart, _, _, _ = data_engine.get_gold_market_data(selected_tf)
        plot_data = df_for_chart.tail(150)

        if plot_data.empty:
            return st.warning("Connecting to data stream...")

        fig = go.Figure()

        # Determine if this specific chart should show a legend
        show_chart_legend = True if chart_type == "price" else False

        if chart_type == "price":
            _plot_price_with_signals(fig, plot_data)
        elif chart_type == "volume":
            _plot_volume(fig, plot_data)
        elif chart_type == "rsi":
            _plot_rsi(fig, plot_data)
        elif chart_type == "macd":
            _plot_macd(fig, plot_data)

        fig.update_layout(
            template="plotly_dark",
            margin=dict(t=30 if show_chart_legend else 5, b=5, l=5, r=5),
            showlegend=show_chart_legend
        )
        st.plotly_chart(fig, use_container_width=True)


def _plot_price_with_signals(fig, data):
    # --- 0. AI PREDICTION ALGORITHM (RSI/MACD/BB BASED) ---
    predict_df = data_engine.generate_ai_prediction(data)
    fig.add_scatter(x=predict_df.index, y=predict_df['Predicted'],
                    line=dict(color='#FFD700', width=3, dash='dashdot'),
                    name="AI Next-Month Forecast")

    # 1. Trend Line
    trend_vals = calculate_trend_line(data['Close'].values)
    fig.add_scatter(x=data.index, y=trend_vals, line=dict(color='orange', width=2, dash='dot'), name="Trend Line")

    # 2. Moving Averages
    fig.add_scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.2), name="MA 20")
    fig.add_scatter(x=data.index, y=data['MA50'], line=dict(color='cyan', width=1.2, dash='dash'), name="MA 50")

    # 3. Bollinger Bands
    fig.add_scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(255,255,255,0.15)', width=1), name="BB Upper")
    fig.add_scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(255,255,255,0.15)', width=1),
                    fill='tonexty', fillcolor='rgba(255,255,255,0.05)', name="BB Lower")

    # 4. Candlesticks
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'],
                                 close=data['Close'], name="GC=F Price"))

    # 5. Trading Signal Markers
    price_range = data['High'].max() - data['Low'].min()
    marker_offset = price_range * 0.04

    buys = data[data['Buy_Signal']]
    sells = data[data['Sell_Signal']]

    fig.add_scatter(x=buys.index, y=buys['Low'] - marker_offset, mode='markers',
                    marker=dict(symbol='triangle-up', size=14, color='#00FF41'), name="Buy Signal")
    fig.add_scatter(x=sells.index, y=sells['High'] + marker_offset, mode='markers',
                    marker=dict(symbol='triangle-down', size=14, color='#FF3131'), name="Sell Signal")

    fig.update_layout(
        height=config.CHART_HEIGHT_MAIN,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )


def _plot_volume(fig, data):
    colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
    fig.add_bar(x=data.index, y=data['Volume'], marker_color=colors, name="Volume")
    fig.update_layout(height=config.CHART_HEIGHT_INDICATOR)


def _plot_rsi(fig, data):
    fig.add_scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC'), name="RSI")
    fig.add_hline(y=config.RSI_OVERBOUGHT, line_color="red", line_dash="dash")
    fig.add_hline(y=config.RSI_OVERSOLD, line_color="green", line_dash="dash")
    fig.update_layout(height=config.CHART_HEIGHT_INDICATOR, yaxis=dict(range=[0, 100]))


def _plot_macd(fig, data):
    hist_colors = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
    fig.add_bar(x=data.index, y=data['MACD_Hist'], marker_color=hist_colors, name="MACD Hist")
    fig.update_layout(height=config.CHART_HEIGHT_INDICATOR)


def _render_news_section(news_list):
    st.divider()
    st.subheader("📰 Market News & Global Sentiment")
    if not news_list:
        st.info("Awaiting latest news updates...")
        return

    for item in news_list[:8]:
        with st.container(border=True):
            st.markdown(f"**{item['title']}**")
            st.markdown(f"[Read Article]({item['link']})")


render_live_overview()