import streamlit as st

def show():
    st.header("📚 How Nync Works")
    st.write("Welcome to the resistance against calendar clutter.")
    st.divider()

    t1, t2, t3, t4 = st.tabs(["🛡️ Teams", "🔥 Pain Board", "🗓️ Scheduler", "🔌 Integrations"])

    with t1:
        st.subheader("Getting Started with Teams")
        st.markdown("""
        Everything in Nync revolves around **Teams**.

        1. **Create a Team:** Go to the **Team** tab → *Create a New Team*. You become the admin.
        2. **Invite Others:** Copy the **Invite Code** (e.g. `NYNC-X9Z2`) or the full **Invite Link** and send it to your colleagues.
        3. **Join a Team:** Paste an invite code in the **Team** tab → *Join a Team*.
        4. **Ghost Members:** Add people who aren't on Nync yet as **Dummy Members** — set their timezone so their hours show up in the heatmap.
        5. **External Guests:** Add clients or contractors as **External Guests** — they'll get a link to vote on meeting times without needing an account.
        """)
        st.info("💡 You can switch between multiple teams using the dropdown at the top of the Dashboard.")

    with t2:
        st.subheader("The Pain Board")
        st.markdown("""
        The Pain Board is your team's meeting fairness tracker.

        **How pain is calculated:**
        - Every meeting gets scored based on each member's *local time* when it happens.
        - A meeting during core work hours = **0 pain**. A meeting at 3am = **10 pain**.
        - Custom working hours (set in **Settings**) shift the pain curve around your actual schedule.
        - Weekends add a flat **+8 penalty**.
        - Calendar conflicts add **+25** on top.

        **The Leaderboard:**
        Shows who has accumulated the most pain across all booked meetings — the *Ultimate Martyr* at the top.
        The goal is to use this data to rotate the burden fairly over time.

        **Voting:**
        When a poll is proposed, team members vote on the time that hurts them the least.
        The admin then books the winning slot directly as a Google Meet or Teams call.
        """)

    with t3:
        st.subheader("The Scheduler & Heatmap")
        st.markdown("""
        The **Heatmap** shows a colour-coded grid of every UTC hour vs every team member.

        - 🟢 **Green** = No pain (core work hours for that person)
        - 🟡 **Yellow** = Slightly outside hours
        - 🟠 **Orange** = Uncomfortable
        - 🔴 **Red** = Deep night / weekend / calendar conflict

        **To propose a meeting:**
        1. Click any column on the heatmap to select a time slot.
        2. Hit **🗳️ Propose as Poll** — this creates a poll on the Pain Board.
        3. The team gets notified by email (and webhook if configured).
        4. Once everyone votes, hit **📅 Book Meeting** to lock it in.

        **Auto-Find Best Times (paid tiers):**
        Nync scans up to 168 hours and ranks slots using the **karma algorithm** —
        it picks the time that's fairest across the whole team, not just lowest total pain.
        The *Fairness Gap* shown on each suggestion is the difference between the most and least burdened member.
        """)
        st.info("💡 Use **Sync Live Calendars** to refresh real-time Google/Outlook availability.")

    with t4:
        st.subheader("Integrations")
        st.markdown("""
        **Google Calendar**
        - Sign in with Google to connect your calendar automatically.
        - Nync reads your busy slots and can book Google Meet calls on your behalf.

        **Outlook / Microsoft Teams**
        - Go to **Settings** → *Connect Outlook* to link your Microsoft account.
        - Nync reads your Outlook calendar and books Teams meetings directly.

        **Webhooks (Discord / Slack)**
        - Go to the **Team** tab → *Webhook Settings*.
        - Paste a Discord or Slack webhook URL.
        - Nync will post a message whenever a new poll is proposed or a meeting is booked.

        **Guest Voting Links**
        - Any active poll has a shareable **Guest Vote Link**.
        - Clients and contractors can rate each time slot (Good / Okay / Painful) without logging in.
        - Their availability feeds into the poll results automatically.
        """)
