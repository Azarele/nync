import streamlit as st

def show():
    # --- HEADER REMOVED ---
    
    st.title("⚖️ Legal Information")
    st.write("Last updated: January 2026")
    
    with st.expander("Terms of Service"):
        st.write("""
        **1. Introduction**
        Welcome to Nync. By using our website and services, you agree to be bound by these terms.
        
        **2. Use of Service**
        You agree to use Nync only for lawful purposes. You must not use our service to send spam or harass other users.
        
        **3. Accounts**
        You are responsible for maintaining the security of your account and password. Nync cannot and will not be liable for any loss or damage from your failure to comply with this security obligation.
        
        **4. Termination**
        We may terminate your access to the Service, without cause or notice, which may result in the forfeiture and destruction of all information associated with you.
        """)

    with st.expander("Privacy Policy"):
        st.write("""
        **1. Information Collection**
        We collect information you provide directly to us, such as when you create an account, update your profile, or communicate with us. This includes your email address and calendar data (if connected).
        
        **2. Calendar Data**
        We only access your calendar to calculate "Busy" times. We do not store meeting details, descriptions, or attendee lists permanently.
        
        **3. Data Security**
        We take reasonable measures to help protect information about you from loss, theft, misuse and unauthorized access.
        """)
