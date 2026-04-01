import streamlit as st
import auth_utils as auth
import time

@st.fragment
def render_calendar_connections(user, supabase):
    st.subheader("📅 Calendar Connections")
    try:
        o_conn = supabase.table("calendar_connections").select("id, created_at").eq("user_id", user.id).eq("provider", "outlook").execute()
        outlook_connected = len(o_conn.data) > 0
        o_date = o_conn.data[0]['created_at'][:10] if outlook_connected else ""

        g_conn = supabase.table("calendar_connections").select("id, created_at").eq("user_id", user.id).eq("provider", "google").execute()
        google_connected = len(g_conn.data) > 0
        g_date = g_conn.data[0]['created_at'][:10] if google_connected else ""
    except:
        outlook_connected, google_connected = False, False

    if outlook_connected:
        st.success(f"✅ Outlook Connected (since {o_date})")
        if st.button("Disconnect Outlook", key="disc_out"):
            supabase.table("calendar_connections").delete().eq("user_id", user.id).eq("provider", "outlook").execute()
            st.rerun(scope="fragment")
    else:
        ms_url = auth.get_microsoft_url(user.id)
        st.link_button("🔌 Connect Outlook", ms_url, type="primary")

    st.write("") 

    if google_connected:
        st.success(f"✅ Google Calendar Connected (since {g_date})")
    else:
        st.info("To connect Google Calendar, please Log Out and Log In again using the Google button.")

@st.fragment
def render_privacy_preferences():
    st.subheader("🍪 Privacy Preferences")
    current_consent = st.session_state.get('consent')
    is_accepted = (current_consent == "accepted")
    
    with st.expander("Manage Cookie Consent", expanded=False):
        with st.form("cookie_update_form"):
            st.checkbox("Essential Cookies (Required)", value=True, disabled=True)
            new_consent = st.checkbox("Analytics & Marketing Offers", value=is_accepted)
            if st.form_submit_button("Save Preferences"):
                st.session_state.save_consent_val = "accepted" if new_consent else "declined"
                st.success("Preferences Saved!")
                time.sleep(0.5)
                st.rerun(scope="fragment")

def show(user, supabase, cookie_manager):
    st.header("⚙️ Personal Settings")
    st.divider()

    # 1. PROFILE SECTION (Full refresh required for billing)
    st.subheader("Profile")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write(f"**Email:** {user.email}")
        
        profile = auth.get_user_profile(user.id)
        if profile:
            tier = profile.get('subscription_tier', 'free').upper()
            color = "#666"
            if tier == "SQUAD": color = "#ff8c00"
            if tier == "GUILD": color = "#1e90ff"
            if tier == "EMPIRE": color = "#9932cc"
            st.markdown(f"**Current Plan:** <span style='background-color:{color}; color:white; padding:2px 8px; border-radius:4px;'>{tier}</span>", unsafe_allow_html=True)
    
    with c2:
        if st.button("Manage Subscription"):
            portal_url = auth.create_stripe_portal_session(user.email)
            if portal_url: st.link_button("Billing Portal", portal_url)
            else: st.info("No billing history found.")

    st.divider()

    # 2. RENDER FRAGMENTS (High-speed UI)
    render_calendar_connections(user, supabase)
    st.divider()
    render_privacy_preferences()
    st.divider()
    
    # 3. DANGER ZONE
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.session_state.clear_cookies = True
                st.rerun()