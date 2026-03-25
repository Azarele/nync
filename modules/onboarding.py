import streamlit as st
import auth_utils as auth
import time

def show(user, supabase, has_cal, has_team):
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Use columns to center the wizard nicely
    c1, c2, c3 = st.columns([1, 2.5, 1])
    
    with c2:
        st.markdown("<h2 style='text-align: center;'>Welcome to Nync ⚡</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Let's get you set up so we can start eliminating schedule pain.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # STEP 1: CALENDAR CONNECTION
        # ==========================================
        st.markdown("#### Step 1: Connect your Calendar")
        if has_cal:
            st.success("✅ **Calendar Connected:** Your availability is now synced securely.", icon="📅")
        else:
            st.info("We need your calendar to find the least painful times to meet.", icon="📅")
            
            sc1, sc2 = st.columns(2)
            with sc1:
                ms_url = auth.get_microsoft_url(user.id)
                st.link_button("🔌 Connect Outlook", ms_url, use_container_width=True, type="primary")
            with sc2:
                st.caption("Using Google Workspace? **Log Out** and sign back in using the Google button to sync automatically.")

        st.write("---")

        # ==========================================
        # STEP 2: TEAM SETUP
        # ==========================================
        st.markdown("#### Step 2: Assemble your Team")
        if has_team:
            st.success("✅ **Team Ready:** You are officially in a squad.", icon="🛡️")
        else:
            if not has_cal:
                # Lock Step 2 until Step 1 is done
                st.warning("Please connect your calendar above to unlock team features.", icon="🔒")
            else:
                t1, t2 = st.tabs(["➕ Create Team", "🤝 Join Team"])
                
                with t1:
                    new_team = st.text_input("Give your squad a name:", placeholder="e.g., Engineering Elite")
                    if st.button("Create Team", type="primary", use_container_width=True):
                        if new_team:
                            if auth.create_team(user.id, new_team):
                                st.success("Team Created! Reloading...")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Failed to create team. Try another name.")
                with t2:
                    code = st.text_input("Got an invite code?", placeholder="NYNC-XXXX")
                    if st.button("Join Team", use_container_width=True):
                        if code:
                            if auth.join_team_by_code(user.id, code):
                                st.success("Joined successfully! Reloading...")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Invalid or expired code.")