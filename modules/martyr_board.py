import streamlit as st
import auth_utils as auth

def show(supabase, team_id):
    # --- NO NAV BAR HERE ---
    
    st.header("🔥 The Martyr Board")
    st.write("Ranking the team's biggest heroes (or victims).")
    st.divider()

    # Fetch Data using the team_id passed from app.py
    stats = auth.get_martyr_stats(team_id)
    
    if not stats:
        st.info("No meeting pain recorded yet. Book a meeting to start the leaderboard!")
        return

    # Display Leaderboard
    for i, person in enumerate(stats):
        rank = i + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        
        c1, c2, c3 = st.columns([1, 4, 2])
        with c1:
            st.markdown(f"### {medal}")
        with c2:
            st.write(f"**{person['email']}**")
            st.caption("The Team Player")
        with c3:
            st.markdown(f"**{person['total_pain']}** Pain Pts")
        
        st.divider()
