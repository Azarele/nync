import streamlit as st
import auth_utils as auth
import datetime as dt
import time
from modules.scheduler import calculate_local_pain

@st.fragment 
def show(supabase, team_id):
    st.markdown("### 🪧 The Pain Board")
    st.caption("Active polls for your team. Vote on the slot that hurts you the least!")
    
    if not supabase or not team_id:
        return
        
    try:
        stats = auth.get_martyr_stats(team_id)
        
        css_styles = (
            "<style>"
            ".leaderboard-container { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin-bottom: 20px; }"
            ".martyr-card { background: linear-gradient(145deg, #1f1f2e, #13131c); border-radius: 16px; padding: 20px 15px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); flex: 1 1 200px; min-width: 160px; max-width: 250px; border: 1px solid rgba(255,255,255,0.05); }"
            ".martyr-card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.7); }"
            ".martyr-emoji { font-size: 3.5rem; margin-bottom: 8px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));}"
            ".martyr-title { font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;}"
            ".martyr-name { font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}"
            ".martyr-score { font-size: 0.9rem; color: #a1a1aa; }"
            ".martyr-score span { color: #ef4444; font-weight: 900; font-size: 1.2rem;}"
            "</style>"
        )
        
        try:
            st.html(css_styles)
        except AttributeError:
            st.markdown(css_styles, unsafe_allow_html=True)

        if stats:
            st.markdown("#### 🏆 The Martyr Leaderboard")
            st.caption("Who has sacrificed the most sleep for the team?")
            
            html_cards = "<div class='leaderboard-container'>"
            
            for i, stat in enumerate(stats[:4]):
                email = stat['email'].split('@')[0]
                pain = stat['total_pain']
                
                if i == 0: emoji, color, title = "🥇", "#fbbf24", "Ultimate Martyr"
                elif i == 1: emoji, color, title = "🥈", "#94a3b8", "Silver Sacrifice"
                elif i == 2: emoji, color, title = "🥉", "#b45309", "Bronze Burden"
                else: emoji, color, title = "🎖️", "#52525b", "Team Player"
                    
                html_cards += f"<div class='martyr-card' style='border-top: 4px solid {color};'>"
                html_cards += f"<div class='martyr-emoji'>{emoji}</div>"
                html_cards += f"<div class='martyr-title' style='color: {color};'>{title}</div>"
                html_cards += f"<div class='martyr-name'>{email}</div>"
                html_cards += f"<div class='martyr-score'>Total Pain: <span>{pain}</span></div>"
                html_cards += "</div>"
                
            html_cards += "</div>"
            
            try:
                st.html(html_cards)
            except AttributeError:
                st.markdown(html_cards, unsafe_allow_html=True)
            
        else:
            with st.container(border=True):
                empty_html = (
                    "<div style='text-align: center; padding: 40px; color: #71717a;'>"
                    "<h1 style='font-size: 50px; margin-bottom: 10px; opacity: 0.5;'>🏆</h1>"
                    "<h4 style='font-weight: 600;'>The Leaderboard is Empty</h4>"
                    "<p style='font-size: 15px;'>No pain recorded yet. Propose a meeting to start the games.</p>"
                    "</div>"
                )
                try:
                    st.html(empty_html)
                except AttributeError:
                    st.markdown(empty_html, unsafe_allow_html=True)

        st.divider()

        st.markdown("#### 🗳️ Active Polls")
        polls = supabase.table('polls').select('id, status, created_at, poll_options(id, slot_time, pain_score, poll_votes(voter_name))').eq('team_id', team_id).eq('status', 'active').order('created_at', desc=True).execute()
        
        if not polls.data:
            st.info("No active polls right now.")
            return
            
        for p in polls.data:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**Poll Created:** {p['created_at'][:10]}")
                
                with st.popover("🔗 Share with External Client", use_container_width=True):
                    st.markdown("Copy this link and send it to your client. They can vote without logging in, and times will automatically convert to their local timezone.")
                    
                    # CHANGE `poll['id']` to `p['id']` here! 👇
                    guest_url = f"https://nyncapp.streamlit.app/?guest_poll={p['id']}"
                    st.code(guest_url, language=None)
                
                # --- BOOKING LOGIC ---
                if c2.button("📅 Book Meeting", key=f"close_{p['id']}", type="primary", use_container_width=True):
                    options = p.get('poll_options', [])
                    if options:
                        winning_opt = max(options, key=lambda x: len(x.get('poll_votes', [])))
                        slot_time_str = winning_opt['slot_time']
                        
                        if not slot_time_str.endswith('Z') and '+' not in slot_time_str:
                            slot_time_str += 'Z'
                        slot_dt_utc = dt.datetime.fromisoformat(slot_time_str.replace('Z', '+00:00'))
                        
                        roster = auth.get_team_roster(team_id)
                        attendees = [m['email'] for m in roster if m.get('email')]
                        
                        target_date = slot_dt_utc.date()
                        hour = slot_dt_utc.hour
                        pain_inserts = []
                        
                        for member in roster:
                            name = member.get('name', 'Unknown')
                            email = member.get('email') or name
                            tz = member.get('tz', 'UTC')
                            
                            pain = calculate_local_pain(target_date, hour, tz)
                            if pain > 0:
                                pain_inserts.append({
                                    'team_id': team_id,
                                    'user_email': email,
                                    'pain_score': pain
                                })
                                
                        if pain_inserts:
                            supabase.table('pain_ledger').insert(pain_inserts).execute()
                            
                        subject = f"Team Sync (Nync)"
                        booked = False
                        
                        conns = supabase.table('calendar_connections').select('provider').eq('user_id', st.session_state.user.id).execute()
                        providers = [c['provider'] for c in conns.data] if conns.data else []
                        
                        if 'outlook' in providers:
                            booked = auth.book_outlook_meeting(st.session_state.user.id, subject, slot_dt_utc, 30, attendees)
                        elif 'google' in providers:
                            booked = auth.book_google_meeting(st.session_state.user.id, subject, slot_dt_utc, 30, attendees)
                            
                        if booked:
                            st.toast("✅ Meeting Booked & Invites Sent!")
                        else:
                            st.warning("⚠️ Poll closed, but calendar booking failed (Check connections).")
                            
                    supabase.table('polls').update({'status': 'closed'}).eq('id', p['id']).execute()
                    time.sleep(1)
                    st.rerun(scope="fragment") 
                    
                st.write("")
                options = p.get('poll_options', [])
                if not options: continue
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
                    if voters: col_votes.caption(f"{', '.join(voters)}")
                    
                    user_name = st.session_state.user.email.split('@')[0]
                    has_voted = user_name in voters
                    
                    if col_btn.button("Unvote" if has_voted else "Vote", key=f"vote_{o_id}", type="primary" if not has_voted else "secondary", use_container_width=True):
                        if has_voted: supabase.table('poll_votes').delete().eq('poll_id', p['id']).eq('voter_name', user_name).execute()
                        else:
                            try: supabase.table('poll_votes').insert({'poll_id': p['id'], 'option_id': o_id, 'voter_name': user_name}).execute()
                            except: pass
                        st.rerun(scope="fragment")

    except Exception as e: st.error(f"Could not load board: {e}")