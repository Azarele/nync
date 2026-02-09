import streamlit as st
import datetime as dt
import time

def show(cookie_manager):
    # 1. Check if consent is already given
    # We read the cookie directly to avoid showing popup if already accepted
    try:
        consent_data = cookie_manager.get("nync_consent")
        if consent_data:
            st.session_state.consent = consent_data
            return
    except:
        pass # If error reading, show popup just in case

    # 2. CREATE A 'FLOATABLE' CONTAINER
    # We use st.columns(1) because it creates a unique 'stColumn' wrapper in the HTML
    # that is easier to target with CSS than a generic container.
    popup_col = st.columns(1)[0]
    
    with popup_col:
        # Marker ID for CSS to find
        st.markdown('<div id="cookie-popup-anchor"></div>', unsafe_allow_html=True)
        
        with st.container():
            c_icon, c_text = st.columns([1, 5])
            with c_icon:
                st.write("🍪")
            with c_text:
                st.write("**Privacy Settings**")
                st.caption("We use cookies to improve your experience.")
            
            with st.expander("Preferences", expanded=False):
                st.checkbox("Essential", value=True, disabled=True, key="ck_ess")
                analytics = st.checkbox("Analytics", value=True, key="ck_ana")
                marketing = st.checkbox("Marketing", value=True, key="ck_mkt")

            # Buttons
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Accept All", key="btn_accept", type="primary", use_container_width=True):
                    save_preference(cookie_manager, True, True)
            with b2:
                if st.button("Reject", key="btn_reject", use_container_width=True):
                    save_preference(cookie_manager, False, False)

    # 3. CSS TO FLOAT THE COLUMN
    st.markdown("""
    <style>
        /* Target the specific column containing our anchor ID */
        div[data-testid="stColumn"]:has(div#cookie-popup-anchor) {
            position: fixed;
            bottom: 1rem;
            right: 1rem;
            width: 320px !important;
            max-width: 90vw;
            background-color: #0e0e0e; /* Dark background */
            border: 1px solid #333;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            z-index: 999999; /* Ensure it's on top */
            flex: none !important; /* Stop Streamlit from stretching it */
        }
        
        /* Hide the anchor helper */
        div#cookie-popup-anchor { display: none; }

        /* Mobile Adjustments */
        @media (max-width: 600px) {
            div[data-testid="stColumn"]:has(div#cookie-popup-anchor) {
                left: 1rem;
                right: 1rem;
                bottom: 1rem;
                width: auto !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def save_preference(cookie_manager, analytics, marketing):
    """Saves the preference cookie and reloads."""
    preference = {
        "essential": True,
        "analytics": analytics,
        "marketing": marketing,
        "timestamp": str(dt.datetime.now())
    }
    
    # 1. Set expiration (1 year)
    expires = dt.datetime.now() + dt.timedelta(days=365)
    
    # 2. Write Cookie
    cookie_manager.set("nync_consent", preference, expires_at=expires)
    
    # 3. Update Session State (Immediate UI feedback)
    st.session_state.consent = preference
    
    # 4. Success Message
    st.toast("Preferences Saved!")
    
    # 5. WAIT for Browser Sync (Critical for button to 'work')
    time.sleep(1) 
    
    # 6. Reload
    st.rerun()