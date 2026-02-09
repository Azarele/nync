import streamlit as st
import datetime as dt
import time

def show(cookie_manager):
    # 1. IMMEDIATE CHECK: If consent is already in Session State, DO NOT RENDER.
    # This ensures the popup disappears instantly after clicking, preventing the "it does nothing" feel.
    if st.session_state.get("consent") is not None:
        return

    # 2. BROWSER COOKIE CHECK: If not in session (e.g., fresh reload), check browser cookies.
    # We wrap this in try/except because cookie_manager can be flaky during initialization.
    try:
        cookies = cookie_manager.get_all()
        if "nync_consent" in cookies and cookies["nync_consent"]:
            st.session_state.consent = cookies["nync_consent"]
            return
    except:
        pass

    # 3. CSS TO FORCE FLOATING POSITION (The "Nuclear" Option)
    # We use !important to override Streamlit's default top-down flow.
    # This targets the specific container that holds our 'cookie-anchor' ID.
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"]:has(div#cookie-anchor) {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            left: auto !important;
            top: auto !important;
            width: 350px !important;
            max-width: 90vw !important;
            background-color: #0e0e0e !important;
            border: 1px solid #333 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            z-index: 999999 !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8) !important;
            margin-bottom: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
        }

        /* Mobile Adjustment */
        @media (max-width: 600px) {
            div[data-testid="stVerticalBlock"]:has(div#cookie-anchor) {
                bottom: 0 !important;
                right: 0 !important;
                left: 0 !important;
                width: 100% !important;
                border-radius: 12px 12px 0 0 !important;
                border-bottom: none !important;
            }
        }
        
        /* Hide the anchor helper */
        div#cookie-anchor { display: none; }
    </style>
    """, unsafe_allow_html=True)

    # 4. THE POPUP CONTENT
    # We use a container to wrap the content. The CSS above finds this container.
    with st.container():
        # CSS Anchor (Critical)
        st.markdown('<div id="cookie-anchor"></div>', unsafe_allow_html=True)
        
        st.write("#### 🍪 Privacy Settings")
        st.caption("We use cookies to improve your experience and show relevant upgrades.")
        
        with st.expander("Customize Preferences", expanded=False):
            st.checkbox("Essential", value=True, disabled=True, key="ck_ess")
            analytics = st.checkbox("Analytics", value=True, key="ck_ana")
            marketing = st.checkbox("Marketing", value=True, key="ck_mkt")

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
            if st.button("Reject", use_container_width=True):
                # We use the checkbox states for granular rejection
                preferences = {
                    "essential": True,
                    "analytics": st.session_state.get("ck_ana", False),
                    "marketing": st.session_state.get("ck_mkt", False),
                    "timestamp": str(dt.datetime.now())
                }
                save_consent(cookie_manager, preferences)

def save_consent(cookie_manager, preferences):
    """Saves consent to session and browser, then reloads."""
    # 1. Update Session State FIRST (Instant Feedback)
    # This guarantees the popup logic (step 1 above) will hide the box on the next run.
    st.session_state.consent = preferences
    
    # 2. Write to Browser Cookie (Persistence)
    try:
        expires = dt.datetime.now() + dt.timedelta(days=365)
        cookie_manager.set("nync_consent", preferences, expires_at=expires)
    except Exception as e:
        print(f"Cookie Error: {e}")
    
    # 3. Toast Message
    st.toast("Preferences Saved!", icon="🍪")
    
    # 4. Wait for Sync (Critical)
    # Give the browser 0.5s to actually write the cookie before we kill the page
    time.sleep(0.5)
    
    # 5. Rerun
    st.rerun()