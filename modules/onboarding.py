import streamlit as st
import auth_utils as auth
from streamlit_javascript import st_javascript
import time

def show(user, supabase, has_cal, has_teams):
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>Welcome to Nync. ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a1a1aa; font-size: 1.1rem;'>Let's get your account set up so you can start scheduling pain-free.</p>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)

    # ==========================================
    # --- AUTO-DETECT TIMEZONE SAFELY ---
    # ==========================================
    try:
        profile = auth.get_user_profile(user.id)
        current_tz = profile.get('default_timezone') if profile else None
        
        if not current_tz or current_tz == 'UTC':
            client_tz = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
            
            if client_tz and client_tz != 0 and client_tz != "0":
                # Save to database
                supabase.table('profiles').update({'default_timezone': client_tz}).eq('id', user.id).execute()
                
                # Safely clear the cache so the app pulls the new timezone
                if hasattr(auth.get_user_profile, 'clear'):
                    auth.get_user_profile.clear()
                    
                st.toast(f"🌍 Auto-detected your timezone: {client_tz}", icon="✅")
                time.sleep(0.5)
                st.rerun() # Immediately refresh to lock in the timezone and remove the JS evaluation
    except Exception as e:
        pass # Fail silently so onboarding is never blocked
        
    # ==========================================
    # --- RENDER ONBOARDING STEPS ---
    # ==========================================
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        with st.container(border=True):
            
            # --- STEP 1: CALENDAR ---
            if has_cal:
                st.markdown("### ✅ 1. Calendar Synced")
                st.caption("We have access to your busy slots.")
            else:
                st.markdown("### 🗓️ 1. Sync your Calendar")
                st.caption("Connect your work calendar so Nync can automatically calculate your availability and book meetings for you.")
                
                ms_url = auth.get_microsoft_url(user.id)
                st.link_button("🔌 Connect Outlook", ms_url, type="primary", use_container_width=True)
                st.info("To connect Google Calendar, please log out and log back in using the 'Continue with Google' button.")
                
            st.divider()

            # --- STEP 2: TEAM ---
            if has_teams:
                st.markdown("### ✅ 2. Team Joined")
                st.caption("You are ready to schedule.")
            else:
                st.markdown("### 🛡️ 2. Join or Create a Team")
                st.caption("You need a team to start proposing and voting on meeting times.")
                
                t_create, t_join = st.tabs(["Create Team", "Join Team"])
                
                with t_create:
                    # Look up their tier and limits instantly
                    profile = auth.get_user_profile(user.id)
                    tier = profile.get('subscription_tier', 'free').lower() if profile else 'free'
                    MAX_TEAMS = 1 if tier in ['free', 'squad'] else 999
                    my_teams = auth.get_user_teams(user.id)
                    
                    if my_teams and len(my_teams) >= MAX_TEAMS:
                        st.error(f"**Limit Reached.** Your {tier.upper()} plan is limited to {MAX_TEAMS} team.")
                        if st.button("🚀 Upgrade Plan", type="primary", use_container_width=True):
                            st.session_state.nav = "Pricing"
                            st.rerun()
                    else:
                        new_team_name = st.text_input("Team Name", placeholder="e.g. Engineering Squad")
                        if st.button("Create Team", use_container_width=True):
                            if new_team_name:
                                if auth.create_team(user.id, new_team_name):
                                    st.success("Team created!")
                                    time.sleep(0.5)
                                    st.rerun()
                            else:
                                st.warning("Please enter a name.")
                            
                with t_join:
                    code = st.text_input("Invite Code", placeholder="NYNC-XXXX")
                    if st.button("Join Team", use_container_width=True):
                        if code:
                            if auth.join_team_by_code(user.id, code):
                                st.success("Joined team!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Invalid or expired invite code.")
                        else:
                            st.warning("Please enter a code.")

        # Fail-safe button in case Streamlit doesn't automatically skip the page on the next rerun
        if has_cal and has_teams:
            st.write("<br>", unsafe_allow_html=True)
            st.success("🎉 You are all set!")
            if st.button("🚀 Go to Dashboard", type="primary", use_container_width=True):
                st.session_state.nav = "Dashboard"
                st.rerun()