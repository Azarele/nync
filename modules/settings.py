import streamlit as st
import auth_utils as auth

def show(user, supabase):
    # --- NO NAV CODE HERE (Handled by app.py) ---
    
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

    # 2. CALENDAR CONNECTIONS (RESTORED)
    st.subheader("📅 Calendar Connections")
    
    # Check if Outlook is already connected via database
    try:
        conn = supabase.table("calendar_connections").select("id").eq("user_id", user.id).eq("provider", "outlook").execute()
        is_connected = len(conn.data) > 0
    except:
        is_connected = False

    if is_connected:
        st.success("✅ Outlook Calendar Connected")
        if st.button("Disconnect Outlook"):
            supabase.table("calendar_connections").delete().eq("user_id", user.id).eq("provider", "outlook").execute()
            st.rerun()
    else:
        st.info("Connect your Outlook calendar to enable the Scheduler.")
        ms_url = auth.get_microsoft_url()
        # Using link_button for external redirect
        st.link_button("🔌 Connect Outlook Calendar", ms_url, use_container_width=True)

    st.divider()

    # 3. TEAM MANAGEMENT (Create / Join)
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

    # 4. MY TEAMS (Dropdown Style)
    st.subheader("My Teams")
    
    my_teams = auth.get_user_teams(user.id)
    
    if not my_teams:
        st.info("You are not in any teams yet.")
    else:
        # Create a dropdown with team names
        team_names = list(my_teams.keys())
        selected_team_name = st.selectbox("Select a Team to Manage", team_names)
        
        # Get the ID of the selected team
        selected_tid = my_teams[selected_team_name]
        
        # Fetch details ONLY for the selected team
        try:
            t_data = supabase.table('teams').select('invite_code, webhook_url').eq('id', selected_tid).single().execute()
            invite_code = t_data.data.get('invite_code', 'N/A')
            webhook = t_data.data.get('webhook_url', '')
        except:
            invite_code = "Error"
            webhook = ""

        # Display Details in a Clean Card
        st.markdown(f"#### 🛡️ {selected_team_name}")
        
        c_code, c_settings = st.columns([1, 1.5])
        
        with c_code:
            st.caption("Invite Code")
            st.code(invite_code, language=None)
            st.caption("Share this code with members to let them join.")
        
        with c_settings:
            with st.expander("🔌 Webhook Settings", expanded=True):
                st.caption("Send notifications to Discord/Teams")
                new_hook = st.text_input("Webhook URL", value=webhook, key=f"wh_{selected_tid}")
                if st.button("Save Webhook", key=f"save_{selected_tid}"):
                    supabase.table('teams').update({'webhook_url': new_hook}).eq('id', selected_tid).execute()
                    st.success("Saved!")
    
    st.divider()
    
    # 5. DANGER ZONE
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.rerun()