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

# --- NEW FRAGMENT: Personal Working Hours ---
@st.fragment
def render_working_hours(user, supabase, profile):
    st.subheader("🕒 Personal Working Hours")
    st.caption("Tell Nync when you actually work. The Pain Engine will dynamically bend around your custom schedule.")
    
    start_hour = profile.get('work_start_hour') if profile.get('work_start_hour') is not None else 9
    end_hour = profile.get('work_end_hour') if profile.get('work_end_hour') is not None else 17
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            hours = st.slider(
                "Select your shift (24h format)", 
                min_value=0, max_value=24, 
                value=(start_hour, end_hour), 
                step=1,
                help="Your core working hours where taking a meeting causes 0 Pain."
            )
            st.caption(f"**Your Schedule:** {hours[0]}:00 to {hours[1]}:00 Local Time")
        
        with c2:
            st.write("")
            st.write("")
            if st.button("💾 Save Hours", type="primary", use_container_width=True):
                supabase.table('profiles').update({
                    'work_start_hour': hours[0],
                    'work_end_hour': hours[1]
                }).eq('id', user.id).execute()
                
                # Clear caches so the heatmap recalculates instantly!
                if hasattr(auth.get_user_profile, 'clear'): auth.get_user_profile.clear()
                if hasattr(auth.get_team_roster, 'clear'): auth.get_team_roster.clear()
                    
                st.success("Hours saved!")
                time.sleep(0.5)
                st.rerun(scope="fragment")

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
    if profile:
        render_working_hours(user, supabase, profile)
        st.divider()
        
    render_calendar_connections(user, supabase)
    st.divider()
    render_privacy_preferences()
    st.divider()
    
    # 3. DANGER ZONE & LOGOUT
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.session_state.clear_cookies = True
                st.rerun()
                
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Log Out", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()