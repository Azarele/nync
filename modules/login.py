import streamlit as st
import auth_utils as auth

def show():
    # Center the container
    c1, c2, c3 = st.columns([1, 1.5, 1])
    
    with c2:
        st.header("⚡ Nync")
        st.caption("Stop playing Calendar Tetris.")
        st.write("") # Spacer

        # --- GOOGLE LOGIN (Top for easy access) ---
        google_url = auth.get_google_url()
        if google_url:
            # target="_self" forces it to open in the same tab
            st.markdown(f'''
                <a href="{google_url}" target="_self" style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    background-color: #1e1e1e;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    text-decoration: none;
                    border: 1px solid #444;
                    font-family: sans-serif;
                    font-weight: 500;
                    margin-bottom: 20px;
                ">
                    <span style="margin-right: 10px; font-size: 18px;">G</span> Sign in with Google
                </a>
            ''', unsafe_allow_html=True)

        st.markdown("--- OR ---")

        # --- EMAIL AUTH (Tabs for better UX) ---
        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

        # TAB 1: LOGIN
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                
                # "Enter" key will trigger this button automatically
                if st.form_submit_button("Log In", type="primary", use_container_width=True):
                    if not email or not password:
                        st.warning("Please enter email and password.")
                    else:
                        auth.login_user(email, password)

        # TAB 2: SIGN UP
        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email")
                new_pass = st.text_input("Password", type="password", key="signup_pass")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not new_email or not new_pass:
                        st.warning("Please enter email and password.")
                    else:
                        auth.signup_user(new_email, new_pass)
