import streamlit as st
import auth_utils as auth

def show(user, supabase):
    # --- NO NAVBAR HERE (It's already in app.py) ---
    
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
            current_tier = profile.get('subscription_tier', 'free').title()
            st.write(f"**Current Plan:** {current_tier}")
    
    with c2:
        if st.button("Manage Subscription"):
            portal_url = auth.create_stripe_portal_session(user.email)
            if portal_url:
                st.link_button("Billing Portal", portal_url)
            else:
                st.info("No billing history found.")

    st.divider()

    # 2. TEAM MANAGEMENT
    st.subheader("Your Teams")
    
    # Create Team
    with st.expander("Create a New Team"):
        new_team_name = st.text_input("Team Name")
        if st.button("Create Team"):
            if auth.create_team(user.id, new_team_name):
                st.success(f"Team '{new_team_name}' created!")
                st.rerun()
            else:
                st.error("Failed to create team.")

    # Join Team
    with st.expander("Join a Team"):
        code = st.text_input("Enter Invite Code (e.g. NYNC-1234)")
        if st.button("Join"):
            if auth.join_team_by_code(user.id, code):
                st.success("Joined team successfully!")
                st.rerun()
            else:
                st.error("Invalid code.")

    # Team List & Webhooks
    my_teams = auth.get_user_teams(user.id)
    if my_teams:
        st.write("### Integrations")
        for name, tid in my_teams.items():
            with st.expander(f"🔌 {name} Settings"):
                st.write("Connect Nync to your chat app to send poll notifications.")
                
                # Fetch current webhook
                t_data = supabase.table('teams').select('webhook_url, invite_code').eq('id', tid).single().execute()
                current_hook = t_data.data.get('webhook_url', '')
                invite_code = t_data.data.get('invite_code', 'N/A')

                st.info(f"**Invite Code:** `{invite_code}`")

                new_hook = st.text_input("Discord/Teams Webhook URL", value=current_hook, key=f"wh_{tid}")
                
                if st.button("Save Webhook", key=f"btn_{tid}"):
                    supabase.table('teams').update({'webhook_url': new_hook}).eq('id', tid).execute()
                    st.success("Saved!")
    
    st.divider()
    
    # 3. DANGER ZONE
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.rerun()
