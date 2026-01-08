import streamlit as st
import auth_utils as auth

def show(user, supabase):
    # --- HEADER REMOVED to fix the "Double Dashboard" glitch ---
    
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

    # 2. TEAM MANAGEMENT
    st.subheader("Your Teams")
    
    with st.expander("Create a New Team"):
        new_team_name = st.text_input("Team Name")
        if st.button("Create Team"):
            if auth.create_team(user.id, new_team_name):
                st.success(f"Team '{new_team_name}' created!")
                st.rerun()

    with st.expander("Join a Team"):
        code = st.text_input("Enter Invite Code (e.g. NYNC-1234)")
        if st.button("Join"):
            if auth.join_team_by_code(user.id, code):
                st.success("Joined team successfully!")
                st.rerun()
            else:
                st.error("Invalid code.")
    
    # 3. DANGER ZONE
    st.divider()
    if st.checkbox("Show Danger Zone"):
        st.warning("These actions are irreversible.")
        if st.button("Delete My Account", type="primary"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.rerun()
