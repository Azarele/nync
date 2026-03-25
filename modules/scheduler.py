import streamlit as st
import datetime as dt
import pytz
import pandas as pd
import altair as alt
import auth_utils as auth

def calculate_local_pain(hour, user_tz_str):
    """Calculates how painful a specific UTC hour is for a local timezone."""
    try:
        user_tz = pytz.timezone(user_tz_str)
        # Create a dummy date to check the hour in their local time
        utc_time = dt.datetime.now(pytz.UTC).replace(hour=hour, minute=0, second=0)
        local_time = utc_time.astimezone(user_tz)
        local_hour = local_time.hour
        
        # Standard Pain Engine Rules:
        if 9 <= local_hour < 17: return 0  # Work hours = Perfect
        elif 8 <= local_hour < 9 or 17 <= local_hour < 18: return 1 # Marginal
        elif 7 <= local_hour < 8 or 18 <= local_hour < 20: return 3 # Annoying
        elif 6 <= local_hour < 7 or 20 <= local_hour < 22: return 5 # Very painful
        else: return 10 # Midnight / Sleep = Extreme pain
    except:
        return 0

def show(supabase, user, roster):
    st.markdown("### 🗺️ Team Availability Heatmap")
    st.caption("A visual grid of when your team is awake and working. Green is good, Red is pain.")
    
    if not roster:
        st.info("Head over to the Team tab to add members first.")
        return

    # User selects a date (defaults to tomorrow)
    target_date = st.date_input("Select Target Date", dt.date.today() + dt.timedelta(days=1))
    
    if st.button("Generate Heatmap", type="primary"):
        with st.spinner("Analyzing Global Timezones..."):
            
            # 1. Build the Data Matrix
            data = []
            utc_hours = list(range(24))
            
            for h in utc_hours:
                # Format UTC hour for display (e.g., "09:00 UTC")
                display_time = f"{h:02d}:00 UTC"
                
                for member in roster:
                    name = member.get('name', 'Unknown')
                    tz = member.get('tz', 'UTC')
                    
                    # Calculate Pain
                    pain = calculate_local_pain(h, tz)
                    
                    data.append({
                        "Time": display_time,
                        "Member": name,
                        "Pain Score": pain,
                        "Local Timezone": tz
                    })
                    
            df = pd.DataFrame(data)

            # 2. Draw the Altair Heatmap
            # Green (0) -> Yellow (3) -> Orange (5) -> Red (10)
            heatmap = alt.Chart(df).mark_rect(cornerRadius=4).encode(
                x=alt.X('Time:O', title='Meeting Time (UTC)', sort=None),
                y=alt.Y('Member:N', title='Team Member'),
                color=alt.Color('Pain Score:Q', scale=alt.Scale(
                    domain=[0, 3, 5, 10], 
                    range=['#2e7d32', '#fbc02d', '#ed6c02', '#c62828']
                ), legend=alt.Legend(title="Pain Level")),
                tooltip=[
                    alt.Tooltip('Member:N', title='Name'),
                    alt.Tooltip('Time:O', title='UTC Time'),
                    alt.Tooltip('Local Timezone:N', title='Timezone'),
                    alt.Tooltip('Pain Score:Q', title='Pain Score')
                ]
            ).properties(
                height=100 + (len(roster) * 40) # Dynamically scales height based on roster size
            ).configure_axis(
                labelFontSize=12,
                titleFontSize=14,
                grid=False
            ).configure_view(
                strokeWidth=0
            )

            # Render the chart natively in Streamlit
            st.altair_chart(heatmap, use_container_width=True)
            
            st.success("Hover over any block to see their exact timezone and pain score!")