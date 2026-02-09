import streamlit as st
import datetime as dt
import time

def show(cookie_manager):
    # 1. IMMEDIATE CHECK: If we already have consent in Session State, stop.
    # This ensures the UI disappears instantly after clicking, even if the cookie takes a moment.
    if st.session_state.get("consent"):
        return

    # 2. COOKIE CHECK: If cookie exists but not in session (e.g. page reload), load it.
    try:
        cookies = cookie_manager.get_all()
        if "nync_consent" in cookies:
            st.session_state.consent = cookies["nync_consent"]
            return
    except:
        pass

    # 3. CSS TO FORCE POSITIONING (The "Nuclear" Option)
    # We target the specific container by looking for our hidden marker ID.
    st.markdown("""
    <style>
        /* 1. Target the specific vertical block containing our ID marker */
        div[data-testid="stVerticalBlock"]:has(div#cookie-consent-anchor) {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            width: 350px !important;
            max-width: 90vw !important;
            background-color: #111111 !important;
            border: 1px solid #333 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0px 10px 40px rgba(0,0,0,0.9) !important;
            z-index: 1000000 !important;
            margin-bottom: 0px !important;
        }

        /* 2. Mobile Adjustment */
        @media (max-width: 600px) {
            div[data-testid="stVerticalBlock"]:has(div#cookie-consent-anchor) {
                bottom: 0px !important;
                right: 0px !important;
                left: 0px !important;
                width: 100% !important;
                border-radius: 12px 12px 0 0 !important;
                border-bottom: none !important;
            }
        }
        
        /* 3. Hide the anchor helper */
        div#cookie-consent-anchor { display: none; }
    </style>
    """, unsafe_allow_html=True)

    # 4. THE UI CONTENT
    # This container will be caught by the CSS above and floated.
    with st.container():
        # MARKER ID (Critical for CSS)
        st.markdown('<div id="cookie-consent-anchor"></div>', unsafe_allow_html=True)
        
        st.write("#### 🍪 Privacy Settings")
        st.caption("We use cookies to improve your experience.")
        
        with st.expander("Preferences", expanded=False):
            st.checkbox("Essential", value=True, disabled=True, key="ck_ess")
            analytics = st.checkbox("Analytics", value=True, key="ck_ana")
            marketing = st.checkbox("Marketing", value=True, key="ck_mkt")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Accept All", type="primary", use_container_width=True):
                confirm_consent(cookie_manager, True, True)
        
        with c2:
            if st.button("Reject", use_container_width=True):
                confirm_consent(cookie_manager, False, False)

def confirm_consent(cookie_manager, analytics, marketing):
    """
    Handles the save logic precisely to ensure UI feedback is instant.
    """
    preference = {
        "essential": True,
        "analytics": analytics,
        "marketing": marketing,
        "timestamp": str(dt.datetime.now())
    }
    
    # 1. Update Session State IMMEDIATELY
    # This hides the popup instantly on the next rerun, even if cookie isn't written yet.
    st.session_state.consent = preference
    
    # 2. Write the Cookie (Valid for 1 year)
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", preference, expires_at=expires)
    
    # 3. Toast Feedback
    st.toast("Preferences Saved!", icon="🍪")
    
    # 4. Slight delay to allow the cookie manager to communicate with browser
    time.sleep(0.5)
    
    # 5. Rerun to refresh the app state (UI will disappear because of step 1)
    st.rerun()