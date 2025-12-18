import streamlit as st
import plotly.graph_objects as go
import numpy as np
import data_engine, trading_logic, styles, config

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()


def calculate_trend(y):
    x = np.arange(len(y))
    m, b = np.polyfit(x, y, 1)
    return m * x + b


@st.fragment(run_every="1m")
def render_live_overview():
    df_base, price_now, news_list, ytd_start = data_engine.get_gold_data("1 Day")
    metrics = data_engine.calculate_metrics(price_now, df_base, ytd_start)
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
        render_window("PRICE ACTION", "price", "p1", default_idx=4)
        render_window("VOLUME", "volume", "v1", default_idx=4)
        render_window("RSI", "rsi", "r1", default_idx=4)

    with col_sidebar:
        st.markdown("### 🚦 Signal Center")
        latest = df_base.iloc[-1]
        status, color = trading_logic.evaluate_status(latest)
        styles.display_signal("PRIMARY ACTION", status, "LIVE", color)
        st.divider()
        for n in news_list[:5]: st.markdown(f"● [{n['title']}]({n['link']})")


def render_window(title, chart_type, key_id, default_idx=2):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        h_col.markdown(f"**{title}**")
        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=default_idx, key=f"sel_{key_id}",
                             label_visibility="collapsed")

        full_df, _, _, _ = data_engine.get_gold_data(tf)
        lookback = 100 if tf in ["15m", "1h"] else 250
        data = full_df.tail(lookback)
        if data.empty: return st.warning("Data load error.")

        fig = go.Figure()
        if chart_type == "price":
            # DYNAMIC OFFSET CALCULATION (Fixes the "floating" triangles)
            # We use 5% of the current price range to position the signal
            price_range = data['High'].max() - data['Low'].min()
            offset = price_range * 0.04

            # Price Layers
            fig.add_trace(
                go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                               name="Price"))
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.5), name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(173, 216, 230, 0.2)', width=1),
                                     name="BB"))
            fig.add_trace(go.Scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(173, 216, 230, 0.2)', width=1),
                                     fill='tonexty'))

            # SIGNALS (The Fix)
            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]

            fig.add_trace(go.Scatter(x=buys.index, y=buys['Low'] - offset, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FF41',
                                                 line=dict(width=1, color='white')), name="BUY"))

            fig.add_trace(go.Scatter(x=sells.index, y=sells['High'] + offset, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF3131',
                                                 line=dict(width=1, color='white')), name="SELL"))

            fig.update_layout(height=450, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            v_colors = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_bar(x=data.index, y=data['Volume'], marker_color=v_colors)
            fig.update_layout(height=200)

        elif chart_type == "rsi":
            fig.add_scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC'))
            fig.add_hline(y=70, line_color="red", line_dash="dash")
            fig.add_hline(y=30, line_color="green", line_dash="dash")
            fig.update_layout(height=200, yaxis=dict(range=[0, 100]))

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key=f"plot_{key_id}_{chart_type}_{tf}")


render_live_overview()