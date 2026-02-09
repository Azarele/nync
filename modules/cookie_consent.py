import streamlit as st
import datetime as dt

def show(cookie_manager):
    # 1. Check if consent is already given
    consent_data = cookie_manager.get("nync_consent")
    if consent_data:
        st.session_state.consent = consent_data
        return

    # 2. CSS TO FLOAT THE CONTAINER (The "Magic")
    # This CSS targets the container that holds our specific marker class
    st.markdown("""
    <style>
        /* Target the vertical block containing our marker */
        div[data-testid="stVerticalBlock"]:has(div.cookie-consent-marker) {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px; /* Fixed small width */
            background-color: #111111;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.8);
            z-index: 1000000; /* On top of everything */
        }
        
        /* Adjust for mobile screens */
        @media (max-width: 600px) {
            div[data-testid="stVerticalBlock"]:has(div.cookie-consent-marker) {
                bottom: 0;
                right: 0;
                left: 0;
                width: 100%;
                border-radius: 12px 12px 0 0;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # 3. THE POPUP CONTENT
    # We use a container that the CSS above will "catch" and float
    with st.container():
        # This marker lets the CSS find this specific container
        st.markdown('<div class="cookie-consent-marker"></div>', unsafe_allow_html=True)
        
        st.write("#### 🍪 Privacy & Cookies")
        st.caption("We use cookies to improve Nync and offer personalized upgrades.")
        
        # Granular Options (Stacked for narrow window)
        with st.expander("Customize Preferences", expanded=False):
            st.checkbox("Essential (Required)", value=True, disabled=True)
            analytics = st.checkbox("Analytics", value=True, help="Helps us improve features.")
            marketing = st.checkbox("Marketing & Offers", value=True, help="Show relevant upgrade deals.")

        # Action Buttons
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Accept All", type="primary", use_container_width=True):
                save_preference(cookie_manager, True, True)
                
        with c2:
            if st.button("Reject Optional", use_container_width=True):
                save_preference(cookie_manager, False, False)

def save_preference(cookie_manager, analytics, marketing):
    preference = {
        "essential": True,
        "analytics": analytics,
        "marketing": marketing,
        "timestamp": str(dt.datetime.now())
    }
    # Save Cookie (Valid for 365 days)
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", preference, expires_at=expires)
    
    # Update Session & Reload
    st.session_state.consent = preference
    st.rerun()