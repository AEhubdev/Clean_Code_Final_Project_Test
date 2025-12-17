import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        [data-testid="stMetricLabel"] { color: #808495 !important; }
        [data-testid="stMetricValue"] { color: white !important; }
        .sidebar-header { color: white !important; font-size: 28px !important; font-weight: bold; text-align: center; margin-bottom: 20px; }
        .signal-container { background-color: #1E222D; padding: 20px; border-radius: 10px; border: 1px solid #363A45; margin-bottom: 15px; }
        .window-header { color: white !important; font-size: 22px !important; font-weight: bold; margin-top: 20px; border-bottom: 1px solid #363A45; padding-bottom: 5px; }
        .news-link { color: #FFFFFF !important; text-decoration: none !important; display: block; padding: 8px; border-bottom: 1px solid #363A45; margin-bottom: 5px; font-size: 15px; }
        .news-link:hover { background-color: #1E222D; color: #FFD700 !important; }
        </style>
        """, unsafe_allow_html=True)

def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>", unsafe_allow_html=True)
    if is_vol: col.caption("Annualized Risk")

def display_signal(label, value, status, color):
    st.markdown(f"""
        <div class="signal-container">
            <div style='color:white; font-size:16px; font-weight:bold; margin-bottom:5px;'>{label}</div>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='color:white; font-size:26px; font-weight:bold;'>{value}</span>
                <span style='background-color:{color}; color:black; padding:2px 10px; border-radius:5px; font-weight:bold; font-size:12px;'>{status}</span>
            </div>
        </div>""", unsafe_allow_html=True)