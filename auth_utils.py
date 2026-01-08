import streamlit as st
import secrets
import string
import stripe
import time  # Standard time module (for sleep)
import datetime as dt  # Renamed to 'dt' to prevent conflicts
import requests
import extra_streamlit_components as stx
from urllib.parse import quote
from supabase import create_client

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_supabase():
    try:
        if "supabase" not in st.secrets: return None
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = get_supabase()

# --- COOKIE MANAGER ---
def get_cookie_manager():
    if 'cookie_manager' in st.session_state:
        return st.session_state.cookie_manager
    cm = stx.CookieManager(key="nync_cookies")
    st.session_state.cookie_manager = cm
    return cm

def save_session_to_cookies(session):
    cookie_manager = get_cookie_manager()
    expires = dt.datetime.now() + dt.timedelta(days=30)
    cookie_manager.set('sb_access_token', session.access_token, key="set_at", expires_at=expires)
    cookie_manager.set('sb_refresh_token', session.refresh_token, key="set_rt", expires_at=expires)

def restore_session_from_cookies():
    cookie_manager = get_cookie_manager()
    time.sleep(0.1) 
    cookies = cookie_manager.get_all()
    access_token = cookies.get('sb_access_token')
    refresh_token = cookies.get('sb_refresh_token')
    
    if access_token and refresh_token:
        try:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res.session:
                st.session_state.session = res.session
                st.session_state.user = res.user
                return True
        except:
            clear_cookies()
            return False
    return False

def clear_cookies():
    cookie_manager = get_cookie_manager() 
    cookie_manager.delete('sb_access_token', key="del_access")
    cookie_manager.delete('sb_refresh_token', key="del_refresh")

# --- AUTH: MICROSOFT ---
def get_microsoft_url():
    try:
        client_id = st.secrets["microsoft"]["client_id"]
        redirect_uri = st.secrets["microsoft"]["redirect_uri"]
        authority = st.secrets["microsoft"]["authority"]
        scope = "Calendars.ReadWrite offline_access User.Read"
        return (f"{authority}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state=microsoft_connect")
    except: return "#"

def handle_microsoft_callback(code, user_id):
    try:
        token_url = f"{st.secrets['microsoft']['authority']}/oauth2/v2.0/token"
        payload = {
            "client_id": st.secrets["microsoft"]["client_id"],
            "scope": "Calendars.ReadWrite offline_access User.Read",
            "code": code,
            "redirect_uri": st.secrets["microsoft"]["redirect_uri"],
            "grant_type": "authorization_code",
            "client_secret": st.secrets["microsoft"]["client_secret"],
        }
        r = requests.post(token_url, data=payload)
        tokens = r.json()
        if "access_token" not in tokens: return False
            
        data = {
            "user_id": user_id, "provider": "outlook",
            "access_token": tokens["access_token"], "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in")
        }
        
        existing = supabase.table("calendar_connections").select("id").eq("user_id", user_id).eq("provider", "outlook").execute()
        if existing.data:
            supabase.table("calendar_connections").update(data).eq("user_id", user_id).eq("provider", "outlook").execute()
        else:
            supabase.table("calendar_connections").insert(data).execute()
        return True
    except: return False

# --- OUTLOOK ---
def refresh_outlook_token(user_id):
    if not supabase: return None
    try:
        record = supabase.table("calendar_connections").select("*").eq("user_id", user_id).eq("provider", "outlook").single().execute()
        if not record.data: return None
        refresh_token = record.data.get("refresh_token")
        
        token_url = f"{st.secrets['microsoft']['authority']}/oauth2/v2.0/token"
        payload = {
            "client_id": st.secrets["microsoft"]["client_id"],
            "client_secret": st.secrets["microsoft"]["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "Calendars.ReadWrite offline_access User.Read"
        }
        r = requests.post(token_url, data=payload)
        new_tokens = r.json()
        if "access_token" not in new_tokens: return None
            
        supabase.table("calendar_connections").update({
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens.get("refresh_token", refresh_token),
            "expires_in": new_tokens.get("expires_in")
        }).eq("user_id", user_id).execute()
        return new_tokens["access_token"]
    except: return None

def fetch_outlook_events(user_id, start_dt, end_dt):
    if not supabase or not user_id: return []
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "outlook").maybe_single().execute()
        if not response or not response.data: return []
        token = response.data.get('access_token')

        headers = {"Authorization": f"Bearer {token}", "Prefer": "outlook.timezone=\"UTC\""}
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_str}&endDateTime={end_str}&$select=subject,start,end,showAs"
        
        r = requests.get(endpoint, headers=headers)
        if r.status_code == 401:
            new_token = refresh_outlook_token(user_id)
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                r = requests.get(endpoint, headers=headers)
            else: return [] 
        if r.status_code != 200: return []
        
        events = r.json().get('value', [])
        blocked_hours = []
        for e in events:
            # Usage: dt.datetime.fromisoformat
            start = dt.datetime.fromisoformat(e['start']['dateTime'].replace('Z', '+00:00'))
            end = dt.datetime.fromisoformat(e['end']['dateTime'].replace('Z', '+00:00'))
            curr = start
            while curr < end:
                blocked_hours.append(curr.replace(minute=0, second=0, microsecond=0))
                curr += dt.timedelta(hours=1)
        return blocked_hours
    except: return []

