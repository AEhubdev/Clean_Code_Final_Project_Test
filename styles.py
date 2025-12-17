import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        .sidebar-header { color: gold; font-size: 24px; font-weight: bold; border-bottom: 2px solid #363A45; padding-bottom: 10px; margin-bottom: 20px; }
        .window-header { color: #808495; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-top: 20px; border-left: 3px solid gold; padding-left: 10px; }
        .signal-card { background: #1E222D; padding: 15px; border-radius: 8px; border: 1px solid #363A45; margin-bottom: 10px; }
        .news-item { font-size: 14px; padding: 8px 0; border-bottom: 1px solid #1E222D; }
        </style>
        """, unsafe_allow_html=True)

def metric_row(c1, c2, c3, p, w, m):
    c1.metric("Live Gold", f"${p:,.2f}", f"{w:+.2f}%")
    c2.metric("Weekly Change", f"{w:+.2f}%")
    c3.metric("Monthly Change", f"{m:+.2f}%")