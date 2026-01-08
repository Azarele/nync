import streamlit as st
from supabase import create_client
from PIL import Image
import os

def setup_page():
    icon = "⚡"
    if os.path.exists("nync_favicon.png"): 
        icon = Image.open("nync_favicon.png")
    st.set_page_config(page_title="Nync", page_icon=icon, layout="wide")

@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase Config Error: {e}")
        return None

def init_session_state():
    if 'session' not in st.session_state: st.session_state.session = None
    if 'user' not in st.session_state: st.session_state.user = None