import streamlit as st
from db import supabase

# --- 1. CORE AUTH & PROFILE LOGIC ---
def login_user(email, password):
    if not supabase: return False
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            st.session_state.session = res.session
            st.session_state.user = res.user
            return True
    except Exception as e: 
        st.warning(f"Login failed: {e}")
    return False

def signup_user(email, password):
    if not supabase: return False
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.session:
            st.session_state.session = res.session
            st.session_state.user = res.user
            return True
        else: 
            st.info("Check email to confirm.")
    except Exception as e: 
        st.warning(f"Sign up failed: {e}")
    return False

@st.cache_data(ttl=300)
def get_user_profile(user_id):
    try: return supabase.table('profiles').select('*').eq('id', user_id).single().execute().data
    except: return None

def get_tier_level(tier_name):
    tiers = {'free': 0, 'squad': 1, 'guild': 2, 'empire': 3}
    return tiers.get(str(tier_name).lower(), 0)

def restore_session(access_token, refresh_token):
    if not supabase: return None
    try:
        res = supabase.auth.set_session(access_token, refresh_token)
        if res.user:
            return res.session
    except:
        return None
    return None

def delete_user_data(user_id):
    try:
        supabase.table('calendar_connections').delete().eq('user_id', user_id).execute()
        supabase.table('team_members').delete().eq('user_id', user_id).execute()
        supabase.table('profiles').delete().eq('id', user_id).execute()
        return True
    except: return False

def upgrade_user_tier(user_id, tier_name):
    try:
        supabase.table('profiles').update({'subscription_tier': tier_name}).eq('id', user_id).execute()
        get_user_profile.clear()
        return True
    except: return False

# --- 2. FORWARD IMPORTS ---
# This ensures that any file doing `import auth_utils as auth` 
# still has access to ALL your functions exactly as they did before!
from team_utils import *
from billing_utils import *
from calendar_utils import *