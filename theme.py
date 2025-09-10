# theme.py
# Tema Permanen untuk Streamlit Anti-Bully

def apply_theme():
    import streamlit as st
    st.set_page_config(layout='wide')
    st.markdown(
        f"""
        <style>
        body {{
            background-color: #FDFDFD;
            color: #000000;
        }}
        .stApp {{
            background-color: #FDFDFD;
        }}
        .stButton>button {{
            background-color: #1689FF;
            color: #fff;
            border-radius: 8px;
        }}
        .stTextInput>div>div>input {{
            border-radius: 8px;
        }}
        .st-cg, .st-ce, .css-1d391kg {{
            background-color: #8BAAD6 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

THEME = {
    "primary_color": "#1689FF",
    "background_color": "#FDFDFD",
    "text_color": "#000000",
    "secondary_background_color": "#8BAAD6",
    "border_radius": "8px"
}

def get_theme():
    return THEME
