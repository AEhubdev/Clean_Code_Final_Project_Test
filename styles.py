import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        [data-testid="stMetricLabel"] { color: #808495 !important; }
        [data-testid="stMetricValue"] { color: white !important; }
        .sidebar-header { color: white !important; font-size: 28px !important; font-weight: bold; text-align: center; }
        .signal-container { background-color: #1E222D; padding: 20px; border-radius: 10px; border: 1px solid #363A45; margin-bottom: 15px; }
        .window-header { color: white !important; font-size: 22px !important; font-weight: bold; border-bottom: 1px solid #363A45; margin-top: 20px; }
        .news-link { color: #FFFFFF !important; text-decoration: none !important; display: block; padding: 8px; border-bottom: 1px solid #363A45; font-size: 14px; }
        .news-link:hover { color: #FFD700 !important; background-color: #1E222D; }
        </style>
        """, unsafe_allow_html=True)

def render_news_item(article):
    st.markdown(f'<a href="{article["link"]}" target="_blank" class="news-link">● {article["title"]}</a>', unsafe_allow_html=True)

def colored_metric(col, label, val_text, delta_val, is_vol=False):
    color = "#FFA500" if is_vol else ("#00FF41" if delta_val > 0 else "#FF3131")
    col.markdown(f"**{label}**")
    col.markdown(f"<h2 style='color:{color}; margin-top:-15px; font-weight:bold;'>{val_text}</h2>", unsafe_allow_html=True)

def display_signal(label, value, status, color):
    st.markdown(f"""
        <div class="signal-container">
            <div style='color:white; font-size:16px; font-weight:bold;'>{label}</div>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='color:white; font-size:26px; font-weight:bold;'>{value}</span>
                <span style='background-color:{color}; color:black; padding:2px 10px; border-radius:5px; font-weight:bold; font-size:12px;'>{status}</span>
            </div>
        </div>""", unsafe_allow_html=True)