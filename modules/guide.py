import streamlit as st

def show():
    st.header("📚 User Manual")
    st.write("Welcome to the resistance against calendar clutter.")
    st.divider()

    st.markdown("""
    ### 1. The Philosophy
    Nync isn't just a calendar app. It's a **pain management system**.
    Most tools try to help you fit *more* meetings in. We track how much your soul is crushing under the weight of them.
    """)

    st.divider()

    t1, t2, t3, t4 = st.tabs(["🛡️ Teams", "🔥 Pain Points", "📅 Scheduling", "🔌 Integrations"])

    with t1:
        st.subheader("Getting Started")
        st.markdown("""
        Everything in Nync revolves around **Teams**.
        
        1.  **Create a Team:** Go to **Settings** -> **Create Team**. You become the admin.
        2.  **Invite Others:** Go to **Settings** -> **My Teams**. Copy the **Invite Code** (e.g., `NYNC-X9Z2`) and send it to your colleagues.
        3.  **Join a Team:** If someone sent you a code, paste it in **Settings** -> **Join Team**.
        """)
        st.info("💡 You can be in multiple teams. Switch between them using the dropdown on the Dashboard.")

    with t2:
        st.subheader("The Martyr Board")
        st.markdown("""
        This is the leaderboard on your Dashboard. But instead of points for winning, you get points for **suffering**.
        
        * **1 Minute of Meeting = 1 Pain Point.**
        * The person with the most points gets the 🥇 Gold Medal (and our sympathy).
        * **Goal:** Use this data to prove you are doing too much "work about work."
        """)

    with t3:
        st.subheader("The Scheduler")
        st.markdown("""
        Stop playing "Calendar Tetris."
        
        1.  Go to **Dashboard** -> **Scheduler** tab.
        2.  Select the **Duration** (e.g., 30 min) and **Time Range**.
        3.  Nync scans everyone's connected calendars instantly.
        4.  **Green Slots** = Everyone is free.
        5.  **Click to Book:** Sends calendar invites immediately (Outlook/Google support).
        """)

    with t4:
        st.subheader("Webhooks & Bots")
        st.markdown("""
        Want to notify your team automatically?
        
        1.  Go to **Settings**.
        2.  Find your Team card.
        3.  Paste a **Discord** or **Microsoft Teams** Webhook URL.
        4.  Nync will post notifications when meetings are booked or when the Martyr Board has a new leader.
        """)
