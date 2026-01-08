import streamlit as st
import streamlit.components.v1 as components
import auth_utils as auth

def show():
    # Use columns to constrain the width
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
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
            
            # --- GOOGLE POPUP LOGIC ---
            google_url = auth.get_google_url()
            if google_url:
                # We inject JS to open the popup. 
                # When the popup finishes (Supabase redirects it), the cookies are set on the domain.
                js_popup = f"""
                <script>
                function openGooglePopup() {{
                    window.open('{google_url}', 'nync_popup', 'width=500,height=600');
                }}
                </script>
                <div style="text-align: center;">
                    <button onclick="openGooglePopup()" style="
                        width: 100%;
                        background-color: transparent;
                        color: #4285F4;
                        padding: 8px;
                        border-radius: 4px;
                        border: 1px solid #4285F4;
                        font-family: sans-serif;
                        font-weight: 500;
                        cursor: pointer;
                        font-size: 16px;
                    ">
                        🔵 Sign in with Google
                    </button>
                </div>
                """
                components.html(js_popup, height=50)

        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                if st.form_submit_button("Create Account", use_container_width=True):
                    auth.signup_user(email, password)
