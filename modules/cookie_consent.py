import streamlit as st
import datetime as dt
import time

@st.dialog("🍪 Cookie Settings")
def cookie_dialog(cookie_manager):
    st.write("We use cookies to improve your experience and offer personalized upgrades.")
    st.caption("Customize your preferences:")
    
    st.checkbox("Essential (Required)", value=True, disabled=True)
    st.checkbox("Analytics", value=True, key="modal_ana")
    st.checkbox("Marketing & Offers", value=True, key="modal_mkt")
    
    st.write("") 
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept All", type="primary", use_container_width=True):
            save_consent(cookie_manager)
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            save_consent(cookie_manager)

def show(cookie_manager, all_cookies):
    # 1. ULTIMATE TRUTH: Check Browser Cookies
    # If the browser has the cookie, we are good forever.
    if all_cookies.get("nync_consent") == "accepted":
        st.session_state.consent = "accepted"
        return

    # 2. FAST CHECK: Check Session State
    if st.session_state.get("consent") == "accepted":
        return

    # 3. SHOW DIALOG
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog(cookie_manager)

def save_consent(cookie_manager):
    # 1. Update session state
    st.session_state.consent = "accepted"
    
    # 2. Write to browser permanently
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", "accepted", expires_at=expires, key="direct_consent_set")
    
    st.success("Preferences Saved!")
    
    # 3. Wait for the browser to catch the cookie before refreshing
    time.sleep(1)
    st.rerun()