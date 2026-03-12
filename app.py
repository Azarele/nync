import streamlit as st
import time
import base64
import html
import auth_utils as auth
import extra_streamlit_components as stx
from modules import login, martyr_board, scheduler, settings, pricing, legal, vote, guide, cookie_consent
import datetime as dt

# 1. SETUP
try:
    st.set_page_config(page_title="Nync", page_icon="nync_favicon.png", layout="wide", initial_sidebar_state="collapsed")
except:
    st.set_page_config(page_title="Nync", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- CSS STYLES ---
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
</style>
""", unsafe_allow_html=True)

# 2. INIT COOKIE MANAGER
cookie_manager = stx.CookieManager(key="cm")
time.sleep(0.1) 
all_cookies = cookie_manager.get_all(key="init_get")

# 3. STATE INIT
if 'session' not in st.session_state: st.session_state.session = None
if 'user' not in st.session_state: st.session_state.user = None
if 'nav' not in st.session_state: st.session_state.nav = "Dashboard"
if 'consent' not in st.session_state: st.session_state.consent = None 
if 'consent_pending_save' not in st.session_state: st.session_state.consent_pending_save = False
if 'logout_pending' not in st.session_state: st.session_state.logout_pending = False

# 4. PENDING DELETES & SAVES 
# By placing these at the top, we guarantee Streamlit renders the component to the DOM.
if st.session_state.logout_pending:
    if "sb_access_token" in all_cookies: cookie_manager.delete("sb_access_token", key="del_acc")
    if "sb_refresh_token" in all_cookies: cookie_manager.delete("sb_refresh_token", key="del_ref")
    st.session_state.logout_pending = False

if st.session_state.consent_pending_save:
    expires = dt.datetime.now() + dt.timedelta(days=365)
    cookie_manager.set("nync_consent", st.session_state.consent, expires_at=expires, key="set_consent")
    st.session_state.consent_pending_save = False
    st.toast("✅ Privacy Preferences Saved!")

# 5. SHOW CONSENT DIALOG
cookie_consent.show(all_cookies)

# 6. RESTORE AUTH FROM COOKIES
if not st.session_state.session and not st.session_state.logout_pending:
    if "sb_access_token" in all_cookies and "sb_refresh_token" in all_cookies:
        session = auth.restore_session(all_cookies["sb_access_token"], all_cookies["sb_refresh_token"])
        if session:
            st.session_state.session = session
            st.session_state.user = session.user
        else:
            # Token is invalid or expired
            st.session_state.logout_pending = True
            st.rerun()

# 7. OAUTH CALLBACKS (Google / Microsoft)
if "code" in st.query_params:
    code = st.query_params["code"]
    state = st.query_params.get("state", "")
    
    if state.startswith("microsoft_connect"):
        try:
            parts = state.split(":")
            if len(parts) > 1:
                user_id_from_state = parts[1]
                if auth.handle_microsoft_callback(code, user_id_from_state):
                    st.toast("✅ Outlook Connected!")
                    st.session_state.nav = "Settings"
        except: pass
        st.query_params.clear()
        st.rerun()
        
    else: 
        try:
            res = auth.supabase.auth.exchange_code_for_session({"auth_code": code})
            if res.session:
                st.session_state.session = res.session
                st.session_state.user = res.user
                auth.save_google_token(res.user.id, res.session)
                st.toast("✅ Logged in with Google!")
        except: pass
        st.query_params.clear()
        st.rerun() # Clears URL. Next run hits Auto-Sync block below to save cookies.

# 8. AUTO-SYNC AUTH COOKIES (The Magic Bullet)
# Detects manual logins, Google logins, and Supabase token rotations flawlessly.
if st.session_state.session:
    mem_acc = st.session_state.session.access_token
    cook_acc = all_cookies.get("sb_access_token")
    
    if mem_acc != cook_acc:
        remember = st.session_state.get("remember_me", True)
        expires = dt.datetime.now() + dt.timedelta(days=30) if remember else None
        cookie_manager.set("sb_access_token", mem_acc, expires_at=expires, key="sync_acc")
        cookie_manager.set("sb_refresh_token", st.session_state.session.refresh_token, expires_at=expires, key="sync_ref")

# 9. GLOBAL QUERY PARAMS & STRIPE
if "vote" in st.query_params and not st.session_state.session:
    st.session_state.pending_vote_id = st.query_params["vote"]
    if "idx" in st.query_params: st.session_state.pending_vote_idx = st.query_params["idx"]

if "invite" in st.query_params: 
    st.session_state.pending_invite = st.query_params["invite"]

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

# 10. ROUTER
if not st.session_state.session:
    login.show()
    # If the user logged in manually, rerun to hit the Auto-Sync block
    if st.session_state.session:
        st.rerun() 
else:
    # --- HANDLE PENDING INVITES ---
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
        
    # --- MONETIZATION: AD BANNER FOR FREE USERS ---
    user_consent = st.session_state.get('consent', {})
    profile = auth.get_user_profile(st.session_state.user.id)
    tier = profile.get('subscription_tier', 'free').upper() if profile else "FREE"

    if tier == "FREE" and user_consent and user_consent.get("marketing", False):
        st.info("💡 **Tip:** Upgrade to **Squad Tier** to remove ads and unlock unlimited teams. [View Pricing](#)", icon="🚀")

    # --- TOP NAV BAR ---
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
            st.session_state.logout_pending = True
            st.rerun()
    
    st.markdown("<hr style='margin-top: 10px; border-color: #333;'>", unsafe_allow_html=True)

    nav = st.session_state.nav

    if nav == "Dashboard":
        my_teams = auth.get_user_teams(st.session_state.user.id)
        if not my_teams:
            st.info("👈 Create a Team in Settings.")
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