import streamlit as st
import time
import base64
import supabase
import html
import auth_utils as auth
import extra_streamlit_components as stx
from modules import login, martyr_board, scheduler, settings, pricing, legal, vote, guide, cookie_consent, onboarding, team
import datetime as dt

# 1. SETUP
try:
    st.set_page_config(page_title="Nync", page_icon="nync_favicon.png", layout="wide", initial_sidebar_state="collapsed")
except: pass

# --- 🚨 INTERCEPT EXTERNAL GUEST LINKS ---
if "guest_poll" in st.query_params:
    poll_id = st.query_params["guest_poll"]
    from modules import guest_vote
    guest_vote.show(auth.supabase, poll_id)
    st.stop() 

# --- GLOBAL PREMIUM CSS ---
st.markdown("""
<style>
    /* Import Premium SaaS Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Elegant Dark Mode Gradient */
    .stApp { 
        background: radial-gradient(circle at top center, #171723, #000000); 
        color: #f4f4f5; 
    } 
    
    /* 🚨 COMPLETELY HIDE STREAMLIT CLUTTER (Scorched Earth Method) 🚨 */
    header { visibility: hidden !important; display: none !important; height: 0px !important; }
    .stApp > header { display: none !important; }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    
    /* Page Fade-In Animation */
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main .block-container {
        animation: slideUpFade 0.5s ease-out forwards;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }
    
    /* Beautiful Interactive Buttons */
    div.stButton > button {
        background-color: transparent; 
        color: #FFFFFF; 
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 14px; 
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 8px 16px; 
        height: auto; 
    }
    div.stButton > button:hover { 
        transform: translateY(-2px);
        background-color: #FFFFFF; 
        color: #000000;
        box-shadow: 0 6px 15px rgba(255,255,255,0.1);
    }
    
    /* Primary Action Buttons */
    div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #4f46e5 !important;
        border: none !important;
        color: white !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #6366f1 !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4) !important;
    }

    button[key="top_logout"] { color: #ef4444 !important; border-color: rgba(239, 68, 68, 0.3) !important; }
    button[key="top_logout"]:hover { background-color: #ef4444 !important; color: white !important; box-shadow: 0 6px 15px rgba(239, 68, 68, 0.3) !important;}
    
    /* Mobile Horizontal Scrolling Container for Heatmap */
    .scrollable-chart {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 15px;
    }
    .scrollable-chart::-webkit-scrollbar { height: 8px; }
    .scrollable-chart::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 4px;}
    .scrollable-chart::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }
    
    /* Python Controlled Overlay */
    .nync-fullscreen-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background-color: #000000; z-index: 9999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        backdrop-filter: blur(10px);
    }
    .nync-spinner {
        width: 50px; height: 50px; border: 3px solid rgba(255, 255, 255, 0.1);
        border-left-color: #6366f1; border-radius: 50%; animation: spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite; margin-bottom: 20px;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .nync-fullscreen-overlay h3 { color: #a1a1aa; font-weight: 500; font-size: 1.1rem; letter-spacing: 0.5px;}
</style>
""", unsafe_allow_html=True)

# 2. BULLETPROOF STATE INITIALIZATION
flags = ["session", "user", "nav", "pending_restore", "clear_cookies", "sync_cookies", "save_consent_val", "consent", "ignore_cookies"]
for f in flags:
    if f not in st.session_state: st.session_state[f] = None
        
if not st.session_state.nav: st.session_state.nav = "Dashboard"
if st.session_state.ignore_cookies is None: st.session_state.ignore_cookies = False

cookie_manager = stx.CookieManager(key="cm")
cookies = cookie_manager.get_all(key="init") or {}

if "invite" in st.query_params: st.session_state.pending_invite = st.query_params["invite"]
if "vote" in st.query_params and not st.session_state.session:
    st.session_state.pending_vote_id = st.query_params["vote"]
    if "idx" in st.query_params: st.session_state.pending_vote_idx = st.query_params["idx"]

