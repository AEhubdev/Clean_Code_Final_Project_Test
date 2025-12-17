import streamlit as st

def apply_terminal_theme():
    """Injects custom CSS for the Gold Terminal aesthetic."""
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        [data-testid="stMetricLabel"] { color: #808495 !important; }
        [data-testid="stMetricValue"] { color: white !important; }
        .signal-card { 
            background-color: #1E222D; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #363A45; 
            margin-bottom: 15px;
        }
        .status-buy { color: #00FF41; font-weight: bold; font-size: 20px; }
        .status-sell { color: #FF3131; font-weight: bold; font-size: 20px; }
        .status-hold { color: #808495; font-weight: bold; font-size: 20px; }
        .news-link {
            color: #FFFFFF !important;
            text-decoration: none !important;
            display: block;
            padding: 8px;
            border-bottom: 1px solid #363A45;
            margin-bottom: 5px;
            font-size: 14px;
        }
        .news-link:hover { background-color: #1E222D; color: #FFD700 !important; }
        </style>
    """, unsafe_allow_html=True)

def render_news_item(article):
    """Renders a single news headline in the sidebar."""
    st.markdown(f'<a href="{article["link"]}" target="_blank" class="news-link">● {article["title"]}</a>', unsafe_allow_html=True)