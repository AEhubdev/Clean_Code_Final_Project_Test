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

    # Top Row Metrics
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
        render_window("MACD", "macd", "m1", default_idx=4)

    with col_sidebar:
        st.markdown("### 🚦 Signal Center")
        latest = df_base.iloc[-1]
        status, color = trading_logic.evaluate_status(latest)
        styles.display_signal("PRIMARY ACTION", status, "LIVE", color)

        # --- RESTORED MACD & RSI SIGNAL BLOCKS ---
        st.markdown("---")
        c1, c2 = st.columns(2)

        r_val = latest['RSI']
        r_col = "red" if r_val > 70 else "green" if r_val < 40 else "#00d4ff"
        c1.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {r_col}"><small>RSI (14)</small><br><strong style="font-size:18px">{r_val:.1f}</strong></div>',
            unsafe_allow_html=True)

        # MACD Signal Restored
        m_val = latest['MACD_Hist']
        m_dir, m_color = ("UP", "green") if m_val > 0 else ("DOWN", "red")
        c2.markdown(
            f'<div style="background:#1e2130; padding:10px; border-radius:5px; border-left:4px solid {m_color}"><small>MACD Hist</small><br><strong style="font-size:18px; color:{m_color}">{m_dir}</strong></div>',
            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sk, sd = latest['Stoch_K'], latest['Stoch_D']
        s_col = "green" if sk > sd else "red"
        st.markdown(
            f'<div style="background:#1e2130; padding:12px; border-radius:5px; border-left:4px solid {s_col}"><small>Stochastic (K/D)</small><br><strong>{sk:.0f} / {sd:.0f}</strong></div>',
            unsafe_allow_html=True)

        st.divider()
        st.markdown("### Market News")
        for n in news_list[:5]: st.markdown(f"● [{n['title']}]({n['link']})")


def render_window(title, chart_type, key_id, default_idx=2):
    with st.container(border=True):
        h_col, s_col = st.columns([0.7, 0.3])
        h_col.markdown(f"**{title}**")
        tf = s_col.selectbox("TF", list(config.TIMEFRAME_OPTIONS.keys()), index=default_idx, key=f"sel_{key_id}",
                             label_visibility="collapsed")

        full_df, _, _, _ = data_engine.get_gold_data(tf)
        data = full_df.tail(150)
        if data.empty: return st.warning("Connecting to exchange...")

        fig = go.Figure()

        if chart_type == "price":
            # Dynamic Positioning for Signals
            p_range = data['High'].max() - data['Low'].min()
            offset = p_range * 0.04

            # Trend & Indicators
            trend = calculate_trend(data['Close'].values)
            fig.add_scatter(x=data.index, y=trend, line=dict(color='orange', width=2, dash='dot'), name="Trend")
            fig.add_scatter(x=data.index, y=data['MA20'], line=dict(color='#00d4ff', width=1.2), name="MA20")
            fig.add_scatter(x=data.index, y=data['BB_U'], line=dict(color='rgba(255,255,255,0.1)', width=1))
            fig.add_scatter(x=data.index, y=data['BB_L'], line=dict(color='rgba(255,255,255,0.1)', width=1),
                            fill='tonexty')

            # Candles
            fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'],
                                         close=data['Close']))

            # Signals (Buy and Sell)
            buys = data[data['Buy_Signal']]
            sells = data[data['Sell_Signal']]
            fig.add_scatter(x=buys.index, y=buys['Low'] - offset, mode='markers',
                            marker=dict(symbol='triangle-up', size=16, color='#00FF41',
                                        line=dict(width=1, color='white')))
            fig.add_scatter(x=sells.index, y=sells['High'] + offset, mode='markers',
                            marker=dict(symbol='triangle-down', size=16, color='#FF3131',
                                        line=dict(width=1, color='white')))
            fig.update_layout(height=400, xaxis_rangeslider_visible=False)

        elif chart_type == "volume":
            v_cols = ['#00FF41' if c >= o else '#FF3131' for c, o in zip(data['Close'], data['Open'])]
            fig.add_bar(x=data.index, y=data['Volume'], marker_color=v_cols)
            fig.update_layout(height=180)

        elif chart_type == "rsi":
            fig.add_scatter(x=data.index, y=data['RSI'], line=dict(color='#BB86FC'))
            fig.add_hline(y=70, line_color="red", line_dash="dash")
            fig.add_hline(y=30, line_color="green", line_dash="dash")
            fig.update_layout(height=180, yaxis=dict(range=[0, 100]))

        elif chart_type == "macd":
            m_cols = ['#00FF41' if x >= 0 else '#FF3131' for x in data['MACD_Hist']]
            fig.add_bar(x=data.index, y=data['MACD_Hist'], marker_color=m_cols)
            fig.update_layout(height=180)

        fig.update_layout(template="plotly_dark", margin=dict(t=5, b=5, l=5, r=5), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


render_live_overview()