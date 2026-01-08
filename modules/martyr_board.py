import streamlit as st
import plotly.express as px
import pandas as pd
import auth_utils as auth

def show(supabase, user, roster):
    st.header("🩸 The Martyr Board")
    st.caption("Tracking who takes the bullet for the team.")

    team_id = st.session_state.active_team_id
    stats = auth.get_martyr_stats(team_id)
    
    if not stats:
        st.info("No meetings recorded yet. Go to the Scheduler to book one!")
        return

    # 1. CREATE LOOKUP LISTS
    # We only want to show stats for people CURRENTLY in the roster
    # active_emails includes both Users and Ghosts
    active_emails = [m['email'] for m in roster]
    name_map = {m['email']: m['name'] for m in roster}
    
    display_data = []
    
    # 2. FILTER & BUILD DATA
    for s in stats:
        email = s['email']
        
        # KEY FIX: Only show if they are currently in the team
        if email in active_emails:
            name = name_map.get(email, email.split('@')[0])
            display_data.append({"Name": name, "Pain Score": s['total_pain']})
    
    if not display_data:
        st.info("History exists, but no current members have pain scores yet.")
        return

    df = pd.DataFrame(display_data)

    if not df.empty:
        # Sort so the highest pain is at the top/right
        df = df.sort_values(by="Pain Score", ascending=True)
        
        # Highlight the "Current Martyr" (Last item in sorted list)
        top_martyr = df.iloc[-1]
        st.error(f"🏆 Current Martyr: **{top_martyr['Name']}** with {top_martyr['Pain Score']} points")
        
        fig = px.bar(
            df, 
            x="Pain Score", 
            y="Name", 
            orientation='h',
            text="Pain Score",
            color="Pain Score",
            color_continuous_scale="Reds"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        
        st.plotly_chart(fig, width='stretch')

    with st.expander("📜 Recent History"):
        history = supabase.table("pain_ledger").select("*").eq("team_id", team_id).order("created_at", desc=True).limit(10).execute()
        if history.data:
            for h in history.data:
                # Optional: You can also filter history here if you want to hide old members' logs
                st.text(f"{h['meeting_date']} - {h['user_email']} took +{h['pain_score']} pain")