if "code" in st.query_params:
    code = st.query_params["code"]
    state_param = st.query_params.get("state", "")
    
    if state_param.startswith("microsoft_connect"):
        try:
            parts = state_param.split(":")
            if len(parts) > 1 and auth.handle_microsoft_callback(code, parts[1]):
                st.toast("✅ Outlook Connected!")
                st.session_state.nav = "Dashboard"
        except: pass
        st.query_params.clear(); st.rerun()
    else:
        try:
            res = auth.supabase.auth.exchange_code_for_session({"auth_code": code})
            if res and res.session:
                st.session_state.session = res.session
                st.session_state.user = res.user
                auth.save_google_token(res.user.id, res.session)
                st.session_state.sync_cookies = True 
                st.session_state.ignore_cookies = False
        except Exception as e: 
            st.error(f"Login Failed: {e}")
        st.query_params.clear(); st.rerun()

if not st.session_state.session and not st.session_state.clear_cookies and not st.session_state.pending_restore and not st.session_state.ignore_cookies:
    if cookies.get("sb_access_token") and cookies.get("sb_refresh_token"):
        st.session_state.pending_restore = True; st.rerun()

if st.session_state.session and not st.session_state.clear_cookies and not st.session_state.sync_cookies:
    if cookies.get("sb_access_token") and st.session_state.session.access_token != cookies.get("sb_access_token"):
        st.session_state.sync_cookies = True; st.rerun()

is_loading = False
load_msg = ""
if st.session_state.pending_restore: is_loading, load_msg = True, "Restoring session..."
elif st.session_state.clear_cookies: is_loading, load_msg = True, "Logging out safely..."
elif st.session_state.sync_cookies: is_loading, load_msg = True, "Securing session..."
elif st.session_state.save_consent_val: is_loading, load_msg = True, "Saving preferences..."

if is_loading:
    st.markdown(f"<div class='nync-fullscreen-overlay'><div class='nync-spinner'></div><h3>{load_msg}</h3></div>", unsafe_allow_html=True)
    if st.session_state.pending_restore:
        st.session_state.pending_restore = False
        acc, ref = cookies.get("sb_access_token"), cookies.get("sb_refresh_token")
        if acc and ref:
            session = auth.restore_session(acc, ref)
            if session: st.session_state.session, st.session_state.user, st.session_state.sync_cookies = session, session.user, True 
            else: st.session_state.clear_cookies = True 
        else: st.session_state.clear_cookies = True
        time.sleep(0.5); st.rerun()
    elif st.session_state.clear_cookies:
        st.session_state.clear_cookies = False
        t_key = str(time.time()).replace(".", "")
        try: cookie_manager.delete("sb_access_token", key=f"del_acc_{t_key}"); cookie_manager.delete("sb_refresh_token", key=f"del_ref_{t_key}")
        except: pass
        time.sleep(0.8); st.rerun()
    elif st.session_state.sync_cookies:
        st.session_state.sync_cookies = False
        if st.session_state.session:
            expires = dt.datetime.now() + dt.timedelta(days=30)
            t_key = str(time.time()).replace(".", "")
            cookie_manager.set("sb_access_token", st.session_state.session.access_token, expires_at=expires, key=f"set_acc_{t_key}")
            cookie_manager.set("sb_refresh_token", st.session_state.session.refresh_token, expires_at=expires, key=f"set_ref_{t_key}")
        time.sleep(0.8); st.rerun()
    elif st.session_state.save_consent_val:
        val = st.session_state.save_consent_val
        st.session_state.save_consent_val = None
        expires = dt.datetime.now() + dt.timedelta(days=365)
        t_key = str(time.time()).replace(".", "")
        cookie_manager.set("nync_consent", val, expires_at=expires, key=f"set_cons_{t_key}")
        st.session_state.consent = val
        time.sleep(0.8); st.rerun()
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
    st.query_params.clear(); st.rerun()

cookie_consent.show(cookies)

if not st.session_state.session:
    if st.query_params.get("nav") == "Legal":
        from modules import legal
        legal.show()
        st.write("")
        if st.button("← Back to Login", type="primary"):
            st.query_params.clear()
            st.rerun()
    else:
        login.show()
        if st.session_state.session: 
            st.session_state.sync_cookies = True
            st.session_state.ignore_cookies = False
            st.rerun()
