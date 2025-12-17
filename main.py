import streamlit as st
import plotly.graph_objects as go
import data_engine, trading_logic, styles, config
import time

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
styles.apply_custom_styles()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">TERMINAL SETTINGS</div>', unsafe_allow_html=True)
    choice = st.selectbox("Select Timeframe", list(config.TIMEFRAME_OPTIONS.keys()), index=2)
    selected_interval = config.TIMEFRAME_OPTIONS[choice]

    st.write("---")
    st.write("⏱️ **Auto-Refresh:** Every 15 mins")
    if st.button("Manual Refresh"):
        st.cache_data.clear()
        st.rerun()

# DATA LOADING
data, price = data_engine.get_gold_data(selected_interval)
latest = data.iloc[-1]

# --- UI ASSEMBLY (Rest of your existing main.py code) ---
# Ensure your metrics and graphs use the 'data' and 'price' variables fetched above
st.title(f"🏆 Gold Market Overview ({choice})")

# [Insert your existing Metrics, 4-window layout, and News code here]

# --- AUTO-REFRESH LOGIC ---
# This script will trigger a rerun every 15 minutes (900 seconds)
time_to_refresh = 900
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > time_to_refresh:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()