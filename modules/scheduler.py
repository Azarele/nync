import streamlit as st
import datetime as dt
import pytz
import pandas as pd
import altair as alt
import requests
import calendar_utils as cal
import email_utils 
import time
import asyncio
from async_calendar_utils import gather_all_conflicts

# ==========================================
# --- 1. CORE LOGIC ENGINES ---
# ==========================================

def calculate_local_pain(target_date, hour, user_tz_str, work_start=9, work_end=17):
    """Calculates exactly how painful a UTC hour is, dynamically bending around custom work hours!"""
    try:
        user_tz = pytz.timezone(user_tz_str)
        utc_time = dt.datetime.combine(target_date, dt.time(hour=hour)).replace(tzinfo=pytz.UTC)
        local_time = utc_time.astimezone(user_tz)
        local_hour = local_time.hour
        is_weekend = local_time.weekday() >= 5 
        
        # --- THE DYNAMIC MATH ENGINE ---
        if work_start <= local_hour < work_end: 
            base_pain = 0  # In their core shift
        elif (work_start - 1) <= local_hour < work_start or work_end <= local_hour < (work_end + 1): 
            base_pain = 1  # 1 hour before/after shift
        elif (work_start - 2) <= local_hour < (work_start - 1) or (work_end + 1) <= local_hour < (work_end + 3): 
            base_pain = 3  # 2 hours early, or early evening
        elif (work_start - 3) <= local_hour < (work_start - 2) or (work_end + 3) <= local_hour < (work_end + 5): 
            base_pain = 5  # Late evening / very early
        else: 
            base_pain = 10 # Midnight / Deep Sleep
        
        # Weekends add a flat +8 penalty, maxing out at 10
        if is_weekend: return min(10, base_pain + 8)
        return base_pain
    except: return 0

def fetch_all_conflicts(supabase, roster, start_date, days):
    start_dt = dt.datetime.combine(start_date, dt.time.min) 
    end_dt = start_dt + dt.timedelta(days=days)
    
    conflicts_dict = {}
    for m in roster:
        uid = m.get('user_id')
        if not uid: continue
        
        res = supabase.table('calendar_connections').select('provider').eq('user_id', uid).execute()
        providers = [r['provider'] for r in res.data] if res.data else []
        
        blocked_strs = set()
        
        if 'outlook' in providers:
            evts = cal.fetch_outlook_events(uid, start_dt, end_dt)
            for e in evts:
                e_naive = e.astimezone(dt.timezone.utc).replace(tzinfo=None) if e.tzinfo else e
                blocked_strs.add(e_naive.isoformat())
                
        if 'google' in providers:
            evts = cal.fetch_google_events(uid, start_dt, end_dt)
            for e in evts:
                e_naive = e.replace(tzinfo=None) if e.tzinfo else e
                blocked_strs.add(e_naive.isoformat())
        
        if blocked_strs:
            conflicts_dict[str(uid)] = list(blocked_strs)
            
    return conflicts_dict

@st.cache_data(ttl=600, show_spinner=False)
def build_heatmap_dataframe(target_date, roster):
    """Builds the visual heatmap data."""
    data = []
    utc_hours = list(range(24))
    for h in utc_hours:
        display_time = f"{h:02d}:00 UTC"
        for member in roster:
            name = member.get('name', 'Unknown')
            tz = member.get('tz', 'UTC')
            
            # PULL PERSONAL HOURS!
            w_start = member.get('work_start', 9)
            w_end = member.get('work_end', 17)
            
            pain = calculate_local_pain(target_date, h, tz, w_start, w_end)
            
            data.append({
                "Time": display_time, "Hour": h, 
                "Member": name, "Pain Score": pain, "Local Timezone": tz
            })
    return pd.DataFrame(data)

@st.cache_data(ttl=600, show_spinner=False)
def get_best_slots(roster, start_date, days=7, conflicts_dict=None):
    """The Magic Algorithm: Scans hours to find the 3 lowest-pain slots."""
    if conflicts_dict is None: conflicts_dict = {}
    best_slots = []
    
    for day_offset in range(days):
        current_date = start_date + dt.timedelta(days=day_offset)
        for h in range(24):
            slot_dt_naive = dt.datetime.combine(current_date, dt.time(hour=h))
            slot_str = slot_dt_naive.isoformat()
            
            total_pain = 0
            conflict_count = 0
            
            for m in roster:
                # PULL PERSONAL HOURS!
                w_start = m.get('work_start', 9)
                w_end = m.get('work_end', 17)
                
                pain = calculate_local_pain(current_date, h, m.get('tz', 'UTC'), w_start, w_end)
                uid = m.get('user_id')
                
                if uid and str(uid) in conflicts_dict:
                    if slot_str in conflicts_dict[str(uid)]:
                        pain += 25 
                        conflict_count += 1
                        
                total_pain += pain
                
            best_slots.append({
                'date': current_date,
                'hour': h,
                'time_str': f"{h:02d}:00 UTC",
                'total_pain': total_pain,
                'conflicts': conflict_count
            })
            
    best_slots.sort(key=lambda x: (x['total_pain'], x['date']))
    return best_slots[:3]

