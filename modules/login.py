import streamlit as st
import auth_utils as auth

def show():
    # Use columns to constrain the width of the login form
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        # --- LOGO CENTERING ---
        # Create 3 sub-columns and place image in the middle one to center it.
        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc2:
            try:
                # use_container_width makes it fill the middle column
                st.image("nync_marketing.png", use_container_width=True) 
            except:
                st.header("⚡")

        # TEXT BELOW LOGO
        st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Nync.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Stop maximizing convenience. Start minimizing pain.</p>", unsafe_allow_html=True)
        
        st.write("") # Spacer

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        # --- TAB 1: SIGN IN ---
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                
                # prevent submission if empty
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.warning("Please enter your email and password.")
                    else:
                        auth.login_user(email, password)
            
            st.write("---")
            
            # GOOGLE LOGIN (Standard Link Button)
            google_url = auth.get_google_url()
            if google_url:
                st.link_button("🔵 Sign in with Google", google_url, use_container_width=True)

        # --- TAB 2: SIGN UP ---
        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.warning("Please enter your email and password.")
                    else:
                        auth.signup_user(email, password)
