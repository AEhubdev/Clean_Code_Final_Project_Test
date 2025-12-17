import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        .sidebar-header { color: white; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border-bottom: 2px solid gold; }
        .signal-container { background-color: #1E222D; padding: 15px; border-radius: 8px; border: 1px solid #363A45; margin-bottom: 10px; }
        .window-header { color: gold; font-size: 18px; font-weight: bold; margin-top: 25px; border-left: 4px solid gold; padding-left: 10px; }
        </style>
        """, unsafe_allow_html=True)

def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h3 style='color:{color}; margin-top:-10px;'>{val_text}</h3>", unsafe_allow_html=True)

def display_signal(label, value, status, color):
    st.markdown(f"""
        <div class="signal-container">
            <div style='color:#808495; font-size:12px;'>{label}</div>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='color:white; font-size:20px; font-weight:bold;'>{value}</span>
                <span style='background-color:{color}; color:black; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:10px;'>{status}</span>
            </div>
        </div>""", unsafe_allow_html=True)