def notify_team(supabase, team_id, roster, target_date, chosen_time, total_pain):
    """Fires Webhooks AND Blasts Emails instantly!"""
    try:
        t_data = supabase.table('teams').select('webhook_url, name').eq('id', team_id).single().execute()
        webhook_url = t_data.data.get('webhook_url')
        team_name = t_data.data.get('name', 'Your Team')
        
        if webhook_url:
            url_lower = webhook_url.lower()
            msg = f"🚨 **New Meeting Proposed for {team_name}** 🚨\n\n"
            msg += f"🗓️ **Time:** {target_date.strftime('%B %d, %Y')} at {chosen_time}\n"
            msg += f"🔥 **Total Team Pain:** {total_pain}\n\n"
            msg += f"👉 **[Click here to vote on the Nync Pain Board!](https://nyncapp.streamlit.app)**"
            
            if "discord" in url_lower: payload = {"content": msg}
            elif "slack" in url_lower: payload = {"text": msg}
            else:
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "4f46e5",
                    "summary": f"New Meeting for {team_name}",
                    "text": msg.replace('\n', '\n\n')
                }
            requests.post(webhook_url, json=payload, timeout=3)
            
        recipient_emails = []
        for m in roster:
            em = m.get('email') or m.get('ghost_email')
            if em and '@' in em: recipient_emails.append(em)
                
        if recipient_emails:
            email_utils.send_poll_email(recipient_emails, team_name, target_date, chosen_time)
            
    except Exception as e: print(f"Notification failed: {e}")


# ==========================================
# --- 2. UI FRAGMENTS ---
# ==========================================

@st.fragment
def render_magic_suggest(supabase, team_id, roster, target_date):
    if st.button("✨ Auto-Find Best Times", type="primary", use_container_width=True):
        st.session_state.show_magic = not st.session_state.get('show_magic', False)
        st.rerun(scope="fragment")

    if st.session_state.get('show_magic', False):
        st.markdown("#### 🎯 Top 3 Suggested Slots")
        
        scope = st.segmented_control(
            "Search Scope", 
            options=["Selected Date Only", "Next 7 Days"], 
            default="Next 7 Days",
            selection_mode="single",
            label_visibility="collapsed"
        )
        
        if not scope: scope = "Next 7 Days"
        days_to_scan = 7 if scope == "Next 7 Days" else 1
        
        check_live = st.checkbox("🔄 Avoid Calendar Conflicts (Live Sync)", value=True, help="Pulls live Google/Outlook data for the whole team.")
        
        if days_to_scan == 7: st.caption(f"Scanning **168 hours** starting from {target_date.strftime('%b %d')}.")
        else: st.caption(f"Scanning all **24 hours on {target_date.strftime('%b %d')}**.")
        
        with st.spinner("Crunching the math & syncing calendars..."):
            
            conflicts_dict = {}
            if check_live:
                conflicts_dict = asyncio.run(gather_all_conflicts(roster, target_date, days_to_scan))
                
            top_slots = get_best_slots(roster, target_date, days_to_scan, conflicts_dict)
            cols = st.columns(3)
            
            for i, slot in enumerate(top_slots):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"**{slot['date'].strftime('%a, %b %d')}**")
                        st.markdown(f"<h3 style='margin:0; padding:0; color:#4f46e5;'>{slot['time_str']}</h3>", unsafe_allow_html=True)
                        
                        if slot['conflicts'] > 0: st.error(f"⚠️ {slot['conflicts']} Overlap(s)")
                        else: st.success("✅ Clear Calendars")
                            
                        base_pain = slot['total_pain'] - (slot['conflicts'] * 25)
                        st.caption(f"🔥 Base Pain: **{base_pain}**")
                        
                        if st.button("Propose", key=f"mag_prop_{i}_{days_to_scan}", use_container_width=True):
                            poll = supabase.table('polls').insert({'team_id': team_id, 'status': 'active'}).execute()
                            if poll.data:
                                poll_id = poll.data[0]['id']
                                slot_dt = dt.datetime.combine(slot['date'], dt.time(hour=slot['hour'])).replace(tzinfo=dt.timezone.utc)
                                supabase.table('poll_options').insert({
                                    'poll_id': poll_id, 'slot_time': slot_dt.isoformat(), 'pain_score': int(base_pain)
                                }).execute()
                                
                                st.success("✅ Poll Created! Check the Pain Board.")
                                notify_team(supabase, team_id, roster, slot['date'], slot['time_str'], base_pain)
                                st.session_state.show_magic = False
                                
                                # FIX: FULL PAGE REFRESH TO UPDATE TABS
                                time.sleep(1.2) 
                                st.rerun() 
        st.divider()


