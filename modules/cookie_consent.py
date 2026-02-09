import streamlit as st
import datetime as dt
import time

# 1. DEFINE THE DIALOG (MODAL)
@st.dialog("🍪 Cookie Settings")
def cookie_dialog(cookie_manager):
    st.write("We use cookies to improve your experience and offer personalized upgrades.")
    
    st.caption("Customize your preferences:")
    # Checkboxes for granular control
    essential = st.checkbox("Essential (Required)", value=True, disabled=True)
    analytics = st.checkbox("Analytics", value=True, key="modal_ana")
    marketing = st.checkbox("Marketing & Offers", value=True, key="modal_mkt")
    
    st.write("") # Spacer
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Accept All", type="primary", use_container_width=True):
            preferences = {
                "essential": True,
                "analytics": True,
                "marketing": True,
                "timestamp": str(dt.datetime.now())
            }
            save_consent(cookie_manager, preferences)
            
    with c2:
        if st.button("Save Selected", use_container_width=True):
            preferences = {
                "essential": True,
                "analytics": analytics,
                "marketing": marketing,
                "timestamp": str(dt.datetime.now())
            }
            save_consent(cookie_manager, preferences)

# 2. MAIN FUNCTION CALLED BY APP.PY
def show(cookie_manager):
    # If we already have consent in Session State, do nothing.
    if st.session_state.get("consent"):
        return

    # Check Browser Cookies (in case of reload)
    try:
        cookies = cookie_manager.get_all()
        if "nync_consent" in cookies:
            st.session_state.consent = cookies["nync_consent"]
            return
    except:
        pass

    # TRIGGER THE DIALOG
    # We use a session state flag to ensure it only opens once per run
    if not st.session_state.get("cookie_dialog_shown"):
        st.session_state.cookie_dialog_shown = True
        cookie_dialog(cookie_manager)

# 3. SAVE LOGIC
def save_consent(cookie_manager, preferences):
    # 1. Update Session State FIRST (Instant UI update)
    st.session_state.consent = preferences
    
    # 2. Save to Browser Cookie (Valid 1 Year)
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", preferences, expires_at=expires)
    
    # 3. Show Success
    st.success("Preferences Saved!")
    time.sleep(0.5)
    
    # 4. Rerun to close the dialog
    st.rerun()