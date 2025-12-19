import numpy as np
import plotly.graph_objects as go
import streamlit as st

import config
import data_engine
import styles
import trading_logic

# --- Application Setup ---
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


# --- Helper Functions ---
def calculate_trend_line(closing_prices: np.ndarray) -> np.ndarray:
    """Calculate linear trend line for closing prices.

    Args:
        closing_prices: Array of closing price values

    Returns:
        Array of trend line values
    """
    indices = np.arange(len(closing_prices))
    slope, intercept = np.polyfit(indices, closing_prices, 1)
    return slope * indices + intercept


def _get_indicator_html(label: str, value: str, color: str) -> str:
    """Generate HTML for indicator display.

    Args:
        label: Indicator label
        value: Indicator value to display
        color: Border color in hex format

    Returns:
        HTML string for indicator display
    """
    return (
        f'<div style="background:#1e2130; padding:10px; border-radius:5px; '
        f'border-left:4px solid {color}"><small>{label}</small><br>'
        f'<strong>{value}</strong></div>'
    )


# --- Core Rendering Functions ---
@st.fragment(run_every="1m")
def render_live_overview() -> None:
    """Main function to render the live dashboard overview."""
    gold_dataframe, current_price, news_items, ytd_start_price = (
        data_engine.get_gold_market_data("1 Day")
    )

    performance_metrics = data_engine.calculate_performance_metrics(
        current_price, gold_dataframe, ytd_start_price
    )
    daily_change_percent = _calculate_daily_change_percent(
        current_price, gold_dataframe
    )

    _render_header_section(current_price, daily_change_percent, performance_metrics)
    _render_main_content(gold_dataframe, news_items)


def _calculate_daily_change_percent(
        current_price: float,
        price_dataframe: pd.DataFrame
) -> float:
    """Calculate daily percentage price change."""
    if len(price_dataframe) < 2:
        return 0.0

    previous_close = price_dataframe['Close'].iloc[-2]
    return ((current_price - previous_close) / previous_close) * 100


def _render_header_section(
        current_price: float,
        daily_change_percent: float,
        performance_metrics: tuple
) -> None:
    """Render the main header section with metrics."""
    st.title("🏆 Gold Multi-Timeframe Terminal")

    metric_columns = st.columns(5)
    metric_columns[0].metric(
        label="Live Gold",
        value=f"${current_price:,.2f}",
        delta=f"{daily_change_percent:+.2f}%"
    )

    styles.colored_metric(
        metric_columns[1], "Weekly", f"{performance_metrics[0]:+.2f}%",
        performance_metrics[0]
    )
    styles.colored_metric(
        metric_columns[2], "Monthly", f"{performance_metrics[1]:+.2f}%",
        performance_metrics[1]
    )
    styles.colored_metric(
        metric_columns[3], "YTD", f"{performance_metrics[2]:+.2f}%",
        performance_metrics[2]
    )
    styles.colored_metric(
        metric_columns[4], "Volatility", f"{performance_metrics[3]:.2f}%",
        performance_metrics[3],
        is_vol=True
    )

    st.divider()


def _render_main_content(price_dataframe: pd.DataFrame, news_items: list) -> None:
    """Render the main content area with charts and sidebar."""
    left_panel, right_panel = st.columns([0.72, 0.28])

    with left_panel:
        _render_chart_panels()

    with right_panel:
        _render_sidebar_signals(price_dataframe)

    _render_news_section(news_items)


def _render_chart_panels() -> None:
    """Render all chart panels in the main content area."""
    render_chart_window("PRICE ACTION & AI FORECAST", "price", "p1_daily", default_idx=2)
    render_chart_window("VOLUME", "volume", "v1_vol", default_idx=2)
    render_chart_window("RSI", "rsi", "r1_rsi", default_idx=2)
    render_chart_window("MACD", "macd", "m1_macd", default_idx=2)


def _render_sidebar_signals(price_dataframe: pd.DataFrame) -> None:
    """Render the sidebar signal panel with technical indicators."""
    st.markdown("### 🚦 Signal Center")

    latest_bar = price_dataframe.iloc[-1]
    signal_text, signal_color = trading_logic.evaluate_status(latest_bar)

    styles.display_signal("PRIMARY ACTION", signal_text, "LIVE", signal_color)
    st.markdown("---")

    _render_technical_indicators(latest_bar)
    st.markdown("<br>", unsafe_allow_html=True)

    _render_stochastic_indicator(latest_bar)


def _render_technical_indicators(latest_bar: pd.Series) -> None:
    """Render RSI and MACD indicators in sidebar."""
    rsi_value = latest_bar['RSI']
    rsi_color = _get_rsi_color(rsi_value)

    column1, column2 = st.columns(2)

    column1.markdown(
        _get_indicator_html("RSI (14)", f"{rsi_value:.1f}", rsi_color),
        unsafe_allow_html=True
    )

    macd_value = latest_bar['MACD_Hist']
    macd_direction, macd_color = ("UP", "green") if macd_value > 0 else ("DOWN", "red")

    column2.markdown(
        _get_indicator_html("MACD Hist", macd_direction, macd_color),
        unsafe_allow_html=True
    )


def _get_rsi_color(rsi_value: float) -> str:
    """Determine color for RSI value."""
    if rsi_value > config.RSI_OVERBOUGHT:
        return "red"
    elif rsi_value < 45:
        return "green"
    return "#00d4ff"


def _render_stochastic_indicator(latest_bar: pd.Series) -> None:
    """Render stochastic oscillator indicator."""
    stoch_text = f"{latest_bar['Stoch_K']:.0f} / {latest_bar['Stoch_D']:.0f}"
    stoch_color = "green" if latest_bar['Stoch_K'] > latest_bar['Stoch_D'] else "red"

    st.markdown(
        _get_indicator_html("Stochastic (K/D)", stoch_text, stoch_color),
        unsafe_allow_html=True
    )


def render_chart_window(
        title: str,
        chart_type: str,
        key_id: str,
        default_idx: int = 2
) -> None:
    """Render a single chart window with timeframe selector.

    Args:
        title: Window title
        chart_type: Type of chart to render ('price', 'volume', 'rsi', 'macd')
        key_id: Unique key for Streamlit widget
        default_idx: Default timeframe selection index
    """
    with st.container(border=True):
        header_column, select_column = st.columns([0.7, 0.3])
        header_column.markdown(f"**{title}**")

        selected_timeframe = select_column.selectbox(
            "TF",
            list(config.TIMEFRAME_OPTIONS.keys()),
            index=default_idx,
            key=f"sel_{key_id}",
            label_visibility="collapsed"
        )

        timeframe_data, _, _, _ = data_engine.get_gold_market_data(selected_timeframe)
        plot_data = timeframe_data.tail(150)

        if plot_data.empty:
            st.warning("Loading...")
            return

        figure = go.Figure()
        show_legend = chart_type == "price"

        if chart_type == "price":
            _plot_price_with_signals(figure, plot_data)
        elif chart_type == "volume":
            _plot_volume(figure, plot_data)
        elif chart_type == "rsi":
            _plot_rsi(figure, plot_data)
        elif chart_type == "macd":
            _plot_macd(figure, plot_data)

        _configure_chart_layout(figure, show_legend)
        st.plotly_chart(figure, use_container_width=True)


def _configure_chart_layout(figure: go.Figure, show_legend: bool) -> None:
    """Configure common chart layout settings."""
    figure.update_layout(
        template="plotly_dark",
        margin=dict(t=30 if show_legend else 5, b=5, l=5, r=5),
        showlegend=show_legend
    )