# ==========================================
# --- 3. MAIN DASHBOARD RENDERER ---
# ==========================================

def show(supabase, user, roster):
    st.markdown("### 🗺️ Team Availability Heatmap")
    st.caption("A visual grid of when your team is awake and working. **Swipe to scroll and tap a column to propose a meeting!**")
    
    if not roster:
        st.info("Head over to the Team tab to add members first.")
        return

    team_id = st.session_state.get('active_team_id')

    c_mag, c_date = st.columns([1, 2], vertical_alignment="bottom")
    with c_date:
        target_date = st.date_input("Select Target Date", dt.date.today() + dt.timedelta(days=1))
    
    with c_mag:
        render_magic_suggest(supabase, team_id, roster, target_date)
        
    with st.spinner("Loading Availability..."):
        df = build_heatmap_dataframe(target_date, roster)
        time_sel = alt.selection_point(fields=['Time'], name="TimeSelect")

        heatmap = alt.Chart(df).mark_rect(cornerRadius=6).encode(
            x=alt.X('Time:O', title='', sort=None, axis=alt.Axis(labelAngle=-45, labelPadding=10)),
            y=alt.Y('Member:N', title='', axis=alt.Axis(labelFontWeight='bold')), 
            color=alt.Color('Pain Score:Q', scale=alt.Scale(
                domain=[0, 3, 5, 10], 
                range=['#10b981', '#f59e0b', '#f97316', '#ef4444']
            ), legend=None), 
            opacity=alt.condition(time_sel, alt.value(1.0), alt.value(0.3)),
            tooltip=[
                alt.Tooltip('Member:N', title='Name'),
                alt.Tooltip('Time:O', title='UTC Time'),
                alt.Tooltip('Local Timezone:N', title='Timezone'),
                alt.Tooltip('Pain Score:Q', title='Pain Score')
            ]
        ).add_params(time_sel).properties(
            height=120 + (len(roster) * 45),
            width=1000 
        ).configure_axis(
            labelFontSize=13, titleFontSize=14, grid=False, domain=False, tickSize=0
        ).configure_view(strokeWidth=0)

        try:
            st.markdown('<div class="scrollable-chart">', unsafe_allow_html=True)
            event = st.altair_chart(heatmap, use_container_width=False, on_select="rerun")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if event and "selection" in event and "TimeSelect" in event["selection"]:
                selected_items = event["selection"]["TimeSelect"]
                if selected_items:
                    chosen_time = selected_items[0]["Time"]
                    time_df = df[df["Time"] == chosen_time]
                    total_pain = time_df["Pain Score"].sum()
                    chosen_hour = time_df["Hour"].iloc[0]
                    
                    st.markdown("---")
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"#### 🎯 Selected Slot: **{chosen_time}**")
                        st.caption(f"**Total Team Pain:** {total_pain} (Lower is better)")
                    with c2:
                        if st.button("🗳️ Propose as Poll", type="primary", use_container_width=True):
                            if team_id:
                                poll = supabase.table('polls').insert({'team_id': team_id, 'status': 'active'}).execute()
                                if poll.data:
                                    poll_id = poll.data[0]['id']
                                    slot_dt = dt.datetime.combine(target_date, dt.time(hour=chosen_hour)).replace(tzinfo=dt.timezone.utc)
                                    supabase.table('poll_options').insert({'poll_id': poll_id, 'slot_time': slot_dt.isoformat(), 'pain_score': int(total_pain)}).execute()
                                    
                                    st.success(f"Poll created for {chosen_time}! Check the Pain Board.")
                                    notify_team(supabase, team_id, roster, target_date, chosen_time, total_pain)
                                    
                                    # FIX: FULL PAGE REFRESH TO UPDATE TABS
                                    time.sleep(1.2)
                                    st.rerun()
                                    
        except Exception as e:
            st.altair_chart(heatmap, use_container_width=False)