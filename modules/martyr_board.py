import streamlit as st
import datetime as dt

# The magic decorator: Only this function will rerun when buttons inside it are clicked!
@st.fragment 
def show(supabase, team_id):
    st.markdown("### 🪧 The Pain Board")
    st.caption("Active polls for your team. Vote on the slot that hurts you the least!")
    
    if not supabase or not team_id:
        return
        
    try:
        # Fetch active polls
        polls = supabase.table('polls').select('id, status, created_at, poll_options(id, slot_time, pain_score, poll_votes(voter_name))').eq('team_id', team_id).eq('status', 'active').order('created_at', desc=True).execute()
        
        if not polls.data:
            st.info("No active polls right now. Propose a meeting from the Heatmap!")
            return
            
        for p in polls.data:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**Poll Created:** {p['created_at'][:10]}")
                if c2.button("Close Poll", key=f"close_{p['id']}", type="secondary", use_container_width=True):
                    supabase.table('polls').update({'status': 'closed'}).eq('id', p['id']).execute()
                    st.rerun(scope="fragment") # Instantly updates just this component
                    
                st.write("")
                options = p.get('poll_options', [])
                if not options:
                    st.warning("No options found for this poll.")
                    continue
                    
                # Sort options by time
                options.sort(key=lambda x: x['slot_time'])
                
                for opt in options:
                    o_id = opt['id']
                    time_str = opt['slot_time'].replace('T', ' ')[:16] + " UTC"
                    votes = opt.get('poll_votes', [])
                    voters = [v['voter_name'] for v in votes]
                    
                    col_time, col_pain, col_votes, col_btn = st.columns([2.5, 1, 2, 1])
                    col_time.write(f"🗓️ {time_str}")
                    col_pain.write(f"🔥 Pain: **{opt['pain_score']}**")
                    col_votes.write(f"🗳️ {len(voters)} Votes")
                    if voters:
                        col_votes.caption(f"{', '.join(voters)}")
                    
                    user_name = st.session_state.user.email.split('@')[0]
                    has_voted = user_name in voters
                    
                    # Vote / Unvote Button Logic
                    if col_btn.button("Unvote" if has_voted else "Vote", key=f"vote_{o_id}", type="primary" if not has_voted else "secondary", use_container_width=True):
                        if has_voted:
                            supabase.table('poll_votes').delete().eq('poll_id', p['id']).eq('voter_name', user_name).execute()
                        else:
                            try:
                                supabase.table('poll_votes').insert({'poll_id': p['id'], 'option_id': o_id, 'voter_name': user_name}).execute()
                            except: pass
                        st.rerun(scope="fragment") # Triggers a high-speed micro-refresh

    except Exception as e:
        st.error(f"Could not load polls: {e}")