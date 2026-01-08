import streamlit as st
import auth_utils as auth

def show():
    # Use columns to constrain the width of the login form
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        # --- LOGO CENTERING ---
        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc2:
            try:
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
                
                # --- NEW: REMEMBER ME CHECKBOX ---
                remember_me = st.checkbox("Remember Me") 
                
                if st.form_submit_button("Log In", type="primary", use_container_width=True):
                    # Pass the checkbox value to the auth function
                    auth.login_user(email, password, remember=remember_me)
            
            st.write("---")
            
            # GOOGLE LOGIN
            google_url = auth.get_google_url()
            if google_url:
                st.markdown(f'''
                    <a href="{google_url}" target="_self" style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 100%;
                        background-color: transparent;
                        color: #4285F4;
                        padding: 8px;
                        border-radius: 4px;
                        text-decoration: none;
                        border: 1px solid #4285F4;
                        font-family: sans-serif;
                        font-weight: 500;
                        transition: all 0.2s;
                    ">
                        🔵 Sign in with Google
                    </a>
                ''', unsafe_allow_html=True)

        # --- TAB 2: SIGN UP ---
        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    auth.signup_user(email, password)
