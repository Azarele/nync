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

        st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Nync.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Stop maximizing convenience. Start minimizing pain.</p>", unsafe_allow_html=True)
        st.write("") 

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                
                if st.form_submit_button("Log In", type="primary", use_container_width=True):
                    auth.login_user(email, password)
            
            st.write("---")
            
            # --- GOOGLE LOGIN (SAME TAB - FIXED) ---
            google_url = auth.get_google_url()
            if google_url:
                # We use a DIV acting as a button with an anchor tag filling it entirely
                st.markdown(f"""
                    <a href="{google_url}" target="_self" style="text-decoration: none;">
                        <div style="
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            width: 100%;
                            background-color: transparent;
                            color: #4285F4;
                            padding: 10px;
                            border-radius: 4px;
                            border: 1px solid #4285F4;
                            font-family: sans-serif;
                            font-weight: 500;
                            cursor: pointer;
                            transition: background-color 0.2s;
                        ">
                            <span style="font-size: 18px; margin-right: 10px;">G</span> Sign in with Google
                        </div>
                    </a>
                """, unsafe_allow_html=True)

        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                if st.form_submit_button("Create Account", use_container_width=True):
                    auth.signup_user(email, password)
