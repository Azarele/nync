import streamlit as st
import time
import base64
import html  # Added for Security (XSS)
import auth_utils as auth
from modules import login, martyr_board, scheduler, settings, pricing, legal, vote

# 1. SETUP
favicon = "nync_favicon.png" 
st.set_page_config(page_title="Nync", page_icon=favicon, layout="wide", initial_sidebar_state="collapsed")

# --- CSS: UI CLEANUP & STYLING ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #000000; color: white; } 
    
    /* Hide Sidebar Elements */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }

    /* --- UI POLISH (THE FIX) --- */
    
    /* 1. NUCLEAR OPTION: Hide Fullscreen Buttons on Images */
    button[title="View fullscreen"], 
    [data-testid="StyledFullScreenButton"],
    [data-testid="stImage"] button {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    
    /* 2. Hide the Anchor Link icons next to headers */
    [data-testid="stHeaderAction"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* --- NAV BUTTON STYLES --- */
    div.stButton > button {
        background-color: transparent;
        color: #FFFFFF;
        border: 1px solid #FFFFFF;
        border-radius: 4px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        padding: 6px 16px;
        height: auto;
        margin-top: 4px;
    }
    div.stButton > button:hover {
        color: #000000;
        background-color: #FFFFFF;
        border-color: #FFFFFF;
    }
    div.stButton > button:focus {
        color: #FFFFFF;
        background-color: transparent;
        border-color: #FFFFFF;
        box-shadow: none;
    }
    button[key="top_logout"] {
        color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }
    button[key="top_logout"]:hover {
        background-color: #ff4b4b !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. SESSION INIT
if 'session' not in st.session_state: st.session_state.session = None
if 'user' not in st.session_state: st.session_state.user = None
if 'nav' not in st.session_state: st.session_state.nav = "Dashboard"

# --- VOTE STASHING LOGIC ---
if "vote" in st.query_params and not st.session_state.session:
    st.session_state.pending_vote_id = st.query_params["vote"]
    if "idx" in st.query_params:
        st.session_state.pending_vote_idx = st.query_params["idx"]

# 3. AUTH LOGIC
if "invite" in st.query_params: st.session_state.pending_invite = st.query_params["invite"]

# --- STRIPE CALLBACK HANDLER ---
if "stripe_session_id" in st.query_params:
    session_id = st.query_params["stripe_session_id"]
    st.toast("🔄 Verifying Payment...")
    
    price_id = auth.verify_stripe_payment(session_id)
    
    if price_id:
        new_tier = "paid" 
        
        # YOUR REAL PRICE IDs
        if price_id == "price_1Smm9VIlTLkLyuizLNG57F1g": new_tier = "squad"
        elif price_id == "price_1SmmATIlTLkLyuizW9PcnZrN": new_tier = "guild"
        elif price_id == "price_1SmmB0IlTLkLyuiz6xySQvqd": new_tier = "empire"
        
        if not st.session_state.user:
             auth.restore_session_from_cookies()

        if st.session_state.user:
            if auth.upgrade_user_tier(st.session_state.user.id, new_tier):
                st.balloons()
                st.success(f"🎉 Upgrade Successful! You are now on the {new_tier.title()} plan.")
                time.sleep(3)
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Payment verified, but database update failed.")
        else:
             st.warning("Payment successful, but lost login session. Please log in again to see changes.")
    else:
        st.error("❌ Payment verification failed.")
        st.query_params.clear()


if "code" in st.query_params:
    code = st.query_params["code"]
    state = st.query_params.get("state", None)

    if state == "microsoft_connect":
        if not st.session_state.session:
            auth.restore_session_from_cookies()
            
        if st.session_state.session:
            st.toast("🔄 Finishing Outlook connection...")
            if auth.handle_microsoft_callback(code, st.session_state.user.id):
                st.success("✅ Outlook Connected!")
                time.sleep(1)
            else: st.error("❌ Connection failed.")
            st.query_params.clear()
            st.rerun()

    elif not state: 
        try:
            res = auth.supabase.auth.exchange_code_for_session({"auth_code": code})
            st.session_state.session = res.session
            st.session_state.user = res.user
            auth.save_session_to_cookies(res.session)
            
            if "ms_stash" in st.query_params:
                st.toast("🔄 Resuming Outlook Connection...")
                if auth.handle_microsoft_callback(st.query_params["ms_stash"], st.session_state.user.id):
                    st.success("✅ Outlook Connected!")
                    time.sleep(1)
            st.query_params.clear()
            st.rerun()
        except: st.query_params.clear()

if not st.session_state.session and "code" not in st.query_params:
    auth.restore_session_from_cookies()

# --- VOTE RESTORATION LOGIC ---
if st.session_state.session and "pending_vote_id" in st.session_state:
    params = {"vote": st.session_state.pending_vote_id}
    if "pending_vote_idx" in st.session_state:
        params["idx"] = st.session_state.pending_vote_idx
    
    del st.session_state.pending_vote_id
    if "pending_vote_idx" in st.session_state: del st.session_state.pending_vote_idx
    
    st.query_params.update(params)
    st.rerun()

# B: LOGIN PAGE (If not logged in)
if not st.session_state.session:
    login.show()

# C: DASHBOARD (Logged In)
else:
    # 1. Handle Pending Invites
    if 'pending_invite' in st.session_state:
        auth.join_team_by_code(st.session_state.user.id, st.session_state.pending_invite)
        del st.session_state.pending_invite
        st.query_params.clear()
        st.rerun()

    # 2. Check for Voting (Strict Mode: Must be logged in)
    if "vote" in st.query_params:
        vote.show(st.query_params["vote"], auth.supabase)
        st.stop() # Hide the rest of the dashboard so they focus on voting

    # --- TOP NAV BAR ---
    c_logo, c_dash, c_set, c_price, c_legal, c_spacer, c_user = st.columns([0.8, 1, 1, 1, 1, 3, 1.2], gap="small")
    
    with c_logo:
        # CLICKABLE LOGO LOGIC
        try:
            with open("nync_marketing.png", "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            
            st.markdown(f"""
                <a href="/" target="_self" style="text-decoration: none;">
                    <img src="data:image/png;base64,{img_data}" width="80" style="margin-top: 5px; cursor: pointer;">
                </a>
            """, unsafe_allow_html=True)
        except:
            if st.button("⚡ Nync.", type="secondary"): 
                st.session_state.nav = "Dashboard"
                st.rerun()

    with c_dash:
        if st.button("Dashboard", use_container_width=True): st.session_state.nav = "Dashboard"
    with c_set:
        if st.button("Settings", use_container_width=True): st.session_state.nav = "Settings"
    with c_price:
        if st.button("Pricing", use_container_width=True): st.session_state.nav = "Pricing"
    with c_legal:
        if st.button("Legal", use_container_width=True): st.session_state.nav = "Legal"

    with c_user:
        if st.button("Log Out", key="top_logout", use_container_width=True):
            auth.supabase.auth.sign_out()
            auth.clear_cookies()
            st.session_state.session = None
            st.rerun()

    st.markdown("<hr style='margin-top: 10px; border-color: #333;'>", unsafe_allow_html=True)

    nav = st.session_state.nav

    if nav == "Dashboard":
        my_teams = auth.get_user_teams(st.session_state.user.id)
        if 'active_team' not in st.session_state or not st.session_state.active_team or st.session_state.active_team not in my_teams:
            if my_teams:
                first = list(my_teams.keys())[0]
                st.session_state.active_team = first
                st.session_state.active_team_id = my_teams[first]
                st.rerun()
            else: st.session_state.active_team = None

        if not st.session_state.active_team:
            st.info("👈 Create a Team in Settings.")
        else:
            st.session_state.active_team_id = my_teams[st.session_state.active_team]
            status = auth.check_team_status(st.session_state.active_team_id)
            
            # --- TIER BADGE & XSS PROTECTION ---
            profile = auth.get_user_profile(st.session_state.user.id)
            user_tier = profile.get('subscription_tier', 'free').upper()
            tier_color = "grey"
            if user_tier == "SQUAD": tier_color = "orange"
            if user_tier == "GUILD": tier_color = "blue"
            if user_tier == "EMPIRE": tier_color = "violet"
            
            # Sanitize inputs to prevent XSS attacks
            safe_team_name = html.escape(st.session_state.active_team)
            safe_tier_name = html.escape(user_tier)

            st.markdown(f"### {safe_team_name} <span style='background-color:#333; color:{tier_color}; padding:2px 8px; border-radius:4px; font-size:12px; vertical-align:middle;'>{safe_tier_name}</span>", unsafe_allow_html=True)
            
            if status == 'locked':
                st.title("🔒 Team Locked")
                st.error("Your 14-day trial has ended.")
                st.button("💎 Upgrade Now", type="primary")
            else:
                roster = auth.get_team_roster(st.session_state.active_team_id)
                t1, t2 = st.tabs(["Pain Board", "Scheduler"])
                with t1: martyr_board.show(auth.supabase, st.session_state.user, roster)
                with t2: scheduler.show(auth.supabase, st.session_state.user, roster)

    elif nav == "Settings":
        settings.show(st.session_state.user, auth.supabase)
    elif nav == "Pricing":
        pricing.show()
    elif nav == "Legal":
        legal.show()