def _plot_price_with_signals(figure: go.Figure, data: pd.DataFrame) -> None:
    """Plot price chart with technical indicators and signals."""
    # AI Forecast
    prediction_dataframe = data_engine.generate_ai_prediction(data)
    if not prediction_dataframe.empty:
        figure.add_scatter(
            x=prediction_dataframe.index,
            y=prediction_dataframe['Predicted'],
            line=dict(color='#FFD700', width=3, dash='dashdot'),
            name="AI 30D Forecast"
        )

    # Trend Line
    trend_values = calculate_trend_line(data['Close'].values)
    figure.add_scatter(
        x=data.index,
        y=trend_values,
        line=dict(color='orange', width=2, dash='dot'),
        name="Linear Trend"
    )

    # Moving Averages
    figure.add_scatter(
        x=data.index,
        y=data['MA20'],
        line=dict(color='#00d4ff', width=1.2),
        name="MA 20"
    )
    figure.add_scatter(
        x=data.index,
        y=data['MA50'],
        line=dict(color='cyan', width=1.2, dash='dash'),
        name="MA 50"
    )

    # Bollinger Bands
    figure.add_scatter(
        x=data.index,
        y=data['BB_U'],
        line=dict(color='rgba(255,255,255,0.15)', width=1),
        name="BB Upper"
    )
    figure.add_scatter(
        x=data.index,
        y=data['BB_L'],
        line=dict(color='rgba(255,255,255,0.15)', width=1),
        fill='tonexty',
        fillcolor='rgba(255,255,255,0.05)',
        name="BB Lower"
    )

    # Candlesticks
    figure.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Gold Price"
        )
    )

    # Trading Signals
    price_range = data['High'].max() - data['Low'].min()
    offset = price_range * 0.04

    buy_signals = data[data['Buy_Signal']]
    sell_signals = data[data['Sell_Signal']]

    figure.add_scatter(
        x=buy_signals.index,
        y=buy_signals['Low'] - offset,
        mode='markers',
        marker=dict(symbol='triangle-up', size=14, color='#00FF41'),
        name="Buy Signal"
    )
    figure.add_scatter(
        x=sell_signals.index,
        y=sell_signals['High'] + offset,
        mode='markers',
        marker=dict(symbol='triangle-down', size=14, color='#FF3131'),
        name="Sell Signal"
    )

    figure.update_layout(
        height=config.CHART_HEIGHT_MAIN,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )


def _plot_volume(figure: go.Figure, data: pd.DataFrame) -> None:
    """Plot volume bars with color coding."""
    color_list = [
        '#00FF41' if close >= open_ else '#FF3131'
        for close, open_ in zip(data['Close'], data['Open'])
    ]

    figure.add_bar(
        x=data.index,
        y=data['Volume'],
        marker_color=color_list,
        name="Volume"
    )
    figure.update_layout(height=config.CHART_HEIGHT_INDICATOR)


def _plot_rsi(figure: go.Figure, data: pd.DataFrame) -> None:
    """Plot RSI indicator with overbought/oversold lines."""
    figure.add_scatter(
        x=data.index,
        y=data['RSI'],
        line=dict(color='#BB86FC'),
        name="RSI"
    )
    figure.add_hline(
        y=config.RSI_OVERBOUGHT,
        line_color="red",
        line_dash="dash"
    )
    figure.add_hline(
        y=config.RSI_OVERSOLD,
        line_color="green",
        line_dash="dash"
    )
    figure.update_layout(
        height=config.CHART_HEIGHT_INDICATOR,
        yaxis=dict(range=[0, 100])
    )


def _plot_macd(figure: go.Figure, data: pd.DataFrame) -> None:
    """Plot MACD histogram with color coding."""
    histogram_colors = [
        '#00FF41' if value >= 0 else '#FF3131'
        for value in data['MACD_Hist']
    ]

    figure.add_bar(
        x=data.index,
        y=data['MACD_Hist'],
        marker_color=histogram_colors,
        name="MACD Hist"
    )
    figure.update_layout(height=config.CHART_HEIGHT_INDICATOR)


def _render_news_section(news_items: list) -> None:
    """Render the news section with market updates."""
    st.divider()
    st.subheader("📰 Market News & Global Sentiment")

    if not news_items:
        st.info("No news available.")
        return

    for news_item in news_items[:8]:
        with st.container(border=True):
            st.markdown(f"**{news_item['title']}**")
            st.markdown(f"[Read Article]({news_item['link']})")


# --- Application Entry Point ---
if __name__ == "__main__":
    render_live_overview()