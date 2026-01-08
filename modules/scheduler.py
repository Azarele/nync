import streamlit as st
import pytz
import time
from urllib.parse import quote 
from datetime import datetime, timedelta, date
import auth_utils as auth
import modules.calc_engine as engine

# Import the AI module
try:
    import modules.ai_writer as ai
    HAS_AI = True
except ImportError:
    HAS_AI = False

def show(supabase, user, roster):
    # Header with Refresh Button
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        st.markdown(f"## 🕒 Scheduler ({len(roster)} Members)")
    with c_btn:
        if st.button("🔄 Refresh Polls", width="stretch"):
            st.rerun()

    # --- 0. MEETING DETAILS ---
    with st.expander("📝 Meeting Details", expanded=True):
        meeting_subject = st.text_input("Meeting Name", value="Nync Team Sync")

    # --- 1. POLL MANAGER ---
    active_polls = supabase.table('polls').select('*').eq('team_id', st.session_state.active_team_id).eq('status', 'active').order('created_at', desc=True).execute()
    
    if active_polls.data:
        with st.expander(f"📊 Active Polls ({len(active_polls.data)})", expanded=True):
            for poll in active_polls.data:
                opts = supabase.table('poll_options').select('*').eq('poll_id', poll['id']).execute().data
                votes = supabase.table('poll_votes').select('*').eq('poll_id', poll['id']).execute().data
                
                tally = {o['id']: 0 for o in opts}
                for v in votes:
                    if v['option_id'] in tally: tally[v['option_id']] += 1
                
                winner_id = max(tally, key=tally.get) if tally else None
                
                st.write(f"**Poll created: {poll['created_at'][:10]}**")
                
                for o in opts:
                    dt_obj = datetime.fromisoformat(o['slot_time'].replace('Z', '+00:00'))
                    count = tally.get(o['id'], 0)
                    prefix = "🏆" if (o['id'] == winner_id and count > 0) else "⚪"
                    st.write(f"{prefix} **{dt_obj.strftime('%H:%M')} UTC**: {count} votes")
                
                c_book, c_close = st.columns([4, 1])
                with c_book:
                    if st.button("📌 Book Winner & Close", key=f"btn_book_{poll['id']}", width="stretch", type="primary"):
                        if not winner_id or tally[winner_id] == 0:
                            st.error("Wait for at least one vote!")
                        else:
                            winning_opt = next(o for o in opts if o['id'] == winner_id)
                            win_dt = datetime.fromisoformat(winning_opt['slot_time'].replace('Z', '+00:00'))
                            attendees = [m['email'] for m in roster if '@' in m['email']]
                            
                            with st.spinner("Booking in Outlook/Teams..."):
                                success = auth.book_outlook_meeting(
                                    user_id=user.id,
                                    subject=meeting_subject,
                                    start_dt_utc=win_dt,
                                    duration_minutes=60,
                                    attendees=attendees
                                )
                            
                            if success:
                                supabase.table('polls').update({'status': 'closed'}).eq('id', poll['id']).execute()
                                st.success("✅ Meeting Booked & Poll Closed!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("❌ Booking Failed. Check Outlook Connection.")
                
                with c_close:
                    if st.button("🗑️", key=f"btn_force_{poll['id']}", help="Force close poll", width="stretch"):
                        supabase.table('polls').update({'status': 'closed'}).eq('id', poll['id']).execute()
                        st.toast("🗑️ Poll closed.")
                        time.sleep(1)
                        st.rerun()
            st.divider()

    # --- 2. SCHEDULER ENGINE ---
    c1, c2 = st.columns(2)
    with c1:
        target_date = st.date_input("Meeting Date", value=date.today() + timedelta(days=1))
    with c2:
        duration_options = [30, 60, 90, 120, 180, 240, 300, 360]
        duration = st.selectbox("Duration (Minutes)", duration_options, index=1)

    if st.button("🚀 Find Fair Time", type="primary", width="stretch"):
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        end_of_day = start_of_day + timedelta(hours=24)
        
        # 1. Audit Calendars
        busy_map = {}
        with st.status("🕵️ Auditing Calendars...", expanded=True) as status:
            for member in roster:
                if member['type'] == 'user':
                    u_data = supabase.table('profiles').select('id').eq('email', member['email']).single().execute()
                    if u_data.data:
                        uid = u_data.data['id']
                        busy_hours = auth.fetch_outlook_events(uid, start_of_day, end_of_day)
                        if busy_hours: busy_map[member['email']] = busy_hours
            status.update(label="Audit Complete!", state="complete", expanded=False)

        # 2. Run Engine
        history_map = auth.get_team_pain_map(st.session_state.active_team_id)
        top_slots = engine.perform_analysis(roster, busy_map, start_of_day, history_map)
        
        if top_slots:
            st.session_state.calculated_results = {
                "top_slots": top_slots,
                "date": target_date,
                "best_slot": top_slots[0],
                "duration": duration
            }

    # --- 3. RESULTS DISPLAY ---
    if st.session_state.get('calculated_results'):
        res = st.session_state.calculated_results
        
        if res['date'] == target_date:
            best = res['best_slot']
            duration_val = res.get('duration', 60)
            
            st.divider()
            st.subheader(f"🎯 Best Time: {best['utc_hour']}:00 UTC")
            st.caption(f"Duration: {duration_val} mins | Lowest Team Pain: {best['total_pain']}")

            total_pain = best['total_pain']
            color = "green" if total_pain < 5 else "orange" if total_pain < 20 else "red"
            st.markdown(f"**Total Pain Score:** :{color}[{total_pain}]")
            
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("📌 Record Only", width="stretch"):
                    if engine.commit_booking(supabase, st.session_state.active_team_id, best['breakdown'], res['date']):
                        st.toast("✅ Recorded!")
            
            with c_b:
                if st.button("🤖 Propose to Teams/Discord", type="primary", width="stretch"):
                    result = auth.create_poll(st.session_state.active_team_id, res['top_slots'], res['date'])
                    if result is True: st.success("✅ Poll sent!")
                    elif result == "No Webhook": st.error("❌ No Webhook.")
                    else: st.error("❌ Failed.")

            # --- AI DIPLOMAT (UPDATED) ---
            if HAS_AI and "openai" in st.secrets:
                st.divider()
                if st.button("✨ Draft Diplomatic Invite (AI)", key="btn_ai_draft"):
                    with st.spinner("Consulting the diplomatic algorithms..."):
                        # Extract REAL NAMES from the best slot breakdown
                        participants = []
                        for email, data in best['breakdown'].items():
                            participants.append({
                                'name': data['name'], # This is the real name (e.g., "Dave", "Sarah")
                                'score': data['pain']
                            })
                        
                        message = ai.draft_diplomatic_invite(
                            slot_time=f"{res['date']} at {best['utc_hour']}:00 UTC",
                            participants=participants
                        )
                        st.text_area("Copy this to your Calendar Invite:", value=message, height=150)
            elif HAS_AI:
                st.caption("ℹ️ Add OpenAI key to secrets.toml to enable AI drafting.")

            # --- SOCIAL SHARE ---
            st.divider()
            with st.expander("📢 Share Report"):
                profile = auth.get_user_profile(user.id)
                is_free = (profile['subscription_tier'] == 'free') if profile else True
                
                raw_text = f"🗓️ {meeting_subject}\n📅 {res['date']}\n⏰ {best['utc_hour']}:00 UTC\n⏳ {duration_val} mins\n\n"
                raw_text += "Pain Report:\n"
                for email, d in best['breakdown'].items():
                    raw_text += f"• {d['name']}: +{d['pain']} pain\n"
                
                if is_free: raw_text += "\n⚡ Audit your team's fairness for free at Nync.app"

                encoded_text = quote(raw_text)
                app_url = "https://nync.app"
                encoded_url = quote(app_url)

                s1, s2, s3, s4 = st.columns(4)
                with s1: st.link_button("🐦 Post on X", f"https://twitter.com/intent/tweet?text={encoded_text}", use_container_width=True)
                with s2: st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={encoded_text}", use_container_width=True)
                with s3: st.link_button("🏢 MS Teams", f"https://teams.microsoft.com/share?href={encoded_url}&msgText={encoded_text}", use_container_width=True)
                with s4: st.link_button("📘 Facebook", f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}", use_container_width=True)

            # GRID VISUALIZATION
            cols = st.columns(min(len(roster), 4))
            for idx, (email, data) in enumerate(best['breakdown'].items()):
                col = cols[idx % 4]
                p = data['pain']
                icon = "✅"
                if data.get('blocked'): icon = "📅"
                elif p >= 10: icon = "💀"
                elif p >= 3: icon = "😫"
                
                with col:
                    st.markdown(f"""
                    <div style="background:#111; padding:10px; border-radius:8px; text-align:center; border:1px solid #333;">
                        <div style="font-size:20px;">{icon}</div>
                        <b>{data['name']}</b><br>{data['local_h']:02d}:00<br>
                        <span style="color:{'#ff4b4b' if p>0 else '#00cc00'}">+{p} Pain</span>
                    </div>
                    """, unsafe_allow_html=True)