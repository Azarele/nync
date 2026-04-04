import streamlit as st
import datetime as dt
import pytz
from streamlit_javascript import st_javascript
import base64 # Required for loading the logo

def show(supabase, poll_id):
    # Hide the sidebar and top header for a clean, white-label client experience
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
            .stApp header {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # --- RENDER NYNC LOGO ---
    try:
        with open("nync_marketing.png", "rb") as f: 
            img_data = base64.b64encode(f.read()).decode()
        st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{img_data}' width='80'></div>", unsafe_allow_html=True)
    except:
        # Fallback just in case the image fails to load
        st.markdown("<h1 style='text-align: center; color: #4f46e5;'>Nync</h1>", unsafe_allow_html=True)
    
    try:
        # Fetch the Poll and Team Name
        poll_res = supabase.table('polls').select('status, teams(name)').eq('id', poll_id).maybe_single().execute()
        if not poll_res.data:
            st.error("This meeting link is invalid or has expired.")
            return
            
        if poll_res.data['status'] != 'active':
            st.warning("This meeting time has already been finalized!")
            return
            
        team_name = poll_res.data['teams']['name']
        st.markdown(f"<h3 style='text-align: center; margin-top: 20px;'><b>{team_name}</b> has invited you to a meeting.</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280;'>Select the time that works best for you.</p>", unsafe_allow_html=True)
        st.divider()

        # Auto-Detect Client Timezone using JS Bridge
        if 'guest_tz' not in st.session_state:
            client_tz = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
            if client_tz and client_tz != "0" and client_tz != 0:
                st.session_state.guest_tz = client_tz
                st.rerun()
            else:
                st.session_state.guest_tz = 'UTC'
                
        guest_tz_str = st.session_state.guest_tz
        guest_tz = pytz.timezone(guest_tz_str)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.caption(f"🌍 Times automatically converted to **{guest_tz_str}**")
            
            # --- ADDED EMAIL COLLECTION ---
            guest_name = st.text_input("Your Name", placeholder="e.g. Jane Doe")
            guest_email = st.text_input("Your Email", placeholder="e.g. jane@acmecorp.com")
            
            # Require both fields to be filled before showing options
            if guest_name and guest_email:
                st.write("")
                opts_res = supabase.table('poll_options').select('id, slot_time').eq('poll_id', poll_id).execute()
                
                # Check if they already voted in this browser session
                voted_already = st.session_state.get('guest_voted', False)
                
                if voted_already:
                    st.success("🎉 Your vote has been recorded! You can safely close this window.")
                else:
                    for opt in opts_res.data:
                        # Convert UTC to Client's Local Time dynamically
                        utc_time = dt.datetime.fromisoformat(opt['slot_time']).replace(tzinfo=pytz.UTC)
                        local_time = utc_time.astimezone(guest_tz)
                        display_time = local_time.strftime("%A, %B %d • %I:%M %p")
                        
                        with st.container(border=True):
                            st.markdown(f"#### {display_time}")
                            if st.button("I'm available here", key=f"gv_{opt['id']}", type="primary", use_container_width=True):
                                
                                # Format into a single string to fit existing database schema
                                combined_identity = f"{guest_name.strip()} ({guest_email.strip()})"
                                
                                supabase.table('poll_votes').insert({
                                    'poll_id': poll_id,
                                    'option_id': opt['id'],
                                    'voter_name': combined_identity 
                                }).execute()
                                
                                st.session_state.guest_voted = True
                                st.rerun()
                                
    except Exception as e:
        st.error("An error occurred loading the meeting details.")