else:
    if 'pending_invite' in st.session_state:
        code = st.session_state.pending_invite
        if auth.join_team_by_code(st.session_state.user.id, code): st.toast(f"✅ Joined Team!")
        else: st.toast("❌ Invalid Invite Code")
        del st.session_state.pending_invite
        if "invite" in st.query_params: st.query_params.clear()
        time.sleep(1); st.rerun()

    if "vote" in st.query_params: vote.show(st.query_params["vote"], auth.supabase); st.stop()
        
    user_consent = st.session_state.get('consent')
    profile = auth.get_user_profile(st.session_state.user.id)
    tier = profile.get('subscription_tier', 'free').upper() if profile else "FREE"

    if tier == "FREE" and user_consent == "accepted":
        st.info("💡 **Tip:** Upgrade to **Squad Tier** to remove ads and unlock unlimited teams. [View Pricing](#)", icon="🚀")

    c_logo, c_nav, c_user = st.columns([1, 7, 1.2], vertical_alignment="center")
    
    with c_logo:
        try:
            with open("nync_marketing.png", "rb") as f: img_data = base64.b64encode(f.read()).decode()
            # 🚨 APPLIED THE WHITE-LOGO FILTER TO THE INNER NAVBAR TOO 🚨
            st.markdown(f"<a href='/' target='_self'><img src='data:image/png;base64,{img_data}' width='65' style='cursor:pointer; filter: brightness(0) invert(1);'></a>", unsafe_allow_html=True)
        except:
            if st.button("⚡ Nync.", type="secondary"): st.session_state.nav = "Dashboard"; st.rerun()

    with c_nav:
        tabs = ["Dashboard", "Team", "Settings", "Pricing", "Guide", "Legal"]
        selected_tab = st.segmented_control("Navigation", options=tabs, default=st.session_state.nav, label_visibility="collapsed", selection_mode="single")
        if selected_tab and selected_tab != st.session_state.nav:
            st.session_state.nav = selected_tab
            st.rerun()

    with c_user:
        if st.button("Log Out", key="top_logout", use_container_width=True):
            auth.supabase.auth.sign_out()
            st.session_state.session = None
            st.session_state.user = None
            st.session_state.clear_cookies = True 
            st.session_state.ignore_cookies = True 
            st.rerun()
    
    st.markdown("<hr style='margin-top: 5px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    nav = st.session_state.nav

    if nav == "Dashboard":
        my_teams = auth.get_user_teams(st.session_state.user.id)
        has_cal = auth.check_calendar_connected(st.session_state.user.id)
        
        if not my_teams or not has_cal: onboarding.show(st.session_state.user, auth.supabase, has_cal, bool(my_teams))
        else:
            if 'active_team' not in st.session_state or st.session_state.active_team not in my_teams:
                st.session_state.active_team = list(my_teams.keys())[0]
            
            st.session_state.active_team_id = my_teams[st.session_state.active_team]
            status = auth.check_team_status(st.session_state.active_team_id)
            
            tier_color = "#666" 
            if tier == "SQUAD": tier_color = "#f59e0b"
            if tier == "GUILD": tier_color = "#3b82f6"
            if tier == "EMPIRE": tier_color = "#8b5cf6"

            safe_team = html.escape(st.session_state.active_team)
            badge_html = f"<span style='background-color:{tier_color}; color:white; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; letter-spacing:0.5px; vertical-align:middle; margin-left:10px;'>{tier}</span>"

            if len(my_teams) > 1:
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"<h3 style='margin-bottom:20px;'>{safe_team} {badge_html}</h3>", unsafe_allow_html=True)
                new = c2.selectbox("Switch Team", list(my_teams.keys()), label_visibility="collapsed")
                if new != st.session_state.active_team:
                    st.session_state.active_team = new
                    st.rerun()
            else:
                st.markdown(f"<h3 style='margin-bottom:20px;'>{safe_team} {badge_html}</h3>", unsafe_allow_html=True)

            if status == 'locked':
                st.error("Team Locked (Trial Expired)")
                if st.button("Upgrade", type="primary"): st.session_state.nav = "Pricing"; st.rerun()
            else:
                roster = auth.get_team_roster(st.session_state.active_team_id)
                t1, t2 = st.tabs(["🪧 Pain Board", "🗓️ Scheduler (Heatmap)"])
                with t1: martyr_board.show(auth.supabase, st.session_state.active_team_id)
                with t2: scheduler.show(auth.supabase, st.session_state.user, roster)
                
    elif nav == "Team": team.show(st.session_state.user, auth.supabase)
    elif nav == "Settings": settings.show(st.session_state.user, auth.supabase, cookie_manager)
    elif nav == "Pricing": pricing.show()
    elif nav == "Guide": guide.show()
    elif nav == "Legal": legal.show()