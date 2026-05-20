import streamlit as st
import billing_utils

PRICE_SQUAD = "price_1Smm9VIlTLkLyuizLNG57F1g"
PRICE_GUILD = "price_1SmmATIlTLkLyuizW9PcnZrN"
PRICE_EMPIRE = "price_1SmmB0IlTLkLyuiz6xySQvqd"

def show():
    st.header("💎 Upgrade Your Team")
    st.write("Stop maximizing convenience. Start minimizing pain.")

    user_tier = 'free'
    if 'user' in st.session_state and st.session_state.user:
        user_tier = billing_utils.get_user_tier(st.session_state.user.id)

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown("### 🟠 Squad")
            st.markdown("## £19/mo")
            st.divider()
            st.markdown("- 1 Team\n- **10 Members**\n- Unlimited History\n- AI Scheduling Engine")
            if user_tier == 'squad':
                st.button("Current Plan", disabled=True, use_container_width=True, key="btn_squad")
            elif user_tier in ('guild', 'empire'):
                st.button("Included", disabled=True, use_container_width=True, key="btn_squad")
            else:
                if st.button("Upgrade to Squad", type="primary", use_container_width=True, key="btn_squad"):
                    start_checkout(PRICE_SQUAD)

    with c2:
        with st.container(border=True):
            st.markdown("### 🔵 Guild")
            st.markdown("## £49/mo")
            st.divider()
            st.markdown("- 5 Teams\n- **25 Members**\n- Priority Support\n- AI Scheduling Engine")
            if user_tier == 'guild':
                st.button("Current Plan", disabled=True, use_container_width=True, key="btn_guild")
            elif user_tier == 'empire':
                st.button("Included", disabled=True, use_container_width=True, key="btn_guild")
            else:
                if st.button("Upgrade to Guild", type="primary", use_container_width=True, key="btn_guild"):
                    start_checkout(PRICE_GUILD)

    with c3:
        with st.container(border=True):
            st.markdown("### 🟣 Empire")
            st.markdown("## £99/mo")
            st.divider()
            st.markdown("- Unlimited Teams\n- **100 Members**\n- SSO / API\n- AI Scheduling Engine")
            if user_tier == 'empire':
                st.button("Current Plan", disabled=True, use_container_width=True, key="btn_empire")
            else:
                if st.button("Upgrade to Empire", type="primary", use_container_width=True, key="btn_empire"):
                    start_checkout(PRICE_EMPIRE)

def start_checkout(price_id):
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("Please log in first.")
        return

    url = billing_utils.create_stripe_checkout(
        st.session_state.user.email,
        price_id,
        success_url="https://nync.app/?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://nync.app/"
    )

    if url:
        st.link_button("👉 Click to Pay Securely", url, type="primary", use_container_width=True)
    else:
        st.error("Stripe is not configured.")
