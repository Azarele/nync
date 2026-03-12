import streamlit as st

@st.dialog("🍪 Cookie Settings")
def cookie_dialog():
    st.write("We use cookies to improve your experience and offer personalized upgrades.")
    st.caption("Customize your preferences:")
    
    st.checkbox("Essential (Required)", value=True, disabled=True)
    st.checkbox("Analytics", value=True, key="modal_ana")
    st.checkbox("Marketing & Offers", value=True, key="modal_mkt")
    
    st.write("") 
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept All", type="primary", use_container_width=True):
            save_consent()
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            save_consent()

def show(all_cookies):
    # 1. Check Session State (Instant Check)
    if st.session_state.get("consent"):
        return

    # 2. Check Browser Cookies (Checks if we've accepted before)
    if all_cookies.get("nync_consent") == "accepted":
        st.session_state.consent = "accepted"
        return

    # 3. Show Dialog if neither passed
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog()

def save_consent():
    # Pass a simple flag back to app.py to physically save the cookie
    st.session_state.consent = "accepted"
    st.session_state.consent_pending_save = True
    st.rerun() # Closes dialog seamlessly