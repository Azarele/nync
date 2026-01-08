import streamlit as st
import pandas as pd
import altair as alt
import auth_utils as auth

def show(supabase, team_id):
    st.header("🔥 The Martyr Board")
    st.write("Who is taking one for the team? (Higher score = More suffering)")
    st.divider()

    stats = auth.get_martyr_stats(team_id)
    
    if not stats:
        st.info("No meeting pain recorded yet. Book a meeting to start the leaderboard!")
        return

    df = pd.DataFrame(stats)
    if 'email' not in df.columns or 'total_pain' not in df.columns:
        st.error("Error reading pain data.")
        return

    df['Name'] = df['email'].apply(lambda x: x.split('@')[0].capitalize())
    
    # --- TRANSPARENT BACKGROUND CHART ---
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('total_pain', title='Pain Points 🩸'),
        y=alt.Y('Name', sort='-x', title='Team Member'),
        color=alt.Color('total_pain', scale=alt.Scale(scheme='reds'), legend=None),
        tooltip=['Name', 'total_pain', 'email']
    ).properties(
        height=300,
        background='transparent' # Ensure it blends with page
    ).configure_view(
        strokeWidth=0 # Remove chart border
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    st.subheader("🏆 The Heroes")
    top_3 = df.nlargest(3, 'total_pain')
    cols = st.columns(3)
    
    for i, (index, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            st.metric(label=f"{medal} {row['Name']}", value=f"{row['total_pain']} pts")
            
    st.divider()
