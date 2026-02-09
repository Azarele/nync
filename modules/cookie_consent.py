import streamlit as st
import datetime as dt
import time

def show(cookie_manager):
    # 1. Check if consent is already given
    # (We read the cookie directly to avoid showing popup if already accepted)
    consent_data = cookie_manager.get("nync_consent")
    if consent_data:
        st.session_state.consent = consent_data
        return

    # 2. CSS TO FLOAT ONLY THE INNERMOST CONTAINER
    # The selector :not(:has(...)) ensures we only target the container that holds the marker 
    # but DOES NOT hold another container. This targets the "leaf" node (our popup).
    st.markdown("""
    <style>
        /* 1. Target the specific vertical block containing our ID marker */
        /* We use 'div[data-testid="stVerticalBlock"]' which represents a st.container() */
        div[data-testid="stVerticalBlock"]:has(span#cookie-consent-marker):not(:has(div[data-testid="stVerticalBlock"])) {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px !important; /* Force small width */
            max-width: 90vw;
            background-color: #111111;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0px 10px 40px rgba(0,0,0,0.8);
            z-index: 999999; /* Always on top */
            gap: 1rem;
        }

        /* 2. Mobile Adjustment: Dock to bottom full width */
        @media (max-width: 600px) {
            div[data-testid="stVerticalBlock"]:has(span#cookie-consent-marker):not(:has(div[data-testid="stVerticalBlock"])) {
                bottom: 0;
                right: 0;
                left: 0;
                width: 100% !important;
                border-radius: 12px 12px 0 0;
                border-bottom: none;
                padding-bottom: 2rem;
            }
        }
        
        /* 3. Hide the anchor span itself */
        span#cookie-consent-marker {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    # 3. THE POPUP CONTENT
    # We use a container to group our elements. The CSS above targets THIS container.
    with st.container():
        # Unique Anchor ID for the CSS to find
        st.markdown('<span id="cookie-consent-marker"></span>', unsafe_allow_html=True)
        
        # Header
        c_text, c_icon = st.columns([5, 1])
        with c_text:
            st.write("#### 🍪 Privacy Settings")
            st.caption("We use cookies to enhance your experience.")
        with c_icon:
            st.write("🔒")
        
        # Options (Collapsible to keep it small)
        with st.expander("Customize", expanded=False):
            st.checkbox("Essential", value=True, disabled=True, key="ck_ess")
            analytics = st.checkbox("Analytics", value=True, key="ck_ana", help="Helps us improve.")
            marketing = st.checkbox("Marketing", value=True, key="ck_mkt", help="Upgrade offers.")

        st.write("") # Small spacer

        # Buttons
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Accept All", type="primary", use_container_width=True):
                save_preference(cookie_manager, True, True)
                
        with c2:
            if st.button("Reject Optional", use_container_width=True):
                save_preference(cookie_manager, False, False)

def save_preference(cookie_manager, analytics, marketing):
    """Saves the cookie and reloads the app"""
    preference = {
        "essential": True,
        "analytics": analytics,
        "marketing": marketing,
        "timestamp": str(dt.datetime.now())
    }
    
    # 1. Set the cookie (valid for 1 year)
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", preference, expires_at=expires)
    
    # 2. Update Session State immediately so UI reacts
    st.session_state.consent = preference
    
    # 3. CRITICAL: Wait for cookie to be written to browser
    # The cookie manager needs a split second to sync with the frontend before we reload.
    time.sleep(0.5)
    
    # 4. Reload the app to hide the popup
    st.rerun()