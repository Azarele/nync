import streamlit as st
import pytz
import auth_utils as auth

def show(user, supabase):
    st.header("⚙️ Settings")

    # fetch profile
    profile = auth.get_user_profile(user.id)
    if not profile:
        st.error("Could not load profile")
        return

    # --- SUBSCRIPTION SECTION ---
    with st.expander("💳 Subscription & Billing", expanded=True):
        tier = profile.get('subscription_tier', 'free').capitalize()
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Current Plan:** {tier}")
            if tier.lower() == 'free':
                st.info("You are on the Free tier.")
            else:
                st.success(f"✅ You are an active {tier} member.")
        
        with c2:
            if tier.lower() != 'free':
                if st.button("Manage / Cancel", help="Open Stripe Billing Portal"):
                    url = auth.create_stripe_portal_session(user.email)
                    if url:
                        st.link_button("Go to Billing Portal", url, type="primary")
                    else:
                        st.error("Could not find billing history.")
            else:
                if st.button("Upgrade Plan"):
                    st.session_state.nav = "Pricing"
                    st.rerun()

    st.divider()

    # --- PROFILE SECTION ---
    with st.expander("👤 User Profile", expanded=True):
        st.write(f"**Email:** {user.email}")
        
        current_tz = profile.get('default_timezone', 'UTC')
        all_timezones = pytz.common_timezones
        
        try:
            idx = all_timezones.index(current_tz)
        except:
            idx = all_timezones.index('UTC')
            
        new_tz = st.selectbox("Default Timezone", all_timezones, index=idx)
        
        if st.button("Save Profile"):
            auth.update_user_timezone(user.id, new_tz)
            st.success("✅ Saved!")

    # --- TEAM SECTION ---
    st.divider()
    st.subheader("🏢 Your Teams")

    # 1. Create Team
    with st.form("create_team_form"):
        new_team_name = st.text_input("Create a New Team", placeholder="e.g. Marketing Squad")
        if st.form_submit_button("Create Team"):
            if new_team_name:
                if auth.create_team(user.id, new_team_name):
                    st.success(f"Team '{new_team_name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create team.")

    # 2. Join Team
    with st.form("join_team_form"):
        code = st.text_input("Join Team by Code", placeholder="NYNC-XXXX")
        if st.form_submit_button("Join Team"):
            if auth.join_team_by_code(user.id, code):
                st.success("Joined team!")
                st.rerun()
            else:
                st.error("Invalid code.")

    # 3. List Teams
    my_teams = auth.get_user_teams(user.id)
    if my_teams:
        st.write("Twitch Switch:")
        for name, tid in my_teams.items():
            if st.button(f"➡️ Switch to: {name}", key=f"switch_{tid}"):
                st.session_state.active_team = name
                st.session_state.active_team_id = tid
                st.rerun()

    st.divider()
    with st.expander("Danger Zone"):
        if st.button("❌ Delete Account"):
            if auth.delete_user_data(user.id):
                auth.supabase.auth.sign_out()
                st.session_state.session = None
                st.rerun()