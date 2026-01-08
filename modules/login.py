import streamlit as st
import auth_utils as auth

def show():
    # Center the login box
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.header("⚡ Nync")
        st.write("Stop playing Calendar Tetris.")
        
        # --- GOOGLE LOGIN (FIXED: SAME TAB) ---
        google_url = auth.get_google_url()
        if google_url:
            # We use HTML to force target="_self" so it doesn't open a new tab
            st.markdown(f'''
                <a href="{google_url}" target="_self" style="
                    display: inline-block;
                    width: 100%;
                    background-color: #2e2e2e;
                    color: white;
                    text-align: center;
                    padding: 10px 0px;
                    border-radius: 8px;
                    text-decoration: none;
                    border: 1px solid #444;
                    font-family: sans-serif;
                    margin-bottom: 15px;
                ">
                    Sign in with Google
                </a>
            ''', unsafe_allow_html=True)

        st.markdown("--- OR ---")

        # --- EMAIL LOGIN ---
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            b1, b2 = st.columns(2)
            with b1:
                if st.form_submit_button("Log In", use_container_width=True):
                    auth.login_user(email, password)
            with b2:
                if st.form_submit_button("Sign Up", use_container_width=True):
                    auth.signup_user(email, password)
