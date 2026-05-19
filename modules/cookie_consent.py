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
            st.session_state.save_consent_val = "accepted"
            st.rerun()
            
    with c2:
        if st.button("Decline Optional", use_container_width=True):
            st.session_state.save_consent_val = "declined"
            st.rerun()

def show(all_cookies):
    if 'cookie_buffer' not in st.session_state:
        st.session_state.cookie_buffer = True
        return

    val = all_cookies.get("nync_consent")
    if val in ["accepted", "declined"]:
        st.session_state.consent = val
        return

    if st.session_state.get("consent") in ["accepted", "declined"]:
        return

    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog()