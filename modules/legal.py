import streamlit as st

def show():
    st.title("⚖️ Legal Information")
    st.write("Last updated: February 2026")
    
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

    # --- NEW COOKIE POLICY SECTION ---
    with st.expander("Cookie Policy"):
        st.write("""
        **1. What are cookies?**
        Cookies are small text files that are placed on your computer by websites that you visit. We use them to make our service work and to understand how you use it.

        **2. Types of Cookies We Use**
        * **Essential Cookies:** These are necessary for the website to function (e.g., keeping you logged in securely). You cannot opt-out of these.
        * **Analytics Cookies:** These allow us to count visits and traffic sources so we can measure and improve the performance of our site.
        * **Marketing Cookies:** These may be set through our site by us or advertising partners to build a profile of your interests and show you relevant offers (e.g., discounts on Nync plans).

        **3. Managing Preferences**
        You can change your cookie preferences at any time by visiting the **Settings** page and updating your choices under "Privacy Preferences".
        """)