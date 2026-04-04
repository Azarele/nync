import streamlit as st
import auth_utils as auth

def show():
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc2:
            try:
                st.image("nync_marketing.png", width=50) 
            except:
                st.header("⚡")

        # 1. FIX THE APP NAME ERROR (Google Verification)
        st.markdown("<h1 style='text-align: center; margin-top: 0px;'>Nync</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Stop maximizing convenience. Start minimizing pain.</p>", unsafe_allow_html=True)
        
        # 2. FIX THE APP PURPOSE ERROR (Google Verification)
        st.markdown("""
        <p style='text-align: center; color: #6b7280; font-size: 14px; max-width: 500px; margin: 0 auto 20px auto;'>
            Nync is a team scheduling and calendar synchronization application. 
            It securely connects to your Google or Microsoft calendar to automatically 
            detect conflicts and help your team find the best meeting times.
        </p>
        """, unsafe_allow_html=True)
        
        st.write("") 

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
            
            st.write("---")
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

        # 3. FIX THE PRIVACY POLICY LINK ERROR (Google Verification)
        st.markdown("""
        <div style='text-align: center; margin-top: 30px; font-size: 12px;'>
            <a href='https://nync.app/?nav=Legal' target='_self' style='color: #9ca3af; text-decoration: underline;'>Privacy Policy & Terms of Service</a>
        </div>
        """, unsafe_allow_html=True)