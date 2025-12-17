import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config

# Initialize Page
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# 1. TOP-LEVEL DATA FETCH (For Header Metrics)
# We use '1d' as the baseline for the top metrics
df_metrics, price_now, news_list = data_engine.get_gold_data("1d")
w_c, m_c, y_c, vol = data_engine.calculate_metrics(price_now, df_metrics)

# --- HEADER SECTION ---
st.title("🏆 Gold Multi-Timeframe Terminal")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Live Gold Price", f"${price_now:,.2f}", f"{w_c:+.2f}%")
styles.colored_metric(c2, "Weekly Change", f"{w_c:+.2f}%", w_c)
styles.colored_metric(c3, "Monthly Change", f"{m_c:+.2f}%", m_c)
styles.colored_metric(c4, "YTD Performance", f"{y_c:+.2f}%", y_c)
styles.colored_metric(c5, "Volatility Index", f"{vol:.2f}%", vol, is_vol=True)
st.divider()

col_charts, col_sidebar = st.columns([0.72, 0.28])


# --- CHART FRAGMENTS (Independent Timeframes) ---

@st.fragment(run_every="15m")
def render_price_window():
    with st.container(border=True):
        head_col, select_col = st.columns([0.75, 0.25])
        head_col.markdown('<div class="window-header" style="margin-top:0;">WINDOW 1: LIVE PRICE ACTION</div>',
                          unsafe_allow_html=True)
        tf_choice = select_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key="tf_p",
                                         label_visibility="collapsed")

        # Fetch data for this specific window
        data = data_engine.get_custom_data(tf_choice)

        if not data.empty:
            fig = go.Figure()
            # Candlestick
            fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                         low=data['Low'], close=data['Close'], name="Gold"))
            # Signals
            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] * 0.998, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FF41'), name='Buy'))
            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] * 1.002, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF3131'), name='Sell'))

            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False,
                              margin=dict(t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data found for this timeframe.")


@st.fragment()
def render_rsi_window():
    with st.container(border=True):
        head_col, select_col = st.columns([0.75, 0.25])
        head_col.markdown('<div class="window-header" style="margin-top:0;">WINDOW 2: RSI MOMENTUM</div>',
                          unsafe_allow_html=True)
        tf_choice = select_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key="tf_r",
                                         label_visibility="collapsed")

        data = data_engine.get_custom_data(tf_choice)
        if not data.empty:
            fig = go.Figure(go.Scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC', width=2)))
            fig.add_hline(y=70, line_dash="dash", line_color="#FF3131")
            fig.add_hline(y=30, line_dash="dash", line_color="#00FF41")
            fig.update_layout(template="plotly_dark", height=200, yaxis=dict(range=[0, 100]), margin=dict(t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)


@st.fragment()
def render_macd_window():
    with st.container(border=True):
        head_col, select_col = st.columns([0.75, 0.25])
        head_col.markdown('<div class="window-header" style="margin-top:0;">WINDOW 3: MACD TREND</div>',
                          unsafe_allow_html=True)
        tf_choice = select_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=2, key="tf_m",
                                         label_visibility="collapsed")

        data = data_engine.get_custom_data(tf_choice)
        if not data.empty:
            h_colors = ['#00FF41' if v >= 0 else '#FF3131' for v in data['MACD_Hist']]
            fig = go.Figure(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=h_colors))
            fig.update_layout(template="plotly_dark", height=200, margin=dict(t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)


# --- COLUMN PLACEMENT ---
with col_charts:
    render_price_window()
    render_rsi_window()
    render_macd_window()

with col_sidebar:
    st.markdown('<div class="sidebar-header">📡 LIVE SIGNALS</div>', unsafe_allow_html=True)

    # Use the 1d data for current status
    latest_row = df_metrics.iloc[-1]
    status, color = trading_logic.evaluate_status(latest_row)

    styles.display_signal("PRIMARY ACTION", status, "LIVE", color)
    styles.display_signal("RSI STRENGTH", f"{latest_row['RSI']:.1f}", "ACTIVE", "#BB86FC")
    styles.display_signal("STOCH %K", f"{latest_row['STOCH_K']:.1f}%", "READY", "#FFA500")

    st.markdown('<div class="window-header">📰 MARKET NEWS</div>', unsafe_allow_html=True)
    if news_list:
        for article in news_list[:8]:
            st.markdown(f'<a href="{article["link"]}" target="_blank" class="news-link">● {article["title"]}</a>',
                        unsafe_allow_html=True)
    else:
        st.write("Fetching news...")

    st.divider()
    if st.button("🔄 Sync Global Terminal"):
        st.cache_data.clear()
        st.rerun()