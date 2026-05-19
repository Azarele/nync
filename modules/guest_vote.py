import streamlit as st
import datetime as dt
import pytz
import base64

RATING_PAIN = {"✅ Good": 0, "⚠️ Okay": 5, "❌ Painful": 10}

def show(supabase, poll_id):
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none !important;}
            [data-testid="collapsedControl"] {display: none !important;}
            .stApp header {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    try:
        with open("nync_marketing.png", "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"<div style='text-align:center;'><img src='data:image/png;base64,{img_data}' width='72' style='filter:brightness(0) invert(1);'></div>",
            unsafe_allow_html=True
        )
    except:
        st.markdown("<h2 style='text-align:center; color:#4f46e5;'>⚡ Nync</h2>", unsafe_allow_html=True)

    try:
        poll_res = supabase.table('polls').select('status, teams(name)').eq('id', poll_id).maybe_single().execute()
        if not poll_res.data:
            st.error("This meeting link is invalid or has expired.")
            return

        if poll_res.data['status'] != 'active':
            st.warning("This meeting poll has already been closed.")
            return

        team_name = poll_res.data['teams']['name']

        st.markdown(
            f"<h3 style='text-align:center; margin-top:20px;'><b>{team_name}</b> wants to meet with you.</h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; color:#a1a1aa;'>Rate each proposed time so we can find what works best for everyone.</p>",
            unsafe_allow_html=True
        )
        st.divider()

        if st.session_state.get('guest_voted', False):
            st.balloons()
            st.success("🎉 Your responses have been recorded. You can safely close this tab.")
            return

        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.caption("🌍 Times shown in **UTC**")
            guest_name = st.text_input("Your Name", placeholder="e.g. Jane Doe")
            guest_email = st.text_input("Your Email", placeholder="e.g. jane@company.com")

            if guest_name and guest_email:
                opts_res = supabase.table('poll_options').select('id, slot_time').eq('poll_id', poll_id).order('slot_time').execute()

                if not opts_res.data:
                    st.info("No time slots have been proposed yet.")
                    return

                st.write("")
                ratings = {}

                for opt in opts_res.data:
                    utc_time = dt.datetime.fromisoformat(opt['slot_time']).replace(tzinfo=pytz.UTC)
                    display_time = utc_time.strftime("%A, %B %d · %H:%M UTC")

                    with st.container(border=True):
                        st.markdown(f"**{display_time}**")
                        rating = st.radio(
                            "Rate this time",
                            options=list(RATING_PAIN.keys()),
                            key=f"rating_{opt['id']}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        ratings[opt['id']] = rating

                st.write("")
                if st.button("Submit Votes", type="primary", use_container_width=True):
                    for opt_id, rating in ratings.items():
                        if rating != "❌ Painful":
                            supabase.table('poll_votes').insert({
                                'poll_id': poll_id,
                                'option_id': opt_id,
                                'voter_name': f"{guest_name.strip()} ({guest_email.strip()}) - {rating}"
                            }).execute()
                    st.session_state.guest_voted = True
                    st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {e}")
