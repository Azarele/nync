import streamlit as st
import auth_utils as auth
import datetime as dt
import time
import pytz  # <-- Added pytz library

def show(user, supabase, cookie_manager):
    st.header("⚙️ Settings")
    st.divider()

    # 1. PROFILE SECTION
    st.subheader("Profile")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.write(f"**Email:** {user.email}")
        
        # Get Profile Data
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
            if portal_url:
                st.link_button("Billing Portal", portal_url)
            else:
                st.info("No billing history found.")

    st.divider()

    # 2. CALENDAR CONNECTIONS
    st.subheader("📅 Calendar Connections")
    
    try:
        o_conn = supabase.table("calendar_connections").select("id, created_at").eq("user_id", user.id).eq("provider", "outlook").execute()
        outlook_connected = len(o_conn.data) > 0
        o_date = o_conn.data[0]['created_at'][:10] if outlook_connected else ""

        g_conn = supabase.table("calendar_connections").select("id, created_at").eq("user_id", user.id).eq("provider", "google").execute()
        google_connected = len(g_conn.data) > 0
        g_date = g_conn.data[0]['created_at'][:10] if google_connected else ""
    except:
        outlook_connected = False
        google_connected = False

    if outlook_connected:
        st.success(f"✅ Outlook Connected (since {o_date})")
        if st.button("Disconnect Outlook"):
            supabase.table("calendar_connections").delete().eq("user_id", user.id).eq("provider", "outlook").execute()
            st.rerun()
    else:
        ms_url = auth.get_microsoft_url(user.id)
        st.link_button("🔌 Connect Outlook", ms_url, type="primary")

    st.write("") 

    if google_connected:
        st.success(f"✅ Google Calendar Connected (since {g_date})")
        st.caption("We have permission to scan your busy slots.")
    else:
        st.info("To connect Google Calendar, please Log Out and Log In again using the Google button.")

    st.divider()

    # 3. PRIVACY & COOKIES
    st.subheader("🍪 Privacy Preferences")
    
    current_consent = st.session_state.get('consent')
    is_accepted = (current_consent == "accepted")
    
    with st.expander("Manage Cookie Consent", expanded=False):
        st.write("Update your cookie preferences here.")
        
        with st.form("cookie_update_form"):
            st.checkbox("Essential Cookies (Required)", value=True, disabled=True)
            new_consent = st.checkbox("Analytics & Marketing Offers", value=is_accepted)
            
            if st.form_submit_button("Save Preferences"):
                val = "accepted" if new_consent else "declined"
                st.session_state.save_consent_val = val
                st.success("Preferences Saved!")
                time.sleep(0.5)
                st.rerun()

    st.divider()

    # 4. TEAM MANAGEMENT
    st.subheader("Team Management")
    c_create, c_join = st.columns(2)
    
    with c_create:
        with st.expander("Create a New Team"):
            new_team_name = st.text_input("Team Name")
            if st.button("Create Team"):
                if auth.create_team(user.id, new_team_name):
                    st.success(f"Team '{new_team_name}' created!")
                    st.rerun()

    with c_join:
        with st.expander("Join a Team"):
            code = st.text_input("Enter Invite Code")
            if st.button("Join"):
                if auth.join_team_by_code(user.id, code):
                    st.success("Joined team successfully!")
                    st.rerun()
                else:
                    st.error("Invalid code.")

    st.divider()

    # 5. MY TEAMS
    st.subheader("My Teams")
    
    my_teams = auth.get_user_teams(user.id)
    
    if not my_teams:
        st.info("You are not in any teams yet.")
    else:
        team_names = list(my_teams.keys())
        selected_team_name = st.selectbox("Select a Team to Manage", team_names)
        selected_tid = my_teams[selected_team_name]
        
        try:
            role_check = supabase.table('team_members').select('role').eq('team_id', selected_tid).eq('user_id', user.id).execute()
            my_role = role_check.data[0]['role'] if role_check.data else 'member'
        except:
            my_role = 'member'
            
        try:
            t_data = supabase.table('teams').select('invite_code, webhook_url').eq('id', selected_tid).single().execute()
            invite_code = t_data.data.get('invite_code', 'N/A')
            webhook = t_data.data.get('webhook_url', '')
        except:
            invite_code = "Error"
            webhook = ""

        st.markdown(f"#### 🛡️ {selected_team_name} <span style='font-size:14px; background:#444; padding:2px 8px; border-radius:4px;'>{my_role.upper()}</span>", unsafe_allow_html=True)
        
        c_code, c_settings = st.columns([1, 1.5])
        
        with c_code:
            st.caption("Invite Code")
            st.code(invite_code, language=None)
            
            st.caption("Invite Link")
            invite_link = f"https://nyncapp.streamlit.app/?invite={invite_code}"
            st.code(invite_link, language=None)
            
        with c_settings:
            # --- REBUILT: TEAM ROSTER MANAGEMENT ---
            with st.expander("👥 Team Roster", expanded=True):
                try:
                    roster_data = supabase.table('team_members').select('id, user_id, role, ghost_name, ghost_email, ghost_timezone, profiles(email, default_timezone)').eq('team_id', selected_tid).execute()
                    
                    if roster_data.data:
                        # Grab all valid timezones from pytz
                        ALL_TZS = pytz.all_timezones
                        
                        for member in roster_data.data:
                            row_id = member.get('id')
                            m_user_id = member.get('user_id')
                            m_role = member.get('role', 'member')
                            is_ghost = (m_user_id is None)
                            
                            # Parse User Info
                            if is_ghost:
                                m_name = member.get('ghost_name') or "Dummy"
                                m_email = member.get('ghost_email') or ""
                                m_tz = member.get('ghost_timezone') or "UTC"
                                display_name = f"👻 {m_name}" + (f" ({m_email})" if m_email else "")
                            else:
                                prof = member.get('profiles') or {}
                                m_email = prof.get('email', 'Unknown User')
                                m_tz = prof.get('default_timezone') or "UTC"
                                display_name = f"👤 {m_email}"
                                
                            c1, c2, c3 = st.columns([2.5, 2, 1])
                            
                            if m_user_id == user.id:
                                c1.markdown(f"**{display_name}** (You)")
                            else:
                                c1.markdown(f"**{display_name}**")
                                
                            if my_role == 'admin':
                                # Timezone Selector - Includes fallback just in case database has a weird legacy timezone
                                tz_options = ALL_TZS if m_tz in ALL_TZS else ALL_TZS + [m_tz]
                                new_tz = c2.selectbox("TZ", tz_options, index=tz_options.index(m_tz), key=f"tz_{row_id}", label_visibility="collapsed")
                                
                                if new_tz != m_tz:
                                    auth.update_member_timezone(row_id, m_user_id, new_tz, is_ghost)
                                    st.rerun()
                                    
                                # Kick Button
                                if m_user_id != user.id:
                                    if c3.button("Kick", key=f"kick_{row_id}", type="secondary", use_container_width=True):
                                        if auth.remove_team_member_by_row(row_id, selected_tid, user.id):
                                            st.toast(f"Removed member.")
                                            time.sleep(0.5)
                                            st.rerun()
                            else:
                                c2.write(f"🌍 {m_tz}")
                                
                        # --- ADD DUMMY MEMBER FORM ---
                        if my_role == 'admin':
                            st.markdown("---")
                            st.markdown("##### ➕ Add Dummy Member")
                            with st.form(f"add_ghost_{selected_tid}", clear_on_submit=True):
                                col1, col2, col3 = st.columns(3)
                                g_name = col1.text_input("Name", placeholder="John Doe")
                                g_email = col2.text_input("Email", placeholder="(Optional)")
                                
                                # Default to UTC, but load all timezones
                                default_tz_index = ALL_TZS.index("UTC") if "UTC" in ALL_TZS else 0
                                g_tz = col3.selectbox("Timezone", ALL_TZS, index=default_tz_index)
                                
                                if st.form_submit_button("Add Dummy"):
                                    if g_name:
                                        auth.add_ghost_member(selected_tid, g_name, g_email, g_tz, user.id)
                                        st.success("Dummy added!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.warning("Name is required.")
                except Exception as e:
                    st.error(f"Could not load roster: {e}")
            
            # --- WEBHOOK SETTINGS ---
            if my_role == 'admin':
                with st.expander("🔌 Webhook Settings"):
                    st.caption("Send notifications to Discord/Teams")
                    new_hook = st.text_input("Webhook URL", value=webhook, key=f"wh_{selected_tid}")
                    if st.button("Save Webhook", key=f"save_{selected_tid}"):
                        supabase.table('teams').update({'webhook_url': new_hook}).eq('id', selected_tid).execute()
                        st.success("Saved!")
            else:
                st.info("🔒 You must be an **Admin** to edit team settings.")

            # --- LEAVE TEAM ---
            st.write("")
            if st.button("Leave Team", type="secondary", key=f"leave_{selected_tid}"):
                if auth.leave_team(selected_tid, user.id):
                    st.toast("You have left the team.")
                    time.sleep(0.5)
                    st.rerun()
    
    st.divider()
    
    # 6. DANGER ZONE
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.session_state.clear_cookies = True
                st.rerun()