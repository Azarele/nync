import streamlit as st
import datetime as dt

def show(cookie_manager):
    # 1. Check if consent is already given
    consent_data = cookie_manager.get("nync_consent")
    if consent_data:
        st.session_state.consent = consent_data
        return

    # 2. CSS TO FLOAT THE CONTAINER (FIXED)
    # The selector now ensures we only target the LEAF container (the one without other containers inside it)
    # This prevents the style from accidentally shrinking your entire app.
    st.markdown("""
    <style>
        /* Target the specific vertical block containing our marker, but ensure it's not the main app wrapper */
        div[data-testid="stVerticalBlock"]:has(div.cookie-consent-marker):not(:has(div[data-testid="stVerticalBlock"])) {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            background-color: #111111;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0px 10px 40px rgba(0,0,0,0.9);
            z-index: 1000000;
        }
        
        /* Mobile adjustment */
        @media (max-width: 600px) {
            div[data-testid="stVerticalBlock"]:has(div.cookie-consent-marker):not(:has(div[data-testid="stVerticalBlock"])) {
                bottom: 0;
                right: 0;
                left: 0;
                width: 100%;
                border-radius: 12px 12px 0 0;
                border-bottom: none;
            }
        }
        
        /* styling for the marker to be invisible */
        div.cookie-consent-marker {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    # 3. THE POPUP CONTENT
    # We use a nested container to ensure our CSS targeting works perfectly
    with st.container():
        # This marker lets the CSS find this specific container
        st.markdown('<div class="cookie-consent-marker"></div>', unsafe_allow_html=True)
        
        c_text, c_icon = st.columns([4, 1])
        with c_text:
            st.write("#### 🍪 Privacy Settings")
            st.caption("We use cookies to enhance your experience and offer personalized upgrades.")
        with c_icon:
            st.markdown("<div style='font-size: 30px; text-align: right;'>🍪</div>", unsafe_allow_html=True)
        
        # Granular Options
        with st.expander("Customize Preferences", expanded=False):
            st.checkbox("Essential (Required)", value=True, disabled=True)
            analytics = st.checkbox("Analytics", value=True, help="Helps us improve features.")
            marketing = st.checkbox("Marketing & Offers", value=True, help="Show relevant upgrade deals.")

        st.write("") # Spacer

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