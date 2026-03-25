import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    try:
        if "supabase" not in st.secrets: return None
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = get_supabase()