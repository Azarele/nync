import streamlit as st
import auth_utils as auth
import base64

def show():
    # --- UI COMPRESSION CSS ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        div[data-testid="stTabs"] { margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2.5, 1])
    
    with c2:
        # 🚨 THE MANUAL NUDGE FIX 🚨
        try:
            with open("nync_marketing.png", "rb") as f: 
                img_data = base64.b64encode(f.read()).decode()
            
            # Added "transform: translateX(-12px);" to perfectly center the lightning bolt
            st.markdown(f"""
                <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; text-align: center;'>
                    <img src='data:image/png;base64,{img_data}' style='width: 140px; filter: brightness(0) invert(1); margin-bottom: 0px; transform: translateX(-12px);'>
                    <h1 style='margin: 0px; padding: 0px; font-size: 2.5rem;'>Nync</h1>
                    <p style='color: #888; font-size: 13px; margin: 0px 0px 10px 0px;'>Stop maximizing convenience. Start minimizing pain.</p>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("<h1 style='text-align: center; margin:0;'>⚡ Nync</h1>", unsafe_allow_html=True)
        
        # 2. TIGHTER GOOGLE COMPLIANCE TEXT
        st.markdown("""
        <p style='text-align: center; color: #6b7280; font-size: 12px; line-height: 1.4; max-width: 500px; margin: 0 auto 10px auto;'>
            Nync is a team scheduling and calendar synchronization application. 
            It securely connects to your Google or Microsoft calendar to automatically 
            detect conflicts and help your team find the best meeting times.
        </p>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                remember = st.checkbox("Remember Me", value=True, key="remember_me")
                
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.warning("⚠️ Please enter email and password.")
                    else:
                        if auth.login_user(email, password):
                            st.success("Logged in!")
            
            st.markdown("<hr style='margin: 10px 0px 15px 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            
            google_url = auth.get_google_url()
            if google_url:
                st.link_button("🔵 Sign in with Google", google_url, use_container_width=True)

        with tab2:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_pass")
                
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.warning("⚠️ Please enter email and password.")
                    else:
                        if auth.signup_user(email, password):
                            st.success("Account created!")

        # 4. COMPACT PRIVACY POLICY LINK
        st.markdown("""
        <div style='text-align: center; margin-top: 15px; font-size: 11px;'>
            <a href='https://nync.app/?nav=Legal' target='_self' style='color: #9ca3af; text-decoration: underline;'>Privacy Policy & Terms of Service</a>
        </div>
        """, unsafe_allow_html=True)