import streamlit as st
import datetime as dt
import pytz
import pandas as pd
import altair as alt

def calculate_local_pain(target_date, hour, user_tz_str):
    try:
        user_tz = pytz.timezone(user_tz_str)
        utc_time = dt.datetime.combine(target_date, dt.time(hour=hour)).replace(tzinfo=pytz.UTC)
        local_time = utc_time.astimezone(user_tz)
        local_hour = local_time.hour
        is_weekend = local_time.weekday() >= 5 
        
        if 9 <= local_hour < 17: base_pain = 0 
        elif 8 <= local_hour < 9 or 17 <= local_hour < 18: base_pain = 1 
        elif 7 <= local_hour < 8 or 18 <= local_hour < 20: base_pain = 3 
        elif 6 <= local_hour < 7 or 20 <= local_hour < 22: base_pain = 5 
        else: base_pain = 10 
        
        if is_weekend: return min(10, base_pain + 8)
        return base_pain
    except: return 0

def show(supabase, user, roster):
    st.markdown("### 🗺️ Team Availability Heatmap")
    st.caption("A visual grid of when your team is awake and working. **Swipe to scroll and tap a column to propose a meeting!**")
    
    if not roster:
        st.info("Head over to the Team tab to add members first.")
        return

    target_date = st.date_input("Select Target Date", dt.date.today() + dt.timedelta(days=1))
    
    with st.spinner("Analyzing Global Timezones..."):
        data = []
        utc_hours = list(range(24))
        
        for h in utc_hours:
            display_time = f"{h:02d}:00 UTC"
            for member in roster:
                name = member.get('name', 'Unknown')
                tz = member.get('tz', 'UTC')
                pain = calculate_local_pain(target_date, h, tz)
                
                data.append({
                    "Time": display_time, "Hour": h, 
                    "Member": name, "Pain Score": pain, "Local Timezone": tz
                })
                
        df = pd.DataFrame(data)
        time_sel = alt.selection_point(fields=['Time'], name="TimeSelect")

        # --- MOBILE OPTIMIZATION & FONT WEIGHT FIX ---
        # Fixed: Changed fontWeight='bold' to labelFontWeight='bold'
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
                            team_id = st.session_state.get('active_team_id')
                            if team_id:
                                poll = supabase.table('polls').insert({'team_id': team_id, 'status': 'active'}).execute()
                                if poll.data:
                                    poll_id = poll.data[0]['id']
                                    slot_dt = dt.datetime.combine(target_date, dt.time(hour=chosen_hour)).replace(tzinfo=dt.timezone.utc)
                                    supabase.table('poll_options').insert({'poll_id': poll_id, 'slot_time': slot_dt.isoformat(), 'pain_score': int(total_pain)}).execute()
                                    st.success(f"Poll created for {chosen_time}!")
                                    
        except Exception as e:
            st.altair_chart(heatmap, use_container_width=False)