def book_outlook_meeting(user_id, subject, start_dt_utc, duration_minutes, attendees):
    """Creates an event in the user's Outlook/Teams calendar."""
    if not supabase: 
        print("❌ Booking Error: No Supabase connection")
        return False
        
    try:
        token = refresh_outlook_token(user_id) 
        if not token: 
            print("❌ Booking Error: Could not refresh Outlook token")
            return False

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        end_dt_utc = start_dt_utc + dt.timedelta(minutes=duration_minutes)
        
        attendee_list = []
        for email in attendees:
            attendee_list.append({"emailAddress": {"address": email}, "type": "required"})

        payload = {
            "subject": subject,
            "start": {"dateTime": start_dt_utc.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt_utc.isoformat(), "timeZone": "UTC"},
            "attendees": attendee_list,
            "isOnlineMeeting": True, 
            "onlineMeetingProvider": "teamsForBusiness" 
        }

        r = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=payload)
        
        if r.status_code in [201, 200]:
            return True
        else:
            # --- DIAGNOSTIC PRINT ---
            print(f"❌ OUTLOOK API ERROR ({r.status_code}): {r.text}")
            return False
            
    except Exception as e: 
        print(f"❌ Python Error in Booking: {e}")
        return False

# --- STATS & KARMA ---
def get_martyr_stats(team_id):
    if not supabase: return []
    try:
        resp = supabase.table("pain_ledger").select("user_email, pain_score").eq("team_id", team_id).execute()
        totals = {}
        for row in resp.data:
            e = row['user_email']
            p = row['pain_score']
            totals[e] = totals.get(e, 0) + p
        leaderboard = [{"email": k, "total_pain": v} for k, v in totals.items()]
        leaderboard.sort(key=lambda x: x['total_pain'], reverse=True)
        return leaderboard
    except: return []

def get_team_pain_map(team_id):
    if not supabase: return {}
    try:
        resp = supabase.table("pain_ledger").select("user_email, pain_score").eq("team_id", team_id).execute()
        totals = {}
        for row in resp.data:
            e = row['user_email']
            p = row['pain_score']
            totals[e] = totals.get(e, 0) + p
        return totals
    except: return {}

# --- POLLS ---
def create_poll(team_id, top_3_slots, target_date):
    if not supabase: return False
    try:
        poll = supabase.table('polls').insert({'team_id': team_id, 'status': 'active'}).execute()
        poll_id = poll.data[0]['id']
        
        options = []
        for slot in top_3_slots:
            d = dt.datetime.combine(target_date, dt.time(slot['utc_hour'], 0)).replace(tzinfo=None).isoformat()
            options.append({'poll_id': poll_id, 'slot_time': d, 'pain_score': slot['total_pain']})
        
        supabase.table('poll_options').insert(options).execute()
        
        t_data = supabase.table('teams').select('webhook_url').eq('id', team_id).single().execute()
        webhook = t_data.data.get('webhook_url')
        
        if webhook:
            return send_poll_card(webhook, poll_id, top_3_slots, target_date)
        else: return "No Webhook"
    except Exception as e:
        print(f"Poll Creation Error: {e}")
        return False

def send_poll_card(webhook_url, poll_id, slots, date_obj):
    """
    Sends 'Smart Links' that pre-select the voting option.
    Uses ?vote={poll_id}&idx={index}
    """
    base_url = "https://nyncapp.streamlit.app/" # In prod, this would be https://nync.app
    
    is_discord = "discord" in webhook_url.lower()
    
    # 1. GENERATE LINKS TEXT
    links_text = ""
    for idx, s in enumerate(slots):
        link = f"{base_url}/?vote={poll_id}&idx={idx}"
        time_display = f"{s['utc_hour']}:00 UTC"
        
        if is_discord:
            links_text += f"⏰ **{time_display}** (+{s['total_pain']} pain) • [Vote for this]({link})\n"
        else:
            links_text += f"⏰ **{time_display}** (+{s['total_pain']} pain) • [Vote for this]({link})\n\n"

    # 2. SEND PAYLOAD
    if is_discord:
        payload = {
            "username": "Nync Bot",
            "avatar_url": "https://emojicdn.elk.sh/⚡",
            "embeds": [{
                "title": "⚡ Nync Vote Required",
                "description": f"**Proposed times for {date_obj}:**\n\n{links_text}",
                "color": 5763719
            }]
        }
    else:
        # Teams Adaptive Card
        payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {"type": "TextBlock", "text": "⚡ Nync Vote Required", "weight": "Bolder", "size": "Medium"},
                        {"type": "TextBlock", "text": f"Proposed times for {date_obj}:", "wrap": True},
                        {"type": "TextBlock", "text": links_text, "wrap": True}
                    ]
                }
            }]
        }

    try:
        r = requests.post(webhook_url, json=payload)
        if r.status_code in [200, 202, 204]:
            return True
        else:
            print(f"Webhook Failed: {r.text}")
            return False
    except Exception as e:
        print(f"Webhook Error: {e}")
        return False

# --- HELPERS ---
def login_user(email, password):
    if not supabase: return
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.session = res.session
        st.session_state.user = res.user
        save_session_to_cookies(res.session) 
        st.rerun()
    except Exception as e: st.error(f"Login failed: {e}")

def signup_user(email, password):
    if not supabase: return
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.session:
            st.session_state.session = res.session
            st.session_state.user = res.user
            save_session_to_cookies(res.session) 
            st.rerun()
        else: st.info("Check email to confirm.")
    except Exception as e: st.error(f"Sign up failed: {e}")

def get_user_profile(user_id):
    try: return supabase.table('profiles').select('*').eq('id', user_id).single().execute().data
    except: return None

def update_user_timezone(user_id, tz):
    supabase.table('profiles').update({'default_timezone': tz}).eq('id', user_id).execute()

def get_user_teams(user_id):
    try:
        resp = supabase.table('team_members').select('team_id, teams(name, invite_code)').eq('user_id', user_id).execute()
        return {item['teams']['name']: item['team_id'] for item in resp.data if item['teams']}
    except: return {}

def get_team_roster(team_id):
    roster = []
    try:
        real = supabase.table('team_members').select('user_id, profiles(email, default_timezone)').eq('team_id', team_id).not_.is_('user_id', 'null').execute()
        for r in real.data:
            if r['profiles']:
                roster.append({'email': r['profiles']['email'], 'tz': r['profiles']['default_timezone'] or 'UTC', 'type': 'user', 'name': r['profiles']['email'].split('@')[0]})
        ghost = supabase.table('team_members').select('ghost_name, ghost_email, ghost_timezone').eq('team_id', team_id).is_('user_id', 'null').execute()
        for g in ghost.data:
            roster.append({'email': g.get('ghost_email') or g.get('ghost_name'), 'tz': g['ghost_timezone'], 'type': 'ghost', 'name': g.get('ghost_name', 'Ghost')})
        return roster
    except: return []

def create_team(user_id, name):
    code = "NYNC-" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    try:
        t = supabase.table('teams').insert({'name': name, 'invite_code': code, 'created_by': user_id}).execute()
        if not t.data: return False
        tid = t.data[0]['id']
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id, 'role': 'admin'}).execute()
        st.session_state.active_team = name
        return True
    except: return False

def join_team_by_code(user_id, code):
    try:
        t = supabase.table('teams').select('id, name').eq('invite_code', code).execute()
        if not t.data: return False
        tid, name = t.data[0]['id'], t.data[0]['name']
        if supabase.table('team_members').select('*').eq('team_id', tid).eq('user_id', user_id).execute().data: return True
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id}).execute()
        st.session_state.active_team = name
        return True
    except: return False

def add_ghost_member(team_id, name, email, tz, owner_id):
    try:
        team_data = supabase.table('teams').select('trial_ends_at').eq('id', team_id).single().execute()
        count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).execute().count
        
        trial_end_str = team_data.data.get('trial_ends_at')
        limit = 3
        allow_add = False
        
        if trial_end_str:
            trial_end = dt.datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
            is_trial_active = dt.datetime.now(trial_end.tzinfo) < trial_end
            if is_trial_active: allow_add = True
            elif count < limit: allow_add = True
        else:
            if count < limit: allow_add = True

        if not allow_add:
            st.error(f"🔒 Trial Expired! Limit {limit} members.")
            return False

        if supabase.table('team_members').select('id').eq('team_id', team_id).eq('ghost_email', email).execute().data: return False
        supabase.table('team_members').insert({'team_id': team_id, 'is_ghost': True, 'ghost_name': name, 'ghost_email': email, 'ghost_timezone': tz}).execute()
        return True
    except: return False

def check_team_status(team_id):
    try:
        team = supabase.table('teams').select('trial_ends_at').eq('id', team_id).single().execute()
        if not team.data: return 'active'
        trial_end_str = team.data.get('trial_ends_at')
        if not trial_end_str: return 'active'
        
        trial_end = dt.datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
        is_expired = dt.datetime.now(trial_end.tzinfo) > trial_end
        count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).execute().count
        
        if is_expired and count > 3: return 'locked'
        return 'active'
    except: return 'active'

def get_google_url():
    try:
        base_url = "https://nyncapp.streamlit.app/"
        params = []
        if "invite" in st.query_params: params.append(f"invite={st.query_params['invite']}")
        if "code" in st.query_params and st.query_params.get("state") == "microsoft_connect":
            params.append(f"ms_stash={st.query_params['code']}")
        redirect_url = f"{base_url}/?{'&'.join(params)}" if params else base_url
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google", "options": {"redirect_to": redirect_url}
        })
        return data.url
    except: return None

# --- STRIPE PAYMENTS (UPDATED) ---
def create_stripe_checkout(user_email, price_id, success_url=None, cancel_url=None):
    """
    Creates a Stripe Checkout Session and returns the URL.
    Accepts success/cancel URLs from pricing.py, defaults to live site if missing.
    """
    if "stripe" not in st.secrets: return None
    
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    # Default Fallback (Production)
    base_url = "https://nyncapp.streamlit.app"
    
    if not success_url:
        success_url = f"{base_url}/?stripe_session_id={{CHECKOUT_SESSION_ID}}"
    if not cancel_url:
        cancel_url = f"{base_url}/?nav=Pricing"
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            customer_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return None

def verify_stripe_payment(session_id):
    """
    Checks with Stripe if the session was paid and returns the price_id.
    """
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            line_item = stripe.checkout.Session.list_line_items(session_id, limit=1)
            price_id = line_item.data[0].price.id
            return price_id
    except:
        return None
    return None

def upgrade_user_tier(user_id, tier_name):
    """Updates the user's profile in Supabase."""
    try:
        supabase.table('profiles').update({'subscription_tier': tier_name}).eq('id', user_id).execute()
        return True
    except: return False

def delete_user_data(user_id):
    try:
        supabase.table('calendar_connections').delete().eq('user_id', user_id).execute()
        supabase.table('team_members').delete().eq('user_id', user_id).execute()
        supabase.table('profiles').delete().eq('id', user_id).execute()
        clear_cookies()
        return True
    except: return False

# --- SUBSCRIPTION MANAGEMENT ---

# Define the hierarchy of plans
TIER_LEVELS = {
    "free": 0,
    "squad": 1,
    "guild": 2,
    "empire": 3
}

def get_tier_level(tier_name):
    """Returns the numeric level of a tier (0-3)."""
    return TIER_LEVELS.get(tier_name.lower(), 0)

def create_stripe_portal_session(user_email):
    """
    Generates a link to the Stripe Customer Portal for cancelling/managing billing.
    """
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    base_url = "https://nyncapp.streamlit.app/" # Change to https://nync.app for production

    try:
        # 1. Search for the customer by email
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data:
            return None # User has never paid via Stripe
        
        customer_id = customers.data[0].id

        # 2. Create the portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{base_url}/?nav=Settings"
        )
        return session.url
    except Exception as e:
        print(f"Portal Error: {e}")
        return None
