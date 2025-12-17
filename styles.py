import streamlit as st

def apply_terminal_theme():
    st.markdown("""
        <style>
        .main { background-color: #0E1117; }
        .signal-card { 
            background-color: #1E222D; 
            padding: 15px; 
            border-radius: 8px; 
            border: 1px solid #363A45; 
            margin-bottom: 10px;
        }
        .status-buy { color: #00FF41; font-weight: bold; }
        .status-sell { color: #FF3131; font-weight: bold; }
        .news-box { border-left: 3px solid #FFD700; padding-left: 10px; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

def render_news_item(article):
    st.markdown(f"""
        <div class='news-box'>
            <a href='{article['link']}' target='_blank' style='color:white; text-decoration:none;'>
                {article['title']}
            </a>
        </div>
    """, unsafe_allow_html=True)