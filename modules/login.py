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
        
        st.write("") 

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        # --- TAB 1: LOG IN ---
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                
                # Prevent "Login Failed" error on empty submit
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.warning("Please enter your email and password.")
                    else:
                        auth.login_user(email, password)
            
            st.write("---")
            
            # --- GOOGLE LOGIN (FORCED SAME TAB) ---
            google_url = auth.get_google_url()
            if google_url:
                # This HTML button looks exactly like a Streamlit button but keeps you in the same tab
                st.markdown(f"""
                    <a href="{google_url}" target="_self" style="text-decoration: none;">
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            background-color: transparent;
                            color: #ffffff;
                            padding: 0.5rem 1rem;
                            border-radius: 0.5rem;
                            border: 1px solid rgba(250, 250, 250, 0.2);
                            font-family: 'Source Sans Pro', sans-serif;
                            font-weight: 400;
                            cursor: pointer;
                            transition: border-color 0.2s, color 0.2s;
                        ">
                            <span style="margin-right: 8px;">🔵</span> Sign in with Google
                        </div>
                    </a>
                """, unsafe_allow_html=True)

        # --- TAB 2: SIGN UP ---
        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not email or not password:
                        st.warning("Please enter your email and password.")
                    else:
                        auth.signup_user(email, password)
