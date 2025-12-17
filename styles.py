import streamlit as st


def apply_custom_styles():
    """Injects CSS for the terminal UI layout."""
    terminal_css = """
        <style>
        .main { background-color: #0E1117; }
        [data-testid="stMetricLabel"] { color: grey !important; }
        [data-testid="stMetricValue"] { color: white !important; }

        .sidebar-header { 
            color: white !important; font-size: 28px !important; 
            font-weight: bold; text-align: center; margin-bottom: 20px; 
            border-bottom: 2px solid gold; padding-bottom: 10px; 
        }

        .signal-container { 
            background-color: #1E222D; padding: 20px; 
            border-radius: 10px; border: 1px solid #363A45; 
            margin-bottom: 15px; 
        }

        .news-link { 
            color: #FFFFFF !important; text-decoration: none !important; 
            display: block; padding: 8px; border-bottom: 1px solid #363A45; 
            margin-bottom: 5px; font-size: 15px; 
        }
        .news-link:hover { background-color: #1E222D; color: #FFD700 !important; }
        </style>
    """
    st.markdown(terminal_css, unsafe_allow_html=True)


def colored_metric(column_element, label, display_value, delta_value, is_volatility=False):
    """
    Renders a stylized metric with dynamic coloring.
    Positive delta = Green, Negative = Red, Volatility = Orange.
    """
    # Color selection logic (Rule C2.17: No convoluted logic)
    if is_volatility:
        text_color = "#FFA500"
    elif delta_value > 0:
        text_color = "#00FF41"
    elif delta_value < 0:
        text_color = "#FF3131"
    else:
        text_color = "#FFFFFF"

    column_element.markdown(f"**{label}**")
    metric_html = f"""
        <h2 style='color:{text_color}; margin-top:-15px; font-weight:bold;'>
            {display_value}
        </h2>
    """
    column_element.markdown(metric_html, unsafe_allow_html=True)


def display_signal(title, signal_value, badge_text, badge_color):
    """Displays a high-visibility signal card in the sidebar."""
    card_html = f"""
        <div class="signal-container">
            <div style='color:white; font-size:16px; font-weight:bold; margin-bottom:5px;'>
                {title}
            </div>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='color:white; font-size:26px; font-weight:bold;'>
                    {signal_value}
                </span>
                <span style='background-color:{badge_color}; color:black; padding:2px 10px; 
                             border-radius:5px; font-weight:bold; font-size:12px;'>
                    {badge_text}
                </span>
            </div>
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)