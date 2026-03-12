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
            st.session_state.action = "set_consent"
            st.rerun()
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            st.session_state.action = "set_consent"
            st.rerun()

def show(all_cookies):
    # 1. TRUTH CHECK: Check Browser Cookies. If exists, we are done forever.
    if all_cookies.get("nync_consent") == "accepted":
        st.session_state.consent = "accepted"
        return

    # 2. SESSION CHECK: If we just clicked accept this session, hide it.
    if st.session_state.get("consent") == "accepted":
        return

    # 3. IF NO CONSENT FOUND -> SHOW DIALOG
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog()