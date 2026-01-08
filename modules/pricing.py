import streamlit as st
import auth_utils as auth

def show():
    # --- HEADER REMOVED ---
    
    st.header("💎 Upgrade Your Team")
    st.write("Stop maximizing convenience. Start minimizing pain.")
    
    # REAL PRICE IDs (Ensure these match your Stripe Dashboard)
    PRICE_SQUAD = "price_1Smm9VIlTLkLyuizLNG57F1g" 
    PRICE_GUILD = "price_1SmmATIlTLkLyuizW9PcnZrN" 
    PRICE_EMPIRE = "price_1SmmB0IlTLkLyuiz6xySQvqd"

    # GET CURRENT USER STATUS
    user_tier = "free"
    if 'user' in st.session_state and st.session_state.user:
        profile = auth.get_user_profile(st.session_state.user.id)
        if profile:
            user_tier = profile.get('subscription_tier', 'free')

    current_level = auth.get_tier_level(user_tier)

    c1, c2, c3, c4 = st.columns(4)
    
    # 1. FREE
    with c1:
        st.subheader("Free")
        st.markdown("## $0/mo")
        st.divider()
        st.markdown("* 1 Team\n* 3 Members Max\n* 14-Day History")
        
        if current_level == 0:
            st.button("Current Plan", disabled=True, width="stretch", key="btn_free")
        else:
            st.button("Included", disabled=True, width="stretch", key="btn_free")

    # 2. SQUAD
    with c2:
        st.markdown("### :orange[Squad]")
        st.markdown("## $19/mo")
        st.divider()
        st.markdown("* 1 Team\n* **10 Members**\n* **Unlimited History**")
        
        if current_level == 1:
            st.button("Current Plan", disabled=True, width="stretch", key="btn_squad")
        elif current_level > 1:
            st.button("Included", disabled=True, width="stretch", key="btn_squad")
        else:
            if st.button("Upgrade to Squad", type="primary", width="stretch", key="btn_squad"):
                start_checkout(PRICE_SQUAD)

    # 3. GUILD
    with c3:
        st.subheader("Guild")
        st.markdown("## $49/mo")
        st.divider()
        st.markdown("* **5 Teams**\n* **50 Members**\n* Priority Support")
        
        if current_level == 2:
            st.button("Current Plan", disabled=True, width="stretch", key="btn_guild")
        elif current_level > 2:
            st.button("Included", disabled=True, width="stretch", key="btn_guild")
        else:
            if st.button("Upgrade to Guild", width="stretch", key="btn_guild"):
                start_checkout(PRICE_GUILD)
            
    # 4. EMPIRE
    with c4:
        st.subheader("Empire")
        st.markdown("## $99/mo")
        st.divider()
        st.markdown("* **Unlimited Teams**\n* **Unlimited Members**\n* SSO / API")
        
        if current_level == 3:
            st.button("Current Plan", disabled=True, width="stretch", key="btn_empire")
        else:
            if st.button("Upgrade to Empire", width="stretch", key="btn_empire"):
                start_checkout(PRICE_EMPIRE)

def start_checkout(price_id):
    """Helper to initiate Stripe flow"""
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("Please log in first.")
        return
        
    url = auth.create_stripe_checkout(
        st.session_state.user.email, 
        price_id,
        success_url="https://nyncapp.streamlit.app/?stripe_session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://nyncapp.streamlit.app/?stripe_cancel=true"
    )

    if url:
        st.link_button("👉 Click to Pay Securely", url, type="primary", use_container_width=True)
    else:
        st.error("Stripe is not configured.")
