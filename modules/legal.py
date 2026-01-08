import streamlit as st

def show():
    st.title("Legal & Compliance")
    
    tab1, tab2 = st.tabs(["🔒 Privacy Policy", "📜 Terms of Service"])
    
    # --- PRIVACY POLICY ---
    with tab1:
        st.markdown("""
        ### Privacy Policy for Nync
        **Last Updated:** January 2026

        #### 1. Introduction
        Nync ("we", "our", or "us") respects your privacy. This policy explains how we handle your data when you use our team scheduling application. By using Nync, you agree to the collection and use of information in accordance with this policy.

        #### 2. Data We Collect
        We collect only the information necessary to provide our scheduling service:
        * **Account Information:** Email address and name (provided via Google Sign-In or manual sign-up).
        * **Calendar Data:** If you connect Outlook/Microsoft, we store secure access tokens to read your calendar availability. We process your event times to calculate "pain scores," but we do not store the specific details (titles, descriptions) of your private meetings permanently in our database.
        * **Team Data:** Names and timezones of team members you create.

        #### 3. Cookies
        We use **strictly necessary cookies** to keep you logged in.
        * `sb_access_token` & `sb_refresh_token`: Used to maintain your secure session with our database (Supabase) so you do not have to log in every time you refresh the page.
        * We do not use cookies for advertising, tracking, or analytics.

        #### 4. Third-Party Services
        We trust the following providers to power our infrastructure:
        * **Supabase:** For secure database hosting and authentication.
        * **Microsoft Azure:** For Outlook Calendar integration.
        * **Google Cloud:** For Google Sign-In.

        #### 5. Your Rights
        You may request the deletion of your account and all associated data at any time by contacting us. Connecting your calendar is optional and can be revoked via your Microsoft Account settings or the "Settings" page in Nync.

        #### 6. Contact Us
        For privacy questions, please contact: [Your Support Email Here]
        """)

    # --- TERMS OF SERVICE ---
    with tab2:
        st.markdown("""
        ### Terms of Service

        #### 1. Acceptance of Terms
        By accessing or using Nync, you agree to be bound by these Terms. If you disagree with any part of the terms, you may not access the service.

        #### 2. Description of Service
        Nync is a scheduling optimization tool designed to distribute meeting times equitably across time zones.

        #### 3. Disclaimer
        The service is provided on an "AS IS" and "AS AVAILABLE" basis. We do not warrant that the service will be uninterrupted or error-free. We are not responsible for missed meetings or scheduling conflicts resulting from the use of our algorithmic suggestions.

        #### 4. User Responsibilities
        You are responsible for safeguarding the password that you use to access the service. You agree not to disclose your password to any third party.

        #### 5. Changes
        We reserve the right to modify or replace these Terms at any time.
        """)