import streamlit as st
import auth_utils as auth
import datetime as dt

@st.fragment 
def show(supabase, team_id):
    st.markdown("### 🪧 The Pain Board")
    st.caption("Active polls for your team. Vote on the slot that hurts you the least!")
    
    if not supabase or not team_id:
        return
        
    try:
        # ==========================================
        # --- NEW: GAMIFIED LEADERBOARD CARDS ---
        # ==========================================
        stats = auth.get_martyr_stats(team_id)
        
        # Custom CSS for the 3D-effect Leaderboard Cards
        st.markdown("""
        <style>
            .martyr-card {
                background: linear-gradient(145deg, #1e1e1e, #111);
                border-radius: 12px;
                padding: 20px 10px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.4);
                transition: transform 0.2s ease;
                margin-bottom: 15px;
            }
            .martyr-card:hover { transform: translateY(-5px); }
            .martyr-emoji { font-size: 3rem; margin-bottom: 5px; }
            .martyr-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}
            .martyr-name { font-size: 1.2rem; font-weight: bold; color: #fff; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
            .martyr-score { font-size: 0.95rem; color: #aaa; }
            .martyr-score span { color: #ff4b4b; font-weight: bold; font-size: 1.1rem;}
        </style>
        """, unsafe_allow_html=True)

        if stats:
            st.markdown("#### 🏆 The Martyr Leaderboard")
            st.caption("Who has sacrificed the most sleep for the team?")
            
            # Display Top 4 members dynamically
            cols = st.columns(min(len(stats), 4))
            for i, stat in enumerate(stats[:4]):
                email = stat['email'].split('@')[0]
                pain = stat['total_pain']
                
                # Assign Medals and Colors based on Rank
                if i == 0: emoji, color, title = "🥇", "#FFD700", "Ultimate Martyr"
                elif i == 1: emoji, color, title = "🥈", "#C0C0C0", "Silver Sacrifice"
                elif i == 2: emoji, color, title = "🥉", "#CD7F32", "Bronze Burden"
                else: emoji, color, title = "🎖️", "#888888", "Team Player"
                    
                with cols[i]:
                    st.markdown(f"""
                    <div class="martyr-card" style="border-top: 4px solid {color};">
                        <div class="martyr-emoji">{emoji}</div>
                        <div class="martyr-title" style="color: {color};">{title}</div>
                        <div class="martyr-name">{email}</div>
                        <div class="martyr-score">Pain Score: <span>{pain}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
        else:
            with st.container(border=True):
                st.markdown("""
                <div style='text-align: center; padding: 30px; color: #888;'>
                    <h1 style='font-size: 40px; margin-bottom: 10px;'>🏆</h1>
                    <h4>The Martyr Leaderboard is Empty</h4>
                    <p style='font-size: 14px;'>No pain recorded yet. Once meetings are booked, the sacrifices will be etched here forever.</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ==========================================
        # --- EXISTING POLLS LOGIC ---
        # ==========================================
        st.markdown("#### 🗳️ Active Polls")
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
                    st.rerun(scope="fragment") 
                    
                st.write("")
                options = p.get('poll_options', [])
                if not options:
                    st.warning("No options found for this poll.")
                    continue
                    
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
                    
                    if col_btn.button("Unvote" if has_voted else "Vote", key=f"vote_{o_id}", type="primary" if not has_voted else "secondary", use_container_width=True):
                        if has_voted:
                            supabase.table('poll_votes').delete().eq('poll_id', p['id']).eq('voter_name', user_name).execute()
                        else:
                            try:
                                supabase.table('poll_votes').insert({'poll_id': p['id'], 'option_id': o_id, 'voter_name': user_name}).execute()
                            except: pass
                        st.rerun(scope="fragment")

    except Exception as e:
        st.error(f"Could not load board: {e}")