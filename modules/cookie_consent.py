import streamlit as st
import datetime as dt

@st.dialog("🍪 Cookie Settings")
def cookie_dialog():
    st.write("We use cookies to improve your experience and offer personalized upgrades.")
    st.caption("Customize your preferences:")
    essential = st.checkbox("Essential (Required)", value=True, disabled=True)
    analytics = st.checkbox("Analytics", value=True, key="modal_ana")
    marketing = st.checkbox("Marketing & Offers", value=True, key="modal_mkt")
    
    st.write("") 
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept All", type="primary", use_container_width=True):
            save_consent({
                "essential": True, 
                "analytics": True, 
                "marketing": True, 
                "timestamp": str(dt.datetime.now())
            })
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            save_consent({
                "essential": True, 
                "analytics": analytics, 
                "marketing": marketing, 
                "timestamp": str(dt.datetime.now())
            })

def show(all_cookies):
    # 1. Check Session State
    if st.session_state.get("consent"):
        return

    # 2. Check Browser Cookies
    if "nync_consent" in all_cookies and all_cookies["nync_consent"]:
        st.session_state.consent = all_cookies["nync_consent"]
        return

    # 3. Show Dialog
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog()

def save_consent(preferences):
    # Flag to app.py to physically save the cookie outside of the dialog
    st.session_state.consent = preferences
    st.session_state.consent_pending_save = True
    st.rerun() # Closes dialog and triggers app.py to save