import streamlit as st
import time
import datetime as dt

def show(cookie_manager):
    # 1. Check if consent is already given
    # We look for a specific cookie named "nync_consent"
    consent_data = cookie_manager.get("nync_consent")
    
    if consent_data:
        # If cookie exists, load it into session state and exit
        st.session_state.consent = consent_data
        return

    # 2. If no cookie, show the "Popup" (Container at the top)
    with st.container():
        st.info("🍪 **We value your privacy.** We use cookies to enhance your experience.")
        
        # Granular Options
        c1, c2, c3 = st.columns(3)
        with c1:
            st.checkbox("Essential (Required)", value=True, disabled=True, help="Login & Security cookies.")
        with c2:
            analytics = st.checkbox("Analytics", value=True, help="Helps us improve Nync features.")
        with c3:
            marketing = st.checkbox("Marketing & Offers", value=True, help="Allows us to show you relevant upgrade offers.")

        # Action Buttons
        b1, b2 = st.columns([1, 4])
        with b1:
            if st.button("Accept Selected", type="primary"):
                # Define the cookie value
                preference = {
                    "essential": True,
                    "analytics": analytics,
                    "marketing": marketing,
                    "timestamp": str(dt.datetime.now())
                }
                
                # Save Cookie (Valid for 365 days)
                expires = dt.datetime.now() + dt.timedelta(days=365)
                cookie_manager.set("nync_consent", preference, expires_at=expires)
                
                # Update Session State immediately so popup hides
                st.session_state.consent = preference
                st.rerun()
                
        with b2:
            if st.button("Reject Non-Essential"):
                # Minimal Consent
                preference = {
                    "essential": True,
                    "analytics": False,
                    "marketing": False,
                    "timestamp": str(dt.datetime.now())
                }
                expires = dt.datetime.now() + dt.timedelta(days=365)
                cookie_manager.set("nync_consent", preference, expires_at=expires)
                st.session_state.consent = preference
                st.rerun()
        
        st.divider()