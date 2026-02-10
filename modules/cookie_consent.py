import streamlit as st
import datetime as dt
import time

@st.dialog("🍪 Cookie Settings")
def cookie_dialog(cookie_manager):
    st.write("We use cookies to improve your experience and offer personalized upgrades.")
    st.caption("Customize your preferences:")
    essential = st.checkbox("Essential (Required)", value=True, disabled=True)
    analytics = st.checkbox("Analytics", value=True, key="modal_ana")
    marketing = st.checkbox("Marketing & Offers", value=True, key="modal_mkt")
    
    st.write("") 
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept All", type="primary", use_container_width=True):
            save_consent(cookie_manager, {"essential": True, "analytics": True, "marketing": True, "timestamp": str(dt.datetime.now())}, "consent_set_all")
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            save_consent(cookie_manager, {"essential": True, "analytics": analytics, "marketing": marketing, "timestamp": str(dt.datetime.now())}, "consent_set_select")

def show(cookie_manager, cookies):
    if st.session_state.get("consent"): return
    if "nync_consent" in cookies:
        st.session_state.consent = cookies["nync_consent"]
        return

    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog(cookie_manager)

def save_consent(cookie_manager, preferences, unique_key):
    st.session_state.consent = preferences
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", preferences, expires_at=expires, key=unique_key)
    st.success("Preferences Saved!")
    time.sleep(10) # Increased wait time
    st.rerun()