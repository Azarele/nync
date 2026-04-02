import streamlit as st
import auth_utils as auth
import time

def show(user, supabase):
    st.header("⚙️ User Settings")
    st.divider()
    
    profile = auth.get_user_profile(user.id)
    if not profile:
        st.error("Could not load profile.")
        return
        
    start_hour = profile.get('work_start_hour') if profile.get('work_start_hour') is not None else 9
    end_hour = profile.get('work_end_hour') if profile.get('work_end_hour') is not None else 17
    
    st.markdown("### 🕒 Personal Working Hours")
    st.caption("Tell Nync when you actually work. The Pain Engine will dynamically bend around your custom schedule.")
    
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
                st.rerun()

    st.write("<br><br>", unsafe_allow_html=True)
    
    if st.button("Log Out", type="secondary"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()