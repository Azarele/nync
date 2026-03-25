import streamlit as st
import time
import base64
import html
import auth_utils as auth
import extra_streamlit_components as stx
from modules import login, martyr_board, scheduler, settings, pricing, legal, vote, guide, cookie_consent, onboarding
import datetime as dt

# 1. SETUP
try:
    st.set_page_config(page_title="Nync", page_icon="nync_favicon.png", layout="wide", initial_sidebar_state="collapsed")
except:
    pass

st.markdown("""
<style>
    .stApp { background-color: #000000; color: white; } 
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    button[title="View fullscreen"], [data-testid="StyledFullScreenButton"], [data-testid="stImage"] button {
        display: none !important; visibility: hidden !important; pointer-events: none !important;
    }
    [data-testid="stHeaderAction"] { display: none !important; }
    div.stButton > button {
        background-color: transparent; color: #FFFFFF; border: 1px solid #FFFFFF;
        border-radius: 4px; font-weight: 500; font-size: 14px; transition: all 0.2s ease;
        padding: 6px 16px; height: auto; margin-top: 4px;
    }
    div.stButton > button:hover { color: #000000; background-color: #FFFFFF; border-color: #FFFFFF; }
    button[key="top_logout"] { color: #ff4b4b !important; border-color: #ff4b4b !important; }
    button[key="top_logout"]:hover { background-color: #ff4b4b !important; color: white !important; }
    
    /* CSS-ONLY STARTUP LOADER */
    .startup-loader {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background-color: #000000; z-index: 9999998;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        animation: fadeOut 0.5s ease-out 1.3s forwards; 
        pointer-events: none;
    }
    @keyframes fadeOut { to { opacity: 0; visibility: hidden; } }
    
    /* PYTHON CONTROLLED OVERLAY */
    .nync-fullscreen-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background-color: #000000; z-index: 9999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .nync-spinner {
        width: 60px; height: 60px; border: 4px solid rgba(255, 255, 255, 0.1);
        border-left-color: #ffffff; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .nync-fullscreen-overlay h3, .startup-loader h3 { color: #888; font-weight: 400; margin: 0; font-family: sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='startup-loader'><div class='nync-spinner'></div><h3>Loading Nync...</h3></div>", unsafe_allow_html=True)

# 2. BULLETPROOF STATE INITIALIZATION
flags = [
    "session", "user", "nav",
    "pending_restore", "clear_cookies", "sync_cookies", "save_consent_val",
    "consent", "ignore_cookies"
]
for f in flags:
    if f not in st.session_state:
        st.session_state[f] = None
        
if not st.session_state.nav: 
    st.session_state.nav = "Dashboard"
if st.session_state.ignore_cookies is None:
    st.session_state.ignore_cookies = False

# 3. INIT COOKIE MANAGER
cookie_manager = stx.CookieManager(key="cm")
cookies = cookie_manager.get_all(key="init") or {}

# =====================================================================
# NEW: CATCH URL PARAMS IMMEDIATELY BEFORE OAUTH CLEARS THEM
# =====================================================================
if "invite" in st.query_params: 
    st.session_state.pending_invite = st.query_params["invite"]

if "vote" in st.query_params and not st.session_state.session:
    st.session_state.pending_vote_id = st.query_params["vote"]
    if "idx" in st.query_params: st.session_state.pending_vote_idx = st.query_params["idx"]

# =====================================================================
# STEP 1: OAUTH CALLBACKS
# =====================================================================
if "code" in st.query_params:
    code = st.query_params["code"]
    state_param = st.query_params.get("state", "")
    
    if state_param.startswith("microsoft_connect"):
        try:
            parts = state_param.split(":")
            if len(parts) > 1 and auth.handle_microsoft_callback(code, parts[1]):
                st.toast("✅ Outlook Connected!")
                st.session_state.nav = "Settings"
        except: pass
        st.query_params.clear()
        st.rerun()
    else:
        try:
            res = auth.supabase.auth.exchange_code_for_session({"auth_code": code})
            if res and res.session:
                st.session_state.session = res.session
                st.session_state.user = res.user
                auth.save_google_token(res.user.id, res.session)
                st.session_state.sync_cookies = True 
                st.session_state.ignore_cookies = False
        except:
            st.error("Login Failed.")
        st.query_params.clear()
        st.rerun()

# =====================================================================
# STEP 2: CHECK FOR EXISTING SESSION COOKIES TO RESTORE
# =====================================================================
if not st.session_state.session and not st.session_state.clear_cookies and not st.session_state.pending_restore and not st.session_state.ignore_cookies:
    acc = cookies.get("sb_access_token")
    ref = cookies.get("sb_refresh_token")
    if acc and ref:
        st.session_state.pending_restore = True
        st.rerun()

# =====================================================================
# STEP 3: TOKEN ROTATION CHECK
# =====================================================================
if st.session_state.session and not st.session_state.clear_cookies and not st.session_state.sync_cookies:
    mem_acc = st.session_state.session.access_token
    cook_acc = cookies.get("sb_access_token")
    if cook_acc and mem_acc != cook_acc:
        st.session_state.sync_cookies = True
        st.rerun()

# =====================================================================
# STEP 4: LOADER STATE MACHINE (Executes background actions safely)
# =====================================================================
is_loading = False
load_msg = ""

if st.session_state.pending_restore:
    is_loading, load_msg = True, "Restoring session..."
elif st.session_state.clear_cookies:
    is_loading, load_msg = True, "Logging out safely..."
elif st.session_state.sync_cookies:
    is_loading, load_msg = True, "Securing session..."
elif st.session_state.save_consent_val:
    is_loading, load_msg = True, "Saving preferences..."

if is_loading:
    st.markdown(f"<div class='nync-fullscreen-overlay'><div class='nync-spinner'></div><h3>{load_msg}</h3></div>", unsafe_allow_html=True)
    
    if st.session_state.pending_restore:
        st.session_state.pending_restore = False
        acc = cookies.get("sb_access_token")
        ref = cookies.get("sb_refresh_token")
        
        if acc and ref:
            session = auth.restore_session(acc, ref)
            if session:
                st.session_state.session = session
                st.session_state.user = session.user
                st.session_state.sync_cookies = True 
            else:
                st.session_state.clear_cookies = True 
        else:
            st.session_state.clear_cookies = True
            
        time.sleep(0.5)
        st.rerun()
        
    elif st.session_state.clear_cookies:
        st.session_state.clear_cookies = False
        t_key = str(time.time()).replace(".", "")
        if "sb_access_token" in cookies:
            try: cookie_manager.delete("sb_access_token", key=f"del_acc_{t_key}")
            except: pass
        if "sb_refresh_token" in cookies:
            try: cookie_manager.delete("sb_refresh_token", key=f"del_ref_{t_key}")
            except: pass
        time.sleep(0.8)
        st.rerun()

    elif st.session_state.sync_cookies:
        st.session_state.sync_cookies = False
        if st.session_state.session:
            mem_acc = st.session_state.session.access_token
            mem_ref = st.session_state.session.refresh_token
            remember = st.session_state.get("remember_me", True)
            expires = dt.datetime.now() + dt.timedelta(days=30) if remember else None
            
            t_key = str(time.time()).replace(".", "")
            cookie_manager.set("sb_access_token", mem_acc, expires_at=expires, key=f"set_acc_{t_key}")
            cookie_manager.set("sb_refresh_token", mem_ref, expires_at=expires, key=f"set_ref_{t_key}")
        time.sleep(0.8)
        st.rerun()

    elif st.session_state.save_consent_val:
        val = st.session_state.save_consent_val
        st.session_state.save_consent_val = None
        expires = dt.datetime.now() + dt.timedelta(days=365)
        t_key = str(time.time()).replace(".", "")
        cookie_manager.set("nync_consent", val, expires_at=expires, key=f"set_cons_{t_key}")
        st.session_state.consent = val
        time.sleep(0.8)
        st.rerun()
        
    st.stop()

# =====================================================================
# UI RENDERING
# =====================================================================

if "stripe_session_id" in st.query_params and st.session_state.user:
    price_id = auth.verify_stripe_payment(st.query_params["stripe_session_id"])
    if price_id:
        new_tier = "paid" 
        if price_id == "price_1Smm9VIlTLkLyuizLNG57F1g": new_tier = "squad"
        elif price_id == "price_1SmmATIlTLkLyuizW9PcnZrN": new_tier = "guild"
        elif price_id == "price_1SmmB0IlTLkLyuiz6xySQvqd": new_tier = "empire"
        auth.upgrade_user_tier(st.session_state.user.id, new_tier)
        st.toast("🎉 Plan Updated!")
        time.sleep(2)
    st.query_params.clear()
    st.rerun()

cookie_consent.show(cookies)

if not st.session_state.session:
    login.show()
    if st.session_state.session:
        st.session_state.sync_cookies = True
        st.session_state.ignore_cookies = False 
        st.rerun()
else:
    # Handle the stored invite code from the URL
    if 'pending_invite' in st.session_state:
        code = st.session_state.pending_invite
        if auth.join_team_by_code(st.session_state.user.id, code):
            st.toast(f"✅ Joined Team!")
        else:
            st.toast("❌ Invalid Invite Code")
        del st.session_state.pending_invite
        if "invite" in st.query_params:
            st.query_params.clear()
        time.sleep(1)
        st.rerun()

    if "vote" in st.query_params:
        vote.show(st.query_params["vote"], auth.supabase)
        st.stop()
        
    user_consent = st.session_state.get('consent')
    profile = auth.get_user_profile(st.session_state.user.id)
    tier = profile.get('subscription_tier', 'free').upper() if profile else "FREE"

    if tier == "FREE" and user_consent == "accepted":
        st.info("💡 **Tip:** Upgrade to **Squad Tier** to remove ads and unlock unlimited teams. [View Pricing](#)", icon="🚀")

    c_logo, c_dash, c_set, c_price, c_guide, c_legal, c_spacer, c_user = st.columns([0.8, 1, 1, 1, 1, 1, 2, 1.2], gap="small")
    
    with c_logo:
        try:
            with open("nync_marketing.png", "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            st.markdown(f"<a href='/' target='_self'><img src='data:image/png;base64,{img_data}' width='80' style='margin-top:5px;cursor:pointer;'></a>", unsafe_allow_html=True)
        except:
            if st.button("⚡ Nync.", type="secondary"): st.session_state.nav = "Dashboard"; st.rerun()

    with c_dash:
        if st.button("Dashboard", use_container_width=True): st.session_state.nav = "Dashboard"
    with c_set:
        if st.button("Settings", use_container_width=True): st.session_state.nav = "Settings"
    with c_price:
        if st.button("Pricing", use_container_width=True): st.session_state.nav = "Pricing"
    with c_guide:
        if st.button("Guide", use_container_width=True): st.session_state.nav = "Guide"
    with c_legal:
        if st.button("Legal", use_container_width=True): st.session_state.nav = "Legal"

    with c_user:
        if st.button("Log Out", key="top_logout", use_container_width=True):
            auth.supabase.auth.sign_out()
            st.session_state.session = None
            st.session_state.user = None
            st.session_state.clear_cookies = True 
            st.session_state.ignore_cookies = True 
            st.rerun()
    
    st.markdown("<hr style='margin-top: 10px; border-color: #333;'>", unsafe_allow_html=True)

    nav = st.session_state.nav

    if nav == "Dashboard":
        my_teams = auth.get_user_teams(st.session_state.user.id)
        has_cal = auth.check_calendar_connected(st.session_state.user.id)
        
        if not my_teams or not has_cal:
            onboarding.show(st.session_state.user, auth.supabase, has_cal, bool(my_teams))
        else:
            if 'active_team' not in st.session_state or st.session_state.active_team not in my_teams:
                st.session_state.active_team = list(my_teams.keys())[0]
            
            st.session_state.active_team_id = my_teams[st.session_state.active_team]
            status = auth.check_team_status(st.session_state.active_team_id)
            
            tier_color = "#666" 
            if tier == "SQUAD": tier_color = "#ff8c00"
            if tier == "GUILD": tier_color = "#1e90ff"
            if tier == "EMPIRE": tier_color = "#9932cc"

            safe_team = html.escape(st.session_state.active_team)
            badge_html = f"<span style='background-color:{tier_color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px; vertical-align:middle; margin-left:10px;'>{tier}</span>"

            if len(my_teams) > 1:
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"### {safe_team} {badge_html}", unsafe_allow_html=True)
                new = c2.selectbox("Switch Team", list(my_teams.keys()), label_visibility="collapsed")
                if new != st.session_state.active_team:
                    st.session_state.active_team = new
                    st.rerun()
            else:
                st.markdown(f"### {safe_team} {badge_html}", unsafe_allow_html=True)

            if status == 'locked':
                st.error("Team Locked (Trial Expired)")
                if st.button("Upgrade"): st.session_state.nav = "Pricing"; st.rerun()
            else:
                roster = auth.get_team_roster(st.session_state.active_team_id)
                t1, t2 = st.tabs(["Pain Board", "Scheduler"])
                with t1: martyr_board.show(auth.supabase, st.session_state.active_team_id)
                with t2: scheduler.show(auth.supabase, st.session_state.user, roster)

    elif nav == "Settings": settings.show(st.session_state.user, auth.supabase, cookie_manager)
    elif nav == "Pricing": pricing.show()
    elif nav == "Guide": guide.show()
    elif nav == "Legal": legal.show()