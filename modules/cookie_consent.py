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
            st.session_state.action = "set_consent_accept"
            st.rerun()
            
    with c2:
        if st.button("Decline Optional", use_container_width=True):
            st.session_state.action = "set_consent_decline"
            st.rerun()

def show(all_cookies):
    # 1. TRUTH CHECK: Check Browser Cookies directly.
    val = all_cookies.get("nync_consent")
    if val in ["accepted", "declined"]:
        st.session_state.consent = val
        return

    # 2. SESSION CHECK: If we just decided this session
    if st.session_state.get("consent") in ["accepted", "declined"]:
        return

    # 3. IF NO CONSENT FOUND -> SHOW DIALOG (Only trigger once)
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog()