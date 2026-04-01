import streamlit as st
import auth_utils as auth
import time
import pytz

# --- FRAGMENT 1: The Team Roster ---
@st.fragment
def render_roster(user, supabase, selected_tid, my_role):
    with st.expander("👥 Team Roster & Timezones", expanded=True):
        try:
            roster_data = supabase.table('team_members').select('id, user_id, role, ghost_name, ghost_email, ghost_timezone, profiles(email, default_timezone)').eq('team_id', selected_tid).execute()
            
            if roster_data.data:
                ALL_TZS = pytz.all_timezones
                
                for member in roster_data.data:
                    row_id = member.get('id')
                    m_user_id = member.get('user_id')
                    m_role = member.get('role', 'member')
                    is_ghost = (m_user_id is None)
                    
                    if is_ghost:
                        m_name = member.get('ghost_name') or "Dummy"
                        m_email = member.get('ghost_email') or ""
                        m_tz = member.get('ghost_timezone') or "UTC"
                        display_name = f"👻 {m_name}" + (f" ({m_email})" if m_email else "")
                    else:
                        prof = member.get('profiles') or {}
                        m_email = prof.get('email', 'Unknown User')
                        m_tz = prof.get('default_timezone') or "UTC"
                        display_name = f"👤 {m_email.split('@')[0]}"
                        
                    c1, c2, c3 = st.columns([2.5, 2, 1])
                    
                    if m_user_id == user.id:
                        c1.markdown(f"**{display_name}** (You)")
                    else:
                        c1.markdown(f"**{display_name}**")
                        
                    if my_role == 'admin':
                        tz_options = ALL_TZS if m_tz in ALL_TZS else ALL_TZS + [m_tz]
                        c2.selectbox("TZ", tz_options, index=tz_options.index(m_tz), key=f"tz_{row_id}", label_visibility="collapsed")
                            
                        if m_user_id != user.id:
                            if c3.button("Kick", key=f"kick_{row_id}", type="secondary", use_container_width=True):
                                if auth.remove_team_member_by_row(row_id, selected_tid, user.id):
                                    st.toast(f"Removed member.")
                                    time.sleep(0.5)
                                    st.rerun(scope="fragment") # <--- FRAGMENT RERUN
                    else:
                        c2.write(f"🌍 {m_tz}")
                
                if my_role == 'admin':
                    st.write("") 
                    if st.button("💾 Save Timezone Changes", type="primary", use_container_width=True):
                        changes_made = False
                        for member in roster_data.data:
                            r_id = member.get('id')
                            u_id = member.get('user_id')
                            is_g = (u_id is None)
                            
                            old_tz = member.get('ghost_timezone') or "UTC" if is_g else (member.get('profiles') or {}).get('default_timezone') or "UTC"
                            new_tz = st.session_state.get(f"tz_{r_id}")
                            
                            if new_tz and new_tz != old_tz:
                                auth.update_member_timezone(r_id, u_id, new_tz, is_g)
                                changes_made = True
                        
                        if changes_made:
                            st.success("Timezones updated successfully!")
                            time.sleep(0.5)
                            st.rerun(scope="fragment") # <--- FRAGMENT RERUN
                        else:
                            st.info("No changes to save.")
                        
                if my_role == 'admin':
                    st.markdown("---")
                    st.markdown("##### ➕ Add Dummy Member")
                    with st.form(f"add_ghost_{selected_tid}", clear_on_submit=True):
                        col1, col2, col3 = st.columns([2, 2, 3])
                        g_name = col1.text_input("Name", placeholder="John Doe")
                        g_email = col2.text_input("Email", placeholder="(Optional)")
                        default_tz_index = ALL_TZS.index("UTC") if "UTC" in ALL_TZS else 0
                        g_tz = col3.selectbox("Timezone", ALL_TZS, index=default_tz_index)
                        
                        if st.form_submit_button("Add Dummy"):
                            if g_name:
                                auth.add_ghost_member(selected_tid, g_name, g_email, g_tz, user.id)
                                st.success("Dummy added!")
                                time.sleep(0.5)
                                st.rerun(scope="fragment") # <--- FRAGMENT RERUN
                            else:
                                st.warning("Name is required.")
        except Exception as e:
            st.error(f"Could not load roster: {e}")

# --- FRAGMENT 2: Webhooks ---
@st.fragment
def render_webhooks(supabase, selected_tid, webhook):
    with st.expander("🔌 Webhook Settings"):
        new_hook = st.text_input("Discord/Teams Webhook URL", value=webhook, key=f"wh_{selected_tid}")
        if st.button("Save Webhook", key=f"save_{selected_tid}"):
            supabase.table('teams').update({'webhook_url': new_hook}).eq('id', selected_tid).execute()
            st.success("Saved!")


def show(user, supabase):
    st.header("🛡️ Team Headquarters")
    st.divider()

    # 1. CREATE OR JOIN TEAM
    c_create, c_join = st.columns(2)
    with c_create:
        with st.expander("➕ Create a New Team"):
            new_team_name = st.text_input("Team Name")
            if st.button("Create Team", use_container_width=True):
                if auth.create_team(user.id, new_team_name):
                    st.success(f"Team '{new_team_name}' created!")
                    time.sleep(0.5)
                    st.rerun() # Full rerun required to update the "Select Team" dropdown globally

    with c_join:
        with st.expander("🤝 Join a Team"):
            code = st.text_input("Enter Invite Code")
            if st.button("Join", use_container_width=True):
                if auth.join_team_by_code(user.id, code):
                    st.success("Joined team successfully!")
                    time.sleep(0.5)
                    st.rerun() # Full rerun required
                else:
                    st.error("Invalid code.")

    st.write("<br>", unsafe_allow_html=True)

    # 2. MANAGE EXISTING TEAMS
    my_teams = auth.get_user_teams(user.id)
    
    if not my_teams:
        st.info("👈 Create or Join a team above to get started.")
        return

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

    st.markdown(f"### {selected_team_name} <span style='font-size:14px; background:#444; padding:2px 8px; border-radius:4px; vertical-align: middle;'>{my_role.upper()}</span>", unsafe_allow_html=True)
    
    c_code, c_settings = st.columns([1, 2])
    
    with c_code:
        st.caption("Invite Code")
        st.code(invite_code, language=None)
        
        st.caption("Invite Link")
        invite_link = f"https://nyncapp.streamlit.app/?invite={invite_code}"
        st.code(invite_link, language=None)
        
    with c_settings:
        # Load our hyper-fast fragments!
        render_roster(user, supabase, selected_tid, my_role)
        
        if my_role == 'admin':
            render_webhooks(supabase, selected_tid, webhook)

        st.write("")
        if st.button("Leave Team", type="secondary", key=f"leave_{selected_tid}"):
            if auth.leave_team(selected_tid, user.id):
                st.toast("You have left the team.")
                time.sleep(0.5)
                st.rerun() # Full rerun required because leaving a team changes the global dropdown