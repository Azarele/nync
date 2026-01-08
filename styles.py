import streamlit as st

def load_css():
    css_vars = """
        --bg-app: #000000; --bg-card: #09090b; --text-primary: #ffffff; --text-secondary: #a1a1aa;
    """
    st.markdown(f"""
    <style>
        :root {{ {css_vars} }}
        .stApp {{ background-color: var(--bg-app); font-family: 'Inter', sans-serif; }}
        h1, h2, h3, h4 {{ color: var(--text-primary) !important; letter-spacing: -0.02em; }}
        p, label, span, div {{ color: var(--text-primary); }}
        
        div[data-baseweb="input"] {{ background-color: #000000 !important; border: 1px solid #ffffff !important; border-radius: 4px !important; }}
        input.stTextInput {{ color: #ffffff !important; caret-color: #ffffff !important; }}
        input::placeholder {{ color: #666666 !important; opacity: 1 !important; }}

        button[kind="primary"] {{ background-color: #ffffff !important; border: 1px solid #ffffff !important; width: 100%; transition: opacity 0.2s; }}
        button[kind="primary"] * {{ color: #000000 !important; font-weight: 700 !important; }}
        button[kind="primary"]:hover {{ opacity: 0.9; }}
        
        button[kind="secondary"] {{ background-color: transparent !important; color: #ffffff !important; border: 1px solid #ffffff !important; width: 100%; }}
        
        .login-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-top: 50px; }}
        .pain-card {{ background-color: var(--bg-card); border: 1px solid #333; border-radius: 8px; padding: 24px; height: 100%; }}
        .status-pill {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }}
        .toxic {{ background: #450a0a; color: #fecaca !important; border: 1px solid #7f1d1d; }}
        .painful {{ background: #431407; color: #fed7aa !important; border: 1px solid #7c2d12; }}
        .annoying {{ background: #422006; color: #fef08a !important; border: 1px solid #713f12; }}
        .ideal {{ background: #064e3b; color: #a7f3d0 !important; border: 1px solid #065f46; }}
        section[data-testid="stSidebar"] {{ background-color: var(--bg-card); border-right: 1px solid #333; }}
    </style>
    """, unsafe_allow